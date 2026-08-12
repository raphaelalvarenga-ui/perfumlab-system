from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.tipos import EstadoFactura


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


estado_factura_enum = Enum(
    EstadoFactura,
    name="estado_factura",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=True,
    validate_strings=True,
    create_constraint=True,
)


class FacturaORM(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), nullable=False)
    cliente_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[EstadoFactura] = mapped_column(
        estado_factura_enum,
        nullable=False,
        default=EstadoFactura.EMITIDA,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    anulada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_anulacion: Mapped[str | None] = mapped_column(Text)

    venta: Mapped["VentaORM"] = relationship(back_populates="factura")

    @property
    def detalles(self):
        return self.venta.detalles if self.venta else []

    __table_args__ = (
        CheckConstraint(
            "length(trim(numero)) > 0",
            name="ck_facturas_numero_no_vacio",
        ),
        CheckConstraint(
            "length(trim(cliente_nombre)) > 0",
            name="ck_facturas_cliente_nombre_no_vacio",
        ),
        CheckConstraint("subtotal >= 0", name="ck_facturas_subtotal_no_negativo"),
        CheckConstraint("total >= 0", name="ck_facturas_total_no_negativo"),
        Index("ix_facturas_numero", "numero", unique=True),
        Index("ix_facturas_venta_id", "venta_id", unique=True),
        Index("ix_facturas_estado", "estado"),
        Index("ix_facturas_created_at_id", "created_at", "id"),
    )
