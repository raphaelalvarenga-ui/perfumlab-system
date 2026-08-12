"""create categories and products

Revision ID: 20260810_0001
Revises:
Create Date: 2026-08-10 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260810_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_categorias"),
        sa.UniqueConstraint("nombre", name="uq_categorias_nombre"),
    )
    op.create_index("ix_categorias_nombre", "categorias", ["nombre"])
    op.create_index(
        "ix_categorias_nombre_lower",
        "categorias",
        [sa.text("lower(nombre)")],
        unique=True,
    )

    op.create_table(
        "productos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=30), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("marca", sa.String(length=80), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column(
            "costo",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "precio",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "stock_actual",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "stock_minimo",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("ml", sa.Integer(), nullable=True),
        sa.Column("imagen", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("genero", sa.String(length=40), nullable=True),
        sa.Column("anio_lanzamiento", sa.Integer(), nullable=True),
        sa.Column("concentracion", sa.String(length=60), nullable=True),
        sa.Column("duracion", sa.String(length=60), nullable=True),
        sa.Column("estela", sa.String(length=60), nullable=True),
        sa.Column("external_provider", sa.String(length=80), nullable=True),
        sa.Column("external_id", sa.String(length=120), nullable=True),
        sa.Column("external_last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("costo >= 0", name="ck_productos_costo_no_negativo"),
        sa.CheckConstraint("precio >= 0", name="ck_productos_precio_no_negativo"),
        sa.CheckConstraint(
            "stock_actual >= 0",
            name="ck_productos_stock_actual_no_negativo",
        ),
        sa.CheckConstraint(
            "stock_minimo >= 0",
            name="ck_productos_stock_minimo_no_negativo",
        ),
        sa.CheckConstraint("ml IS NULL OR ml > 0", name="ck_productos_ml_positivo"),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
            name="fk_productos_categoria_id_categorias",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_productos"),
        sa.UniqueConstraint("sku", name="uq_productos_sku"),
    )
    op.create_index("ix_productos_categoria_id", "productos", ["categoria_id"])
    op.create_index("ix_productos_marca", "productos", ["marca"])
    op.create_index("ix_productos_nombre", "productos", ["nombre"])
    op.create_index("ix_productos_sku", "productos", ["sku"])
    op.create_index(
        "ix_productos_sku_lower",
        "productos",
        [sa.text("lower(sku)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_productos_sku_lower", table_name="productos")
    op.drop_index("ix_productos_sku", table_name="productos")
    op.drop_index("ix_productos_nombre", table_name="productos")
    op.drop_index("ix_productos_marca", table_name="productos")
    op.drop_index("ix_productos_categoria_id", table_name="productos")
    op.drop_table("productos")

    op.drop_index("ix_categorias_nombre_lower", table_name="categorias")
    op.drop_index("ix_categorias_nombre", table_name="categorias")
    op.drop_table("categorias")
