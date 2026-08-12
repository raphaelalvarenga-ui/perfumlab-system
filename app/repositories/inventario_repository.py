from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.orm.movimiento_inventario import MovimientoInventarioORM
from app.models.orm.producto import ProductoORM
from app.models.tipos import TipoMovimientoInventario


class InventarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_producto_for_update(self, producto_id: int) -> ProductoORM | None:
        statement = (
            select(ProductoORM)
            .where(ProductoORM.id == producto_id)
            .with_for_update()
        )
        return self.db.execute(statement).scalar_one_or_none()

    def update_stock(self, producto: ProductoORM, stock_nuevo: int) -> ProductoORM:
        producto.stock_actual = stock_nuevo
        self.db.flush()
        return producto

    def create_movimiento(
        self,
        *,
        producto_id: int,
        tipo: TipoMovimientoInventario,
        cantidad: int,
        stock_anterior: int,
        stock_nuevo: int,
        motivo: str,
        usuario_id: int | None = None,
    ) -> MovimientoInventarioORM:
        movimiento = MovimientoInventarioORM(
            producto_id=producto_id,
            tipo=tipo,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            usuario_id=usuario_id,
        )
        self.db.add(movimiento)
        self.db.flush()
        self.db.refresh(movimiento)
        return movimiento

    def get_movimiento_by_id(
        self,
        movimiento_id: int,
    ) -> MovimientoInventarioORM | None:
        return self.db.get(MovimientoInventarioORM, movimiento_id)

    def list_movimientos(
        self,
        *,
        page: int,
        limit: int,
        producto_id: int | None = None,
        tipo: TipoMovimientoInventario | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> tuple[list[MovimientoInventarioORM], int]:
        statement = self._aplicar_filtros(
            select(MovimientoInventarioORM),
            producto_id=producto_id,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
        )
        count_statement = self._aplicar_filtros(
            select(func.count(MovimientoInventarioORM.id)),
            producto_id=producto_id,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
        )

        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(
                MovimientoInventarioORM.created_at.desc(),
                MovimientoInventarioORM.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def _aplicar_filtros(
        self,
        statement: Select,
        *,
        producto_id: int | None,
        tipo: TipoMovimientoInventario | None,
        desde: datetime | None,
        hasta: datetime | None,
    ) -> Select:
        if producto_id is not None:
            statement = statement.where(
                MovimientoInventarioORM.producto_id == producto_id
            )
        if tipo is not None:
            statement = statement.where(MovimientoInventarioORM.tipo == tipo)
        if desde is not None:
            statement = statement.where(MovimientoInventarioORM.created_at >= desde)
        if hasta is not None:
            statement = statement.where(MovimientoInventarioORM.created_at <= hasta)
        return statement
