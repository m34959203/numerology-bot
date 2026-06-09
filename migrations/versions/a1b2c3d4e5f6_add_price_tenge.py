"""add price_tenge to services

Revision ID: a1b2c3d4e5f6
Revises: e47bb79859ce
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e47bb79859ce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "services",
        sa.Column("price_tenge", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("services", "price_stars", server_default="0")


def downgrade() -> None:
    op.drop_column("services", "price_tenge")
