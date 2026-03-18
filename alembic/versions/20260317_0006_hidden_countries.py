"""add hidden countries

Revision ID: 20260317_0006
Revises: 20260317_0005
Create Date: 2026-03-17 02:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260317_0006"
down_revision: str | None = "20260317_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hidden_countries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "country_code", name="uq_hidden_countries_user_country"),
    )
    op.create_index(
        op.f("ix_hidden_countries_user_id"),
        "hidden_countries",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hidden_countries_user_id"), table_name="hidden_countries")
    op.drop_table("hidden_countries")
