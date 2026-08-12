"""create users and auth audit

Revision ID: 20260812_0006
Revises: 20260812_0005
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260812_0006"
down_revision: str | None = "20260812_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


rol_usuario = postgresql.ENUM(
    "ADMINISTRADOR",
    "VENDEDOR",
    name="rol_usuario",
    create_type=False,
)


def upgrade() -> None:
    rol_usuario.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("username", sa.String(length=60), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", rol_usuario, nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(trim(nombre)) > 0",
            name="ck_usuarios_nombre_no_vacio",
        ),
        sa.CheckConstraint(
            "length(trim(username)) > 0",
            name="ck_usuarios_username_no_vacio",
        ),
        sa.CheckConstraint(
            "length(trim(password_hash)) > 0",
            name="ck_usuarios_password_hash_no_vacio",
        ),
        sa.CheckConstraint(
            "token_version >= 0",
            name="ck_usuarios_token_version_no_negativo",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios"),
    )
    op.create_index("ix_usuarios_username", "usuarios", ["username"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"])
    op.create_index("ix_usuarios_rol", "usuarios", ["rol"])
    op.create_index(
        "ix_usuarios_username_lower",
        "usuarios",
        [sa.text("lower(username)")],
        unique=True,
    )
    op.create_index(
        "ix_usuarios_email_lower",
        "usuarios",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.add_column(
        "ventas",
        sa.Column("anulada_por_usuario_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_ventas_anulada_por_usuario_id",
        "ventas",
        ["anulada_por_usuario_id"],
    )
    op.create_foreign_key(
        "fk_ventas_usuario_id_usuarios",
        "ventas",
        "usuarios",
        ["usuario_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ventas_anulada_por_usuario_id_usuarios",
        "ventas",
        "usuarios",
        ["anulada_por_usuario_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_movimientos_inventario_usuario_id_usuarios",
        "movimientos_inventario",
        "usuarios",
        ["usuario_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("facturas", sa.Column("usuario_id", sa.Integer(), nullable=True))
    op.add_column(
        "facturas",
        sa.Column("anulada_por_usuario_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_facturas_usuario_id", "facturas", ["usuario_id"])
    op.create_index(
        "ix_facturas_anulada_por_usuario_id",
        "facturas",
        ["anulada_por_usuario_id"],
    )
    op.create_foreign_key(
        "fk_facturas_usuario_id_usuarios",
        "facturas",
        "usuarios",
        ["usuario_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_facturas_anulada_por_usuario_id_usuarios",
        "facturas",
        "usuarios",
        ["anulada_por_usuario_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_facturas_anulada_por_usuario_id_usuarios",
        "facturas",
        type_="foreignkey",
    )
    op.drop_constraint("fk_facturas_usuario_id_usuarios", "facturas", type_="foreignkey")
    op.drop_index("ix_facturas_anulada_por_usuario_id", table_name="facturas")
    op.drop_index("ix_facturas_usuario_id", table_name="facturas")
    op.drop_column("facturas", "anulada_por_usuario_id")
    op.drop_column("facturas", "usuario_id")

    op.drop_constraint(
        "fk_movimientos_inventario_usuario_id_usuarios",
        "movimientos_inventario",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_ventas_anulada_por_usuario_id_usuarios",
        "ventas",
        type_="foreignkey",
    )
    op.drop_constraint("fk_ventas_usuario_id_usuarios", "ventas", type_="foreignkey")
    op.drop_index("ix_ventas_anulada_por_usuario_id", table_name="ventas")
    op.drop_column("ventas", "anulada_por_usuario_id")

    op.drop_index("ix_usuarios_email_lower", table_name="usuarios")
    op.drop_index("ix_usuarios_username_lower", table_name="usuarios")
    op.drop_index("ix_usuarios_rol", table_name="usuarios")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_index("ix_usuarios_username", table_name="usuarios")
    op.drop_table("usuarios")
    rol_usuario.drop(op.get_bind(), checkfirst=True)
