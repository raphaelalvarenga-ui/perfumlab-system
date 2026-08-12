from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.orm.factura import FacturaORM
from app.models.orm.venta import VentaORM
from app.models.tipos import EstadoFactura


class FacturasRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, factura_id: int) -> FacturaORM | None:
        statement = (
            select(FacturaORM)
            .options(self._detalles_option())
            .where(FacturaORM.id == factura_id)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_numero(self, numero: str) -> FacturaORM | None:
        statement = (
            select(FacturaORM)
            .options(self._detalles_option())
            .where(func.lower(FacturaORM.numero) == numero.strip().lower())
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_venta_id(self, venta_id: int) -> FacturaORM | None:
        statement = (
            select(FacturaORM)
            .options(self._detalles_option())
            .where(FacturaORM.venta_id == venta_id)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        limit: int,
        venta_id: int | None = None,
        estado: EstadoFactura | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        buscar: str | None = None,
    ) -> tuple[list[FacturaORM], int]:
        statement = self._aplicar_filtros(
            select(FacturaORM).options(self._detalles_option()),
            venta_id=venta_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
            buscar=buscar,
        )
        count_statement = self._aplicar_filtros(
            select(func.count(FacturaORM.id)),
            venta_id=venta_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
            buscar=buscar,
        )

        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(FacturaORM.created_at.desc(), FacturaORM.id.desc())
            .offset(offset)
            .limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> FacturaORM:
        factura = FacturaORM(**datos)
        self.db.add(factura)
        self.db.flush()
        return factura

    def mark_anulada(
        self,
        factura: FacturaORM,
        *,
        motivo: str,
        anulada_at: datetime,
        anulada_por_usuario_id: int | None = None,
    ) -> FacturaORM:
        factura.estado = EstadoFactura.ANULADA
        factura.anulada_at = anulada_at
        factura.motivo_anulacion = motivo
        factura.anulada_por_usuario_id = anulada_por_usuario_id
        self.db.flush()
        return factura

    def _aplicar_filtros(
        self,
        statement: Select,
        *,
        venta_id: int | None,
        estado: EstadoFactura | None,
        desde: datetime | None,
        hasta: datetime | None,
        buscar: str | None,
    ) -> Select:
        if venta_id is not None:
            statement = statement.where(FacturaORM.venta_id == venta_id)
        if estado is not None:
            statement = statement.where(FacturaORM.estado == estado)
        if desde is not None:
            statement = statement.where(FacturaORM.created_at >= desde)
        if hasta is not None:
            statement = statement.where(FacturaORM.created_at <= hasta)
        if buscar:
            patron = f"%{buscar.strip()}%"
            statement = statement.where(
                or_(
                    FacturaORM.numero.ilike(patron),
                    FacturaORM.cliente_nombre.ilike(patron),
                )
            )
        return statement

    def _detalles_option(self):
        return selectinload(FacturaORM.venta).selectinload(VentaORM.detalles)
