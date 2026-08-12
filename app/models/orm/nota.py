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
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.tipos import TipoNota


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


tipo_nota_enum = Enum(
    TipoNota,
    name="tipo_nota",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=True,
    validate_strings=True,
    create_constraint=True,
)


class ProductoNotaORM(Base):
    __tablename__ = "producto_notas"

    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    nota_id: Mapped[int] = mapped_column(
        ForeignKey("notas.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    tipo: Mapped[TipoNota] = mapped_column(tipo_nota_enum, primary_key=True)
    posicion: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    producto: Mapped["ProductoORM"] = relationship(back_populates="notas_rel")
    nota: Mapped["NotaORM"] = relationship(back_populates="productos_rel")

    __table_args__ = (
        CheckConstraint(
            "posicion IS NULL OR posicion >= 0",
            name="ck_producto_notas_posicion_no_negativa",
        ),
        Index("ix_producto_notas_nota_id", "nota_id"),
        Index("ix_producto_notas_tipo", "tipo"),
    )


class NotaORM(Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        index=True,
    )
    imagen_url: Mapped[str | None] = mapped_column(Text)
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

    productos_rel: Mapped[list[ProductoNotaORM]] = relationship(
        back_populates="nota",
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(nombre)) > 0",
            name="ck_notas_nombre_no_vacio",
        ),
        CheckConstraint(
            "length(trim(slug)) > 0",
            name="ck_notas_slug_no_vacio",
        ),
        Index("ix_notas_slug_lower", func.lower(slug), unique=True),
    )
