"""add user learning progress

Revision ID: 20260315_0003
Revises: 20260315_0002
Create Date: 2026-03-15 18:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260315_0003"
down_revision: str | None = "20260315_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_learning_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("attempts_count", sa.Integer(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), nullable=False),
        sa.Column("skipped_answers", sa.Integer(), nullable=False),
        sa.Column("wrong_attempts", sa.Integer(), nullable=False),
        sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("proficiency_score", sa.Integer(), nullable=False),
        sa.Column("last_outcome", sa.String(length=20), nullable=True),
        sa.Column(
            "last_reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "country_code",
            "category",
            name="uq_learning_progress_user_country_category",
        ),
    )
    op.create_index(
        op.f("ix_user_learning_progress_user_id"),
        "user_learning_progress",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_learning_progress_user_id"), table_name="user_learning_progress")
    op.drop_table("user_learning_progress")
