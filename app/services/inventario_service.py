from datetime import datetime

from sqlalchemy.orm import Session

from app.models.tipos import TipoMovimientoInventario
from app.repositories.inventario_repository import InventarioRepository
from app.schemas.inventario import MovimientoInventarioListResponse
from app.services.exceptions import NotFoundError
from app.services.stock_service import StockService


class InventarioService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InventarioRepository(db)
        self.stock_service = StockService(db)

    def registrar_entrada(self, datos: dict, *, usuario_id: int):
        return self._ejecutar_con_commit(
            self.stock_service.registrar_entrada,
            producto_id=datos["producto_id"],
            cantidad=datos["cantidad"],
            motivo=datos["motivo"],
            usuario_id=usuario_id,
        )

    def registrar_salida(self, datos: dict, *, usuario_id: int):
        return self._ejecutar_con_commit(
            self.stock_service.registrar_salida,
            producto_id=datos["producto_id"],
            cantidad=datos["cantidad"],
            motivo=datos["motivo"],
            usuario_id=usuario_id,
        )

    def registrar_ajuste(self, datos: dict, *, usuario_id: int):
        return self._ejecutar_con_commit(
            self.stock_service.registrar_ajuste,
            producto_id=datos["producto_id"],
            stock_nuevo=datos["stock_nuevo"],
            motivo=datos["motivo"],
            usuario_id=usuario_id,
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

    def _ejecutar_con_commit(self, operacion, **kwargs):
        try:
            movimiento = operacion(**kwargs)
            self.db.commit()
            self.db.refresh(movimiento)
            return movimiento
        except Exception:
            self.db.rollback()
            raise
