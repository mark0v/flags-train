"""add quiz run mode

Revision ID: 20260317_0005
Revises: 20260315_0004
Create Date: 2026-03-17 01:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260317_0005"
down_revision: str | None = "20260315_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quiz_runs",
        sa.Column(
            "mode",
            sa.String(length=20),
            nullable=False,
            server_default="mixed",
        ),
    )
    op.alter_column("quiz_runs", "mode", server_default=None)


def downgrade() -> None:
    op.drop_column("quiz_runs", "mode")
