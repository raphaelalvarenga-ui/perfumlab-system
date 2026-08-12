from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.orm.detalle_venta import DetalleVentaORM
from app.models.orm.venta import VentaORM
from app.models.tipos import EstadoVenta


class VentasRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, venta_id: int) -> VentaORM | None:
        statement = (
            select(VentaORM)
            .options(selectinload(VentaORM.detalles))
            .where(VentaORM.id == venta_id)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_id_for_update(self, venta_id: int) -> VentaORM | None:
        statement = (
            select(VentaORM)
            .options(selectinload(VentaORM.detalles))
            .where(VentaORM.id == venta_id)
            .with_for_update(of=VentaORM)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        limit: int,
        cliente_id: int | None = None,
        estado: EstadoVenta | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> tuple[list[VentaORM], int]:
        statement = self._aplicar_filtros(
            select(VentaORM).options(selectinload(VentaORM.detalles)),
            cliente_id=cliente_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
        )
        count_statement = self._aplicar_filtros(
            select(func.count(VentaORM.id)),
            cliente_id=cliente_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
        )

        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(VentaORM.created_at.desc(), VentaORM.id.desc())
            .offset(offset)
            .limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> VentaORM:
        venta = VentaORM(**datos)
        self.db.add(venta)
        self.db.flush()
        return venta

    def create_detalle(self, datos: dict) -> DetalleVentaORM:
        detalle = DetalleVentaORM(**datos)
        self.db.add(detalle)
        self.db.flush()
        return detalle

    def _aplicar_filtros(
        self,
        statement: Select,
        *,
        cliente_id: int | None,
        estado: EstadoVenta | None,
        desde: datetime | None,
        hasta: datetime | None,
    ) -> Select:
        if cliente_id is not None:
            statement = statement.where(VentaORM.cliente_id == cliente_id)
        if estado is not None:
            statement = statement.where(VentaORM.estado == estado)
        if desde is not None:
            statement = statement.where(VentaORM.created_at >= desde)
        if hasta is not None:
            statement = statement.where(VentaORM.created_at <= hasta)
        return statement
