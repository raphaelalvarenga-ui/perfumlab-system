from datetime import datetime

from sqlalchemy.orm import Session

from app.models.orm.producto import ProductoORM
from app.models.tipos import TipoMovimientoInventario
from app.repositories.inventario_repository import InventarioRepository
from app.schemas.inventario import MovimientoInventarioListResponse
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class InventarioService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InventarioRepository(db)

    def registrar_entrada(self, datos: dict):
        return self._registrar_cambio_stock(
            producto_id=datos["producto_id"],
            tipo=TipoMovimientoInventario.ENTRADA,
            cantidad=datos["cantidad"],
            stock_final=None,
            motivo=datos["motivo"],
        )

    def registrar_salida(self, datos: dict):
        return self._registrar_cambio_stock(
            producto_id=datos["producto_id"],
            tipo=TipoMovimientoInventario.SALIDA,
            cantidad=datos["cantidad"],
            stock_final=None,
            motivo=datos["motivo"],
        )

    def registrar_ajuste(self, datos: dict):
        return self._registrar_cambio_stock(
            producto_id=datos["producto_id"],
            tipo=TipoMovimientoInventario.AJUSTE,
            cantidad=None,
            stock_final=datos["stock_nuevo"],
            motivo=datos["motivo"],
        )

    def listar_movimientos(
        self,
        *,
        page: int,
        limit: int,
        producto_id: int | None = None,
        tipo: TipoMovimientoInventario | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> MovimientoInventarioListResponse:
        items, total = self.repository.list_movimientos(
            page=page,
            limit=limit,
            producto_id=producto_id,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
        )
        return MovimientoInventarioListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def obtener_movimiento(self, movimiento_id: int):
        movimiento = self.repository.get_movimiento_by_id(movimiento_id)
        if movimiento is None:
            raise NotFoundError("Movimiento de inventario no encontrado.")
        return movimiento

    def _registrar_cambio_stock(
        self,
        *,
        producto_id: int,
        tipo: TipoMovimientoInventario,
        cantidad: int | None,
        stock_final: int | None,
        motivo: str,
    ):
        try:
            producto = self.repository.get_producto_for_update(producto_id)
            self._validar_producto_operable(producto)

            stock_anterior = int(producto.stock_actual)
            cantidad_movimiento, stock_nuevo = self._calcular_movimiento(
                tipo=tipo,
                cantidad=cantidad,
                stock_anterior=stock_anterior,
                stock_final=stock_final,
            )

            self.repository.update_stock(producto, stock_nuevo)
            movimiento = self.repository.create_movimiento(
                producto_id=producto.id,
                tipo=tipo,
                cantidad=cantidad_movimiento,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                motivo=motivo.strip(),
                usuario_id=None,
            )
            self.db.commit()
            self.db.refresh(movimiento)
            return movimiento
        except Exception:
            self.db.rollback()
            raise

    def _validar_producto_operable(self, producto: ProductoORM | None) -> None:
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        if not producto.activo:
            raise ConflictError("El producto esta inactivo.")

    def _calcular_movimiento(
        self,
        *,
        tipo: TipoMovimientoInventario,
        cantidad: int | None,
        stock_anterior: int,
        stock_final: int | None,
    ) -> tuple[int, int]:
        if tipo == TipoMovimientoInventario.ENTRADA:
            cantidad_movimiento = self._validar_cantidad(cantidad)
            return cantidad_movimiento, stock_anterior + cantidad_movimiento

        if tipo == TipoMovimientoInventario.SALIDA:
            cantidad_movimiento = self._validar_cantidad(cantidad)
            if cantidad_movimiento > stock_anterior:
                raise BadRequestError("No hay suficiente stock disponible.")
            return cantidad_movimiento, stock_anterior - cantidad_movimiento

        stock_nuevo = self._validar_stock_final(stock_final)
        if stock_nuevo == stock_anterior:
            raise BadRequestError("El ajuste no modifica el stock actual.")
        return abs(stock_nuevo - stock_anterior), stock_nuevo

    def _validar_cantidad(self, cantidad: int | None) -> int:
        if cantidad is None or cantidad <= 0:
            raise BadRequestError("La cantidad debe ser mayor que cero.")
        return cantidad

    def _validar_stock_final(self, stock_final: int | None) -> int:
        if stock_final is None or stock_final < 0:
            raise BadRequestError("El stock nuevo no puede ser negativo.")
        return stock_final
