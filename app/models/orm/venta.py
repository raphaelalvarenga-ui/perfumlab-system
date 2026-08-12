from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.tipos import EstadoVenta


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


estado_venta_enum = Enum(
    EstadoVenta,
    name="estado_venta",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=True,
    validate_strings=True,
    create_constraint=True,
)


class VentaORM(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id"),
        index=True,
    )
    cliente_nombre: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Cliente mostrador",
    )
    usuario_id: Mapped[int | None] = mapped_column(Integer, index=True)
    estado: Mapped[EstadoVenta] = mapped_column(
        estado_venta_enum,
        nullable=False,
        default=EstadoVenta.COMPLETADA,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    anulada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_anulacion: Mapped[str | None] = mapped_column(Text)

    cliente: Mapped["ClienteORM | None"] = relationship(back_populates="ventas")
    detalles: Mapped[list["DetalleVentaORM"]] = relationship(
        back_populates="venta",
        order_by="DetalleVentaORM.id",
    )

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_ventas_subtotal_no_negativo"),
        CheckConstraint("total >= 0", name="ck_ventas_total_no_negativo"),
        CheckConstraint(
            "length(trim(cliente_nombre)) > 0",
            name="ck_ventas_cliente_nombre_no_vacio",
        ),
        Index("ix_ventas_created_at_id", "created_at", "id"),
    )
