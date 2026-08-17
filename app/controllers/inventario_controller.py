from app.api_client import get_api_client
from app.database.json_storage import (
    buscar_por_id,
    cargar_tabla,
    cargar_todo,
    fecha_actual,
    guardar_todo,
    inicializar_datos_json,
    siguiente_id,
)
from app.validaciones import (
    validar_entero_no_negativo,
    validar_entero_positivo,
    validar_id_positivo,
    validar_texto_opcional,
)


class InventarioController:
    def __init__(self, ruta_db=None, api_client=None):
        self.ruta_datos = ruta_db
        self.api = api_client or (get_api_client() if ruta_db is None else None)
        if self._usar_json:
            inicializar_datos_json(self.ruta_datos)

    @property
    def _usar_json(self):
        return self.ruta_datos is not None

    def registrar_entrada(self, producto_id, cantidad, motivo):
        producto_id = validar_id_positivo(producto_id, "producto")
        cantidad = validar_entero_positivo(cantidad, "La cantidad")
        motivo = validar_texto_opcional(motivo, "motivo", maximo=160)
        if not self._usar_json:
            return self.api.inventario.registrar_entrada(producto_id, cantidad, motivo)["id"]

        datos = cargar_todo(self.ruta_datos)
        producto = self._obtener_producto(datos["productos"], producto_id)
        stock_anterior = int(producto["stock_actual"])
        stock_nuevo = stock_anterior + cantidad
        movimiento_id = self._registrar_cambio_stock(
            datos,
            producto,
            "ENTRADA",
            cantidad,
            stock_anterior,
            stock_nuevo,
            motivo,
        )
        guardar_todo(
            {
                "productos": datos["productos"],
                "movimientos_inventario": datos["movimientos_inventario"],
            },
            self.ruta_datos,
        )
        return movimiento_id

    def registrar_salida(self, producto_id, cantidad, motivo):
        producto_id = validar_id_positivo(producto_id, "producto")
        cantidad = validar_entero_positivo(cantidad, "La cantidad")
        motivo = validar_texto_opcional(motivo, "motivo", maximo=160)
        if not self._usar_json:
            return self.api.inventario.registrar_salida(producto_id, cantidad, motivo)["id"]

        datos = cargar_todo(self.ruta_datos)
        producto = self._obtener_producto(datos["productos"], producto_id)
        stock_anterior = int(producto["stock_actual"])
        if cantidad > stock_anterior:
            raise ValueError("No hay suficiente stock disponible.")

        stock_nuevo = stock_anterior - cantidad
        movimiento_id = self._registrar_cambio_stock(
            datos,
            producto,
            "SALIDA",
            cantidad,
            stock_anterior,
            stock_nuevo,
            motivo,
        )
        guardar_todo(
            {
                "productos": datos["productos"],
                "movimientos_inventario": datos["movimientos_inventario"],
            },
            self.ruta_datos,
        )
        return movimiento_id

    def registrar_ajuste(self, producto_id, nuevo_stock, motivo):
        producto_id = validar_id_positivo(producto_id, "producto")
        nuevo_stock = validar_entero_no_negativo(nuevo_stock, "El nuevo stock")
        motivo = validar_texto_opcional(motivo, "motivo", maximo=160)
        if not self._usar_json:
            return self.api.inventario.registrar_ajuste(producto_id, nuevo_stock, motivo)["id"]

        datos = cargar_todo(self.ruta_datos)
        producto = self._obtener_producto(datos["productos"], producto_id)
        stock_anterior = int(producto["stock_actual"])
        cantidad = abs(nuevo_stock - stock_anterior)
        if cantidad <= 0:
            raise ValueError("El ajuste debe cambiar el stock actual.")

        movimiento_id = self._registrar_cambio_stock(
            datos,
            producto,
            "AJUSTE",
            cantidad,
            stock_anterior,
            nuevo_stock,
            motivo,
        )
        guardar_todo(
            {
                "productos": datos["productos"],
                "movimientos_inventario": datos["movimientos_inventario"],
            },
            self.ruta_datos,
        )
        return movimiento_id

    def obtener_movimientos(self, producto_id=None):
        if not self._usar_json:
            movimientos = self.api.inventario.listar_movimientos_todos(producto_id=producto_id)
            return [self._movimiento_api_a_legacy(movimiento) for movimiento in movimientos]

        movimientos = cargar_tabla("movimientos_inventario", self.ruta_datos)
        if producto_id is not None:
            producto_id = int(producto_id)
            movimientos = [
                movimiento
                for movimiento in movimientos
                if int(movimiento["producto_id"]) == producto_id
            ]

        movimientos.sort(
            key=lambda movimiento: (
                str(movimiento.get("fecha", "")),
                int(movimiento.get("id", 0)),
            ),
            reverse=True,
        )
        return movimientos

    def _movimiento_api_a_legacy(self, movimiento):
        return {
            "id": movimiento["id"],
            "producto_id": movimiento["producto_id"],
            "tipo_movimiento": movimiento["tipo"],
            "cantidad": movimiento["cantidad"],
            "stock_anterior": movimiento["stock_anterior"],
            "stock_nuevo": movimiento["stock_nuevo"],
            "motivo": movimiento["motivo"],
            "fecha": movimiento["created_at"],
        }

    def _obtener_producto(self, productos, producto_id):
        producto_id = validar_id_positivo(producto_id, "producto")
        producto = buscar_por_id(productos, producto_id)
        if producto is None:
            raise ValueError("El producto indicado no existe.")
        return producto

    def _registrar_cambio_stock(
        self,
        datos,
        producto,
        tipo_movimiento,
        cantidad,
        stock_anterior,
        stock_nuevo,
        motivo,
    ):
        producto["stock_actual"] = int(stock_nuevo)
        producto["fecha_actualizacion"] = fecha_actual()
        movimiento_id = siguiente_id(
            "movimientos_inventario",
            datos["movimientos_inventario"],
        )
        datos["movimientos_inventario"].append(
            {
                "id": movimiento_id,
                "producto_id": int(producto["id"]),
                "tipo_movimiento": tipo_movimiento,
                "cantidad": int(cantidad),
                "stock_anterior": int(stock_anterior),
                "stock_nuevo": int(stock_nuevo),
                "motivo": motivo.strip() if motivo else "",
                "fecha": fecha_actual(),
            }
        )
        return movimiento_id
