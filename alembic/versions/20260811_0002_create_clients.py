"""create clients

Revision ID: 20260811_0002
Revises: 20260810_0001
Create Date: 2026-08-11 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_0002"
down_revision: str | None = "20260810_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("correo", sa.String(length=120), nullable=True),
        sa.Column("telefono", sa.String(length=25), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_clientes"),
    )
    op.create_index("ix_clientes_nombre", "clientes", ["nombre"])
    op.create_index("ix_clientes_correo", "clientes", ["correo"])
    op.create_index("ix_clientes_telefono", "clientes", ["telefono"])
    op.create_index(
        "ix_clientes_correo_lower",
        "clientes",
        [sa.text("lower(correo)")],
        unique=True,
        postgresql_where=sa.text("correo IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_clientes_correo_lower", table_name="clientes")
    op.drop_index("ix_clientes_telefono", table_name="clientes")
    op.drop_index("ix_clientes_correo", table_name="clientes")
    op.drop_index("ix_clientes_nombre", table_name="clientes")
    op.drop_table("clientes")
