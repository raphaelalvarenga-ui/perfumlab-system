from sqlalchemy.orm import Session

from app.models.orm.movimiento_inventario import MovimientoInventarioORM
from app.models.orm.producto import ProductoORM
from app.models.tipos import TipoMovimientoInventario
from app.repositories.inventario_repository import InventarioRepository
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InventarioRepository(db)

    def bloquear_producto(self, producto_id: int) -> ProductoORM | None:
        return self.repository.get_producto_for_update(producto_id)

    def bloquear_productos_ordenados(
        self,
        producto_ids: list[int],
    ) -> list[ProductoORM]:
        ids_ordenados = sorted(set(producto_ids))
        return self.repository.get_productos_for_update(ids_ordenados)

    def registrar_entrada(
        self,
        *,
        producto_id: int,
        cantidad: int,
        motivo: str,
        usuario_id: int | None = None,
    ) -> MovimientoInventarioORM:
        producto = self.bloquear_producto(producto_id)
        return self.registrar_entrada_en_producto(
            producto,
            cantidad=cantidad,
            motivo=motivo,
            usuario_id=usuario_id,
        )

    def registrar_salida(
        self,
        *,
        producto_id: int,
        cantidad: int,
        motivo: str,
        usuario_id: int | None = None,
    ) -> MovimientoInventarioORM:
        producto = self.bloquear_producto(producto_id)
        return self.registrar_salida_en_producto(
            producto,
            cantidad=cantidad,
            motivo=motivo,
            usuario_id=usuario_id,
        )

    def registrar_ajuste(
        self,
        *,
        producto_id: int,
        stock_nuevo: int,
        motivo: str,
        usuario_id: int | None = None,
    ) -> MovimientoInventarioORM:
        producto = self.bloquear_producto(producto_id)
        return self.registrar_ajuste_en_producto(
            producto,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            usuario_id=usuario_id,
        )

    def registrar_entrada_en_producto(
        self,
        producto: ProductoORM | None,
        *,
        cantidad: int,
        motivo: str,
        usuario_id: int | None = None,
        requiere_activo: bool = True,
    ) -> MovimientoInventarioORM:
        self._validar_producto_operable(producto, requiere_activo=requiere_activo)
        cantidad_movimiento = self._validar_cantidad(cantidad)
        stock_anterior = int(producto.stock_actual)
        stock_nuevo = stock_anterior + cantidad_movimiento
        return self._crear_movimiento_stock(
            producto=producto,
            tipo=TipoMovimientoInventario.ENTRADA,
            cantidad=cantidad_movimiento,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            usuario_id=usuario_id,
        )

    def registrar_salida_en_producto(
        self,
        producto: ProductoORM | None,
        *,
        cantidad: int,
        motivo: str,
        usuario_id: int | None = None,
        mensaje_stock_insuficiente: str | None = None,
    ) -> MovimientoInventarioORM:
        self._validar_producto_operable(producto)
        cantidad_movimiento = self._validar_cantidad(cantidad)
        stock_anterior = int(producto.stock_actual)

        if cantidad_movimiento > stock_anterior:
            raise BadRequestError(
                mensaje_stock_insuficiente or "No hay suficiente stock disponible."
            )

        stock_nuevo = stock_anterior - cantidad_movimiento
        return self._crear_movimiento_stock(
            producto=producto,
            tipo=TipoMovimientoInventario.SALIDA,
            cantidad=cantidad_movimiento,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            usuario_id=usuario_id,
        )

    def registrar_ajuste_en_producto(
        self,
        producto: ProductoORM | None,
        *,
        stock_nuevo: int,
        motivo: str,
        usuario_id: int | None = None,
    ) -> MovimientoInventarioORM:
        self._validar_producto_operable(producto)
        stock_final = self._validar_stock_final(stock_nuevo)
        stock_anterior = int(producto.stock_actual)

        if stock_final == stock_anterior:
            raise BadRequestError("El ajuste no modifica el stock actual.")

        return self._crear_movimiento_stock(
            producto=producto,
            tipo=TipoMovimientoInventario.AJUSTE,
            cantidad=abs(stock_final - stock_anterior),
            stock_anterior=stock_anterior,
            stock_nuevo=stock_final,
            motivo=motivo,
            usuario_id=usuario_id,
        )

    def validar_producto_operable(
        self,
        producto: ProductoORM | None,
        *,
        requiere_activo: bool = True,
    ) -> None:
        self._validar_producto_operable(producto, requiere_activo=requiere_activo)

    def _crear_movimiento_stock(
        self,
        *,
        producto: ProductoORM,
        tipo: TipoMovimientoInventario,
        cantidad: int,
        stock_anterior: int,
        stock_nuevo: int,
        motivo: str,
        usuario_id: int | None,
    ) -> MovimientoInventarioORM:
        motivo_limpio = self._validar_motivo(motivo)
        self.repository.update_stock(producto, stock_nuevo)
        return self.repository.create_movimiento(
            producto_id=producto.id,
            tipo=tipo,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo_limpio,
            usuario_id=usuario_id,
        )

    def _validar_producto_operable(
        self,
        producto: ProductoORM | None,
        *,
        requiere_activo: bool = True,
    ) -> None:
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        if requiere_activo and not producto.activo:
            raise ConflictError("El producto esta inactivo.")

    def _validar_cantidad(self, cantidad: int | None) -> int:
        if cantidad is None or cantidad <= 0:
            raise BadRequestError("La cantidad debe ser mayor que cero.")
        return cantidad

    def _validar_stock_final(self, stock_final: int | None) -> int:
        if stock_final is None or stock_final < 0:
            raise BadRequestError("El stock nuevo no puede ser negativo.")
        return stock_final

    def _validar_motivo(self, motivo: str) -> str:
        motivo_limpio = motivo.strip() if motivo else ""
        if not motivo_limpio:
            raise BadRequestError("El motivo es obligatorio.")
        return motivo_limpio
