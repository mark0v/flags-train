"""release cleanup for obsolete quiz data

Revision ID: 20260317_0007
Revises: 20260317_0006
Create Date: 2026-03-17 03:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260317_0007"
down_revision: str | None = "20260317_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("DELETE FROM quiz_answers"))
    op.execute(sa.text("DELETE FROM user_learning_progress"))
    op.execute(sa.text("DELETE FROM hidden_countries"))
    op.execute(sa.text("DELETE FROM quiz_runs"))
    op.execute(sa.text("UPDATE users SET language = 'en'"))
    op.drop_column("quiz_runs", "mode")


def downgrade() -> None:
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
