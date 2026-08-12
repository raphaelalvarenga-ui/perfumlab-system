"""create inventory movements

Revision ID: 20260812_0003
Revises: 20260811_0002
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260812_0003"
down_revision: str | None = "20260811_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


tipo_movimiento_inventario = postgresql.ENUM(
    "ENTRADA",
    "SALIDA",
    "AJUSTE",
    name="tipo_movimiento_inventario",
    create_type=False,
)


def upgrade() -> None:
    tipo_movimiento_inventario.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "movimientos_inventario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_movimiento_inventario, nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("stock_anterior", sa.Integer(), nullable=False),
        sa.Column("stock_nuevo", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("cantidad > 0", name="ck_mov_inv_cantidad_positiva"),
        sa.CheckConstraint(
            "stock_anterior >= 0",
            name="ck_mov_inv_stock_anterior_no_negativo",
        ),
        sa.CheckConstraint(
            "stock_nuevo >= 0",
            name="ck_mov_inv_stock_nuevo_no_negativo",
        ),
        sa.CheckConstraint(
            "length(trim(motivo)) > 0",
            name="ck_mov_inv_motivo_no_vacio",
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"],
            ["productos.id"],
            name="fk_movimientos_inventario_producto_id_productos",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_movimientos_inventario"),
    )
    op.create_index(
        "ix_movimientos_inventario_producto_id",
        "movimientos_inventario",
        ["producto_id"],
    )
    op.create_index(
        "ix_movimientos_inventario_tipo",
        "movimientos_inventario",
        ["tipo"],
    )
    op.create_index(
        "ix_movimientos_inventario_usuario_id",
        "movimientos_inventario",
        ["usuario_id"],
    )
    op.create_index(
        "ix_movimientos_inventario_created_at_id",
        "movimientos_inventario",
        ["created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_movimientos_inventario_created_at_id",
        table_name="movimientos_inventario",
    )
    op.drop_index(
        "ix_movimientos_inventario_usuario_id",
        table_name="movimientos_inventario",
    )
    op.drop_index("ix_movimientos_inventario_tipo", table_name="movimientos_inventario")
    op.drop_index(
        "ix_movimientos_inventario_producto_id",
        table_name="movimientos_inventario",
    )
    op.drop_table("movimientos_inventario")
    tipo_movimiento_inventario.drop(op.get_bind(), checkfirst=True)
