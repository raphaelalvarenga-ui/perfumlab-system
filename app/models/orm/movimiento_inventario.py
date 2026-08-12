from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.tipos import TipoMovimientoInventario


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


tipo_movimiento_enum = Enum(
    TipoMovimientoInventario,
    name="tipo_movimiento_inventario",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=True,
    validate_strings=True,
    create_constraint=True,
)


class MovimientoInventarioORM(Base):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoMovimientoInventario] = mapped_column(
        tipo_movimiento_enum,
        nullable=False,
        index=True,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_anterior: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_nuevo: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    producto: Mapped["ProductoORM"] = relationship(
        back_populates="movimientos_inventario"
    )
    usuario: Mapped["UsuarioORM | None"] = relationship(
        back_populates="movimientos_inventario",
        foreign_keys=[usuario_id],
    )

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_mov_inv_cantidad_positiva"),
        CheckConstraint(
            "stock_anterior >= 0",
            name="ck_mov_inv_stock_anterior_no_negativo",
        ),
        CheckConstraint(
            "stock_nuevo >= 0",
            name="ck_mov_inv_stock_nuevo_no_negativo",
        ),
        CheckConstraint("length(trim(motivo)) > 0", name="ck_mov_inv_motivo_no_vacio"),
        Index("ix_movimientos_inventario_created_at_id", "created_at", "id"),
    )
