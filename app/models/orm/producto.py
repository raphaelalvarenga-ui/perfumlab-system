from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductoORM(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    marca: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    costo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    precio: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ml: Mapped[int | None] = mapped_column(Integer)
    imagen: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    genero: Mapped[str | None] = mapped_column(String(40))
    anio_lanzamiento: Mapped[int | None] = mapped_column(Integer)
    concentracion: Mapped[str | None] = mapped_column(String(60))
    duracion: Mapped[str | None] = mapped_column(String(60))
    estela: Mapped[str | None] = mapped_column(String(60))
    external_provider: Mapped[str | None] = mapped_column(String(80))
    external_id: Mapped[str | None] = mapped_column(String(120))
    external_last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=utc_now,
    )

    categoria: Mapped["CategoriaORM"] = relationship(back_populates="productos")
    movimientos_inventario: Mapped[list["MovimientoInventarioORM"]] = relationship(
        back_populates="producto"
    )
    detalles_venta: Mapped[list["DetalleVentaORM"]] = relationship(
        back_populates="producto"
    )
    acordes_rel: Mapped[list["ProductoAcordeORM"]] = relationship(
        back_populates="producto",
        order_by="ProductoAcordeORM.posicion.asc(), ProductoAcordeORM.acorde_id.asc()",
    )
    notas_rel: Mapped[list["ProductoNotaORM"]] = relationship(
        back_populates="producto",
        order_by=(
            "ProductoNotaORM.tipo.asc(), "
            "ProductoNotaORM.posicion.asc(), "
            "ProductoNotaORM.nota_id.asc()"
        ),
    )

    __table_args__ = (
        CheckConstraint("costo >= 0", name="ck_productos_costo_no_negativo"),
        CheckConstraint("precio >= 0", name="ck_productos_precio_no_negativo"),
        CheckConstraint(
            "stock_actual >= 0",
            name="ck_productos_stock_actual_no_negativo",
        ),
        CheckConstraint(
            "stock_minimo >= 0",
            name="ck_productos_stock_minimo_no_negativo",
        ),
        CheckConstraint("ml IS NULL OR ml > 0", name="ck_productos_ml_positivo"),
        Index("ix_productos_sku_lower", func.lower(sku), unique=True),
    )
