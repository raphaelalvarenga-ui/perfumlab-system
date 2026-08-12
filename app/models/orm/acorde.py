from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.tipos import IntensidadAcorde


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


intensidad_acorde_enum = Enum(
    IntensidadAcorde,
    name="intensidad_acorde",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=True,
    validate_strings=True,
    create_constraint=True,
)


class ProductoAcordeORM(Base):
    __tablename__ = "producto_acordes"

    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    acorde_id: Mapped[int] = mapped_column(
        ForeignKey("acordes.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    intensidad: Mapped[IntensidadAcorde | None] = mapped_column(
        intensidad_acorde_enum,
        nullable=True,
    )
    posicion: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    producto: Mapped["ProductoORM"] = relationship(back_populates="acordes_rel")
    acorde: Mapped["AcordeORM"] = relationship(back_populates="productos_rel")

    __table_args__ = (
        CheckConstraint(
            "posicion IS NULL OR posicion >= 0",
            name="ck_producto_acordes_posicion_no_negativa",
        ),
        Index("ix_producto_acordes_acorde_id", "acorde_id"),
    )


class AcordeORM(Base):
    __tablename__ = "acordes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=utc_now,
    )

    productos_rel: Mapped[list[ProductoAcordeORM]] = relationship(
        back_populates="acorde",
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(nombre)) > 0",
            name="ck_acordes_nombre_no_vacio",
        ),
        CheckConstraint(
            "length(trim(slug)) > 0",
            name="ck_acordes_slug_no_vacio",
        ),
        Index("ix_acordes_slug_lower", func.lower(slug), unique=True),
    )
