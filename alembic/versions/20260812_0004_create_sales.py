"""create sales

Revision ID: 20260812_0004
Revises: 20260812_0003
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260812_0004"
down_revision: str | None = "20260812_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


estado_venta = postgresql.ENUM(
    "COMPLETADA",
    "ANULADA",
    name="estado_venta",
    create_type=False,
)


def upgrade() -> None:
    estado_venta.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ventas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("cliente_nombre", sa.String(length=120), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("estado", estado_venta, nullable=False),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("anulada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_anulacion", sa.Text(), nullable=True),
        sa.CheckConstraint("subtotal >= 0", name="ck_ventas_subtotal_no_negativo"),
        sa.CheckConstraint("total >= 0", name="ck_ventas_total_no_negativo"),
        sa.CheckConstraint(
            "length(trim(cliente_nombre)) > 0",
            name="ck_ventas_cliente_nombre_no_vacio",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
            name="fk_ventas_cliente_id_clientes",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ventas"),
    )
    op.create_index("ix_ventas_cliente_id", "ventas", ["cliente_id"])
    op.create_index("ix_ventas_estado", "ventas", ["estado"])
    op.create_index("ix_ventas_usuario_id", "ventas", ["usuario_id"])
    op.create_index("ix_ventas_created_at_id", "ventas", ["created_at", "id"])

    op.create_table(
        "detalle_ventas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("producto_sku", sa.String(length=30), nullable=False),
        sa.Column("producto_nombre", sa.String(length=120), nullable=False),
        sa.Column(
            "precio_unitario",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "cantidad > 0",
            name="ck_detalle_ventas_cantidad_positiva",
        ),
        sa.CheckConstraint(
            "precio_unitario >= 0",
            name="ck_detalle_ventas_precio_unitario_no_negativo",
        ),
        sa.CheckConstraint(
            "subtotal >= 0",
            name="ck_detalle_ventas_subtotal_no_negativo",
        ),
        sa.CheckConstraint(
            "length(trim(producto_sku)) > 0",
            name="ck_detalle_ventas_producto_sku_no_vacio",
        ),
        sa.CheckConstraint(
            "length(trim(producto_nombre)) > 0",
            name="ck_detalle_ventas_producto_nombre_no_vacio",
        ),
        sa.ForeignKeyConstraint(
            ["venta_id"],
            ["ventas.id"],
            name="fk_detalle_ventas_venta_id_ventas",
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"],
            ["productos.id"],
            name="fk_detalle_ventas_producto_id_productos",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_detalle_ventas"),
    )
    op.create_index("ix_detalle_ventas_venta_id", "detalle_ventas", ["venta_id"])
    op.create_index(
        "ix_detalle_ventas_producto_id",
        "detalle_ventas",
        ["producto_id"],
    )
    op.create_index(
        "ix_detalle_ventas_venta_producto",
        "detalle_ventas",
        ["venta_id", "producto_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_detalle_ventas_venta_producto", table_name="detalle_ventas")
    op.drop_index("ix_detalle_ventas_producto_id", table_name="detalle_ventas")
    op.drop_index("ix_detalle_ventas_venta_id", table_name="detalle_ventas")
    op.drop_table("detalle_ventas")

    op.drop_index("ix_ventas_created_at_id", table_name="ventas")
    op.drop_index("ix_ventas_usuario_id", table_name="ventas")
    op.drop_index("ix_ventas_estado", table_name="ventas")
    op.drop_index("ix_ventas_cliente_id", table_name="ventas")
    op.drop_table("ventas")
    estado_venta.drop(op.get_bind(), checkfirst=True)
