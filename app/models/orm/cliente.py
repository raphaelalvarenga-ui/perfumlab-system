from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClienteORM(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    correo: Mapped[str | None] = mapped_column(String(120), index=True)
    telefono: Mapped[str | None] = mapped_column(String(25), index=True)
    direccion: Mapped[str | None] = mapped_column(Text)
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

    ventas: Mapped[list["VentaORM"]] = relationship(back_populates="cliente")

    __table_args__ = (
        Index(
            "ix_clientes_correo_lower",
            func.lower(correo),
            unique=True,
            postgresql_where=correo.is_not(None),
            sqlite_where=correo.is_not(None),
        ),
    )
