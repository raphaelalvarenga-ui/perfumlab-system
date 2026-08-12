"""add external fragrance metadata

Revision ID: 20260812_0008
Revises: 20260812_0007
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260812_0008"
down_revision: str | None = "20260812_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("external_image_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "productos",
        sa.Column("external_transparent_image_url", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_productos_external_provider_external_id",
        "productos",
        ["external_provider", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_productos_external_provider_external_id",
        "productos",
        type_="unique",
    )
    op.drop_column("productos", "external_transparent_image_url")
    op.drop_column("productos", "external_image_url")
