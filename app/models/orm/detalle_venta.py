from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DetalleVentaORM(Base):
    __tablename__ = "detalle_ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id"),
        nullable=False,
        index=True,
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id"),
        nullable=False,
        index=True,
    )
    producto_sku: Mapped[str] = mapped_column(String(30), nullable=False)
    producto_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    venta: Mapped["VentaORM"] = relationship(back_populates="detalles")
    producto: Mapped["ProductoORM"] = relationship(back_populates="detalles_venta")

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_ventas_cantidad_positiva"),
        CheckConstraint(
            "precio_unitario >= 0",
            name="ck_detalle_ventas_precio_unitario_no_negativo",
        ),
        CheckConstraint("subtotal >= 0", name="ck_detalle_ventas_subtotal_no_negativo"),
        CheckConstraint(
            "length(trim(producto_sku)) > 0",
            name="ck_detalle_ventas_producto_sku_no_vacio",
        ),
        CheckConstraint(
            "length(trim(producto_nombre)) > 0",
            name="ck_detalle_ventas_producto_nombre_no_vacio",
        ),
        Index("ix_detalle_ventas_venta_producto", "venta_id", "producto_id"),
    )
