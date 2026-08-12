"""create fragrance notes and accords

Revision ID: 20260812_0007
Revises: 20260812_0006
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260812_0007"
down_revision: str | None = "20260812_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


tipo_nota = postgresql.ENUM(
    "SALIDA",
    "CORAZON",
    "FONDO",
    name="tipo_nota",
    create_type=False,
)
intensidad_acorde = postgresql.ENUM(
    "DOMINANTE",
    "PROMINENTE",
    "MODERADO",
    "SUTIL",
    name="intensidad_acorde",
    create_type=False,
)


def upgrade() -> None:
    tipo_nota.create(op.get_bind(), checkfirst=True)
    intensidad_acorde.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "acordes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(trim(nombre)) > 0",
            name="ck_acordes_nombre_no_vacio",
        ),
        sa.CheckConstraint(
            "length(trim(slug)) > 0",
            name="ck_acordes_slug_no_vacio",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_acordes"),
    )
    op.create_index("ix_acordes_nombre", "acordes", ["nombre"])
    op.create_index("ix_acordes_slug", "acordes", ["slug"], unique=True)
    op.create_index(
        "ix_acordes_slug_lower",
        "acordes",
        [sa.text("lower(slug)")],
        unique=True,
    )

    op.create_table(
        "notas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("imagen_url", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(trim(nombre)) > 0",
            name="ck_notas_nombre_no_vacio",
        ),
        sa.CheckConstraint(
            "length(trim(slug)) > 0",
            name="ck_notas_slug_no_vacio",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notas"),
    )
    op.create_index("ix_notas_nombre", "notas", ["nombre"])
    op.create_index("ix_notas_slug", "notas", ["slug"], unique=True)
    op.create_index(
        "ix_notas_slug_lower",
        "notas",
        [sa.text("lower(slug)")],
        unique=True,
    )

    op.create_table(
        "producto_acordes",
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("acorde_id", sa.Integer(), nullable=False),
        sa.Column("intensidad", intensidad_acorde, nullable=True),
        sa.Column("posicion", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "posicion IS NULL OR posicion >= 0",
            name="ck_producto_acordes_posicion_no_negativa",
        ),
        sa.ForeignKeyConstraint(
            ["acorde_id"],
            ["acordes.id"],
            name="fk_producto_acordes_acorde_id_acordes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"],
            ["productos.id"],
            name="fk_producto_acordes_producto_id_productos",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("producto_id", "acorde_id", name="pk_producto_acordes"),
    )
    op.create_index(
        "ix_producto_acordes_acorde_id",
        "producto_acordes",
        ["acorde_id"],
    )

    op.create_table(
        "producto_notas",
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("nota_id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_nota, nullable=False),
        sa.Column("posicion", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "posicion IS NULL OR posicion >= 0",
            name="ck_producto_notas_posicion_no_negativa",
        ),
        sa.ForeignKeyConstraint(
            ["nota_id"],
            ["notas.id"],
            name="fk_producto_notas_nota_id_notas",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["producto_id"],
            ["productos.id"],
            name="fk_producto_notas_producto_id_productos",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "producto_id",
            "nota_id",
            "tipo",
            name="pk_producto_notas",
        ),
    )
    op.create_index("ix_producto_notas_nota_id", "producto_notas", ["nota_id"])
    op.create_index("ix_producto_notas_tipo", "producto_notas", ["tipo"])


def downgrade() -> None:
    op.drop_index("ix_producto_notas_tipo", table_name="producto_notas")
    op.drop_index("ix_producto_notas_nota_id", table_name="producto_notas")
    op.drop_table("producto_notas")

    op.drop_index("ix_producto_acordes_acorde_id", table_name="producto_acordes")
    op.drop_table("producto_acordes")

    op.drop_index("ix_notas_slug_lower", table_name="notas")
    op.drop_index("ix_notas_slug", table_name="notas")
    op.drop_index("ix_notas_nombre", table_name="notas")
    op.drop_table("notas")

    op.drop_index("ix_acordes_slug_lower", table_name="acordes")
    op.drop_index("ix_acordes_slug", table_name="acordes")
    op.drop_index("ix_acordes_nombre", table_name="acordes")
    op.drop_table("acordes")

    intensidad_acorde.drop(op.get_bind(), checkfirst=True)
    tipo_nota.drop(op.get_bind(), checkfirst=True)
