from app.database.json_storage import (
    DATABASE_PATH,
    buscar_por_id,
    cargar_tabla,
    cargar_todo,
    fecha_actual,
    guardar_todo,
    inicializar_datos_json,
    siguiente_id,
)


class InventarioController:
    def __init__(self, ruta_db=DATABASE_PATH):
        self.ruta_datos = ruta_db
        inicializar_datos_json(self.ruta_datos)

    def registrar_entrada(self, producto_id, cantidad, motivo):
        self._validar_cantidad(cantidad)
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
        self._validar_cantidad(cantidad)
        datos = cargar_todo(self.ruta_datos)
        producto = self._obtener_producto(datos["productos"], producto_id)
        stock_anterior = int(producto["stock_actual"])

        if cantidad > stock_anterior:
            raise ValueError("No hay stock suficiente para registrar la salida.")

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
        if nuevo_stock < 0:
            raise ValueError("El nuevo stock no puede ser negativo.")

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

    def _validar_cantidad(self, cantidad):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

    def _obtener_producto(self, productos, producto_id):
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
