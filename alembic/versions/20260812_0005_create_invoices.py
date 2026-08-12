"""create invoices

Revision ID: 20260812_0005
Revises: 20260812_0004
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260812_0005"
down_revision: str | None = "20260812_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


estado_factura = postgresql.ENUM(
    "EMITIDA",
    "ANULADA",
    name="estado_factura",
    create_type=False,
)


def upgrade() -> None:
    estado_factura.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "facturas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("cliente_nombre", sa.String(length=120), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("estado", estado_factura, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("anulada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_anulacion", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "length(trim(numero)) > 0",
            name="ck_facturas_numero_no_vacio",
        ),
        sa.CheckConstraint(
            "length(trim(cliente_nombre)) > 0",
            name="ck_facturas_cliente_nombre_no_vacio",
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_facturas_subtotal_no_negativo"),
        sa.CheckConstraint("total >= 0", name="ck_facturas_total_no_negativo"),
        sa.ForeignKeyConstraint(
            ["venta_id"],
            ["ventas.id"],
            name="fk_facturas_venta_id_ventas",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_facturas"),
    )
    op.create_index("ix_facturas_numero", "facturas", ["numero"], unique=True)
    op.create_index("ix_facturas_venta_id", "facturas", ["venta_id"], unique=True)
    op.create_index("ix_facturas_estado", "facturas", ["estado"])
    op.create_index("ix_facturas_created_at_id", "facturas", ["created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_facturas_created_at_id", table_name="facturas")
    op.drop_index("ix_facturas_estado", table_name="facturas")
    op.drop_index("ix_facturas_venta_id", table_name="facturas")
    op.drop_index("ix_facturas_numero", table_name="facturas")
    op.drop_table("facturas")
    estado_factura.drop(op.get_bind(), checkfirst=True)
