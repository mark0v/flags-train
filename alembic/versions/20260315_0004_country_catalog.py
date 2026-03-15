"""add country catalog

Revision ID: 20260315_0004
Revises: 20260315_0003
Create Date: 2026-03-15 20:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260315_0004"
down_revision: str | None = "20260315_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("localized_name", sa.JSON(), nullable=False),
        sa.Column("capital", sa.JSON(), nullable=False),
        sa.Column("official_language", sa.JSON(), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False),
        sa.Column("population_display", sa.JSON(), nullable=False),
        sa.Column("currency_name", sa.JSON(), nullable=False),
        sa.Column("currency_code", sa.String(length=8), nullable=False),
        sa.Column("flag_file", sa.String(length=255), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("code"),
    )


def downgrade() -> None:
    op.drop_table("countries")
