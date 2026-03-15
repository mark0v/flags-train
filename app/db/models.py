from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    quiz_runs: Mapped[list["QuizRun"]] = relationship(back_populates="user")


class QuizRun(Base):
    __tablename__ = "quiz_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    language: Mapped[str] = mapped_column(String(2))
    countries_count: Mapped[int] = mapped_column(Integer)
    categories_csv: Mapped[str] = mapped_column(String(255))
    total_questions: Mapped[int] = mapped_column(Integer)
    resolved_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    skipped_answers: Mapped[int] = mapped_column(Integer, default=0)
    wrong_attempts: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="quiz_runs")
    answers: Mapped[list["QuizAnswer"]] = relationship(back_populates="quiz_run")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    __table_args__ = (
        UniqueConstraint("quiz_run_id", "question_id", name="uq_quiz_answers_run_question"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_run_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_runs.id", ondelete="CASCADE"),
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(64))
    country_code: Mapped[str] = mapped_column(String(3))
    category: Mapped[str] = mapped_column(String(20))
    selected_option: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_option: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(20))
    wrong_attempts: Mapped[int] = mapped_column(Integer, default=0)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    quiz_run: Mapped[QuizRun] = relationship(back_populates="answers")
