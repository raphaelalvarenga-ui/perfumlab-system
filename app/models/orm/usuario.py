from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.tipos import RolUsuario


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


rol_usuario_enum = Enum(
    RolUsuario,
    name="rol_usuario",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=True,
    validate_strings=True,
    create_constraint=True,
)


class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(120), index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        rol_usuario_enum,
        nullable=False,
        index=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=utc_now,
    )

    ventas_creadas: Mapped[list["VentaORM"]] = relationship(
        back_populates="usuario",
        foreign_keys="VentaORM.usuario_id",
    )
    ventas_anuladas: Mapped[list["VentaORM"]] = relationship(
        back_populates="anulada_por_usuario",
        foreign_keys="VentaORM.anulada_por_usuario_id",
    )
    movimientos_inventario: Mapped[list["MovimientoInventarioORM"]] = relationship(
        back_populates="usuario",
        foreign_keys="MovimientoInventarioORM.usuario_id",
    )
    facturas_emitidas: Mapped[list["FacturaORM"]] = relationship(
        back_populates="usuario",
        foreign_keys="FacturaORM.usuario_id",
    )
    facturas_anuladas: Mapped[list["FacturaORM"]] = relationship(
        back_populates="anulada_por_usuario",
        foreign_keys="FacturaORM.anulada_por_usuario_id",
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(nombre)) > 0",
            name="ck_usuarios_nombre_no_vacio",
        ),
        CheckConstraint(
            "length(trim(username)) > 0",
            name="ck_usuarios_username_no_vacio",
        ),
        CheckConstraint(
            "length(trim(password_hash)) > 0",
            name="ck_usuarios_password_hash_no_vacio",
        ),
        CheckConstraint(
            "token_version >= 0",
            name="ck_usuarios_token_version_no_negativo",
        ),
        Index("ix_usuarios_username_lower", func.lower(username), unique=True),
        Index(
            "ix_usuarios_email_lower",
            func.lower(email),
            unique=True,
            postgresql_where=email.is_not(None),
            sqlite_where=email.is_not(None),
        ),
    )
