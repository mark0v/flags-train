"""add quiz runs and answers

Revision ID: 20260315_0002
Revises: 20260315_0001
Create Date: 2026-03-15 17:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260315_0002"
down_revision: str | None = "20260315_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quiz_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=False),
        sa.Column("countries_count", sa.Integer(), nullable=False),
        sa.Column("categories_csv", sa.String(length=255), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("resolved_questions", sa.Integer(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), nullable=False),
        sa.Column("skipped_answers", sa.Integer(), nullable=False),
        sa.Column("wrong_attempts", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quiz_runs_user_id"), "quiz_runs", ["user_id"], unique=False)

    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_run_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("selected_option", sa.Text(), nullable=True),
        sa.Column("correct_option", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("wrong_attempts", sa.Integer(), nullable=False),
        sa.Column(
            "answered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["quiz_run_id"], ["quiz_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_run_id", "question_id", name="uq_quiz_answers_run_question"),
    )
    op.create_index(
        op.f("ix_quiz_answers_quiz_run_id"),
        "quiz_answers",
        ["quiz_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_quiz_answers_quiz_run_id"), table_name="quiz_answers")
    op.drop_table("quiz_answers")
    op.drop_index(op.f("ix_quiz_runs_user_id"), table_name="quiz_runs")
    op.drop_table("quiz_runs")
