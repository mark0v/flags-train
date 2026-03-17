from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    EXPOSED_QUIZ_CATEGORIES,
    QuizAnswerOutcome,
    QuizCategory,
    QuizMode,
    QuizRunStatus,
    SupportedLanguage,
)
from app.db.models import QuizAnswer, QuizRun
from app.repositories.learning_progress import LearningProgressRepository
from app.services.quiz.engine import Question
from app.services.statistics import LastQuizPreferences, UserStatsSummary


class QuizRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        user_id: int,
        language: SupportedLanguage,
        mode: QuizMode,
        countries_count: int,
        categories: list[QuizCategory],
        total_questions: int,
    ) -> QuizRun:
        quiz_run = QuizRun(
            user_id=user_id,
            language=language.value,
            mode=mode.value,
            countries_count=countries_count,
            categories_csv=",".join(category.value for category in categories),
            total_questions=total_questions,
            status=QuizRunStatus.IN_PROGRESS.value,
        )
        self._session.add(quiz_run)
        await self._session.flush()
        return quiz_run

    async def save_question_result(
        self,
        quiz_run_id: int,
        question: Question,
        selected_option: str | None,
        outcome: QuizAnswerOutcome,
        wrong_attempts: int,
    ) -> QuizAnswer:
        stmt = select(QuizAnswer).where(
            QuizAnswer.quiz_run_id == quiz_run_id,
            QuizAnswer.question_id == question.id,
        )
        result = await self._session.execute(stmt)
        answer = result.scalar_one_or_none()
        if answer is None:
            answer = QuizAnswer(
                quiz_run_id=quiz_run_id,
                question_id=question.id,
                country_code=question.country_code,
                category=question.category.value,
                correct_option=question.correct_option,
            )
            self._session.add(answer)

        answer.selected_option = selected_option
        answer.outcome = outcome.value
        answer.wrong_attempts = wrong_attempts
        answer.answered_at = datetime.now(UTC)
        await self._session.flush()
        return answer

    async def finish_run(
        self,
        quiz_run_id: int,
        status: QuizRunStatus,
        resolved_questions: int,
        correct_answers: int,
        skipped_answers: int,
        wrong_attempts: int,
    ) -> QuizRun:
        stmt = select(QuizRun).where(QuizRun.id == quiz_run_id)
        result = await self._session.execute(stmt)
        quiz_run = result.scalar_one()
        quiz_run.status = status.value
        quiz_run.resolved_questions = resolved_questions
        quiz_run.correct_answers = correct_answers
        quiz_run.skipped_answers = skipped_answers
        quiz_run.wrong_attempts = wrong_attempts
        quiz_run.completed_at = datetime.now(UTC)
        await self._session.flush()
        return quiz_run

    async def get_user_summary(self, user_id: int) -> UserStatsSummary:
        recent_cutoff = datetime.now(UTC) - timedelta(days=7)
        stmt = select(
            func.count(QuizRun.id),
            func.coalesce(
                func.sum(case((QuizRun.status == QuizRunStatus.COMPLETED.value, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((QuizRun.status == QuizRunStatus.ABANDONED.value, 1), else_=0)),
                0,
            ),
            func.coalesce(func.sum(QuizRun.resolved_questions), 0),
            func.coalesce(func.sum(QuizRun.correct_answers), 0),
            func.coalesce(func.sum(QuizRun.skipped_answers), 0),
            func.coalesce(func.sum(QuizRun.wrong_attempts), 0),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (QuizRun.status == QuizRunStatus.COMPLETED.value)
                            & (QuizRun.completed_at >= recent_cutoff),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.max(QuizRun.completed_at),
        ).where(QuizRun.user_id == user_id)
        result = await self._session.execute(stmt)
        row = result.one()
        progress_repo = LearningProgressRepository(self._session)
        tracked_items, mastered_items = await progress_repo.get_progress_counters(
            user_id,
            EXPOSED_QUIZ_CATEGORIES,
        )
        due_items = await progress_repo.get_due_items_count(user_id, EXPOSED_QUIZ_CATEGORIES)
        due_countries = await progress_repo.get_due_country_count(
            user_id,
            EXPOSED_QUIZ_CATEGORIES,
        )
        category_breakdown = await progress_repo.get_category_breakdown(
            user_id,
            EXPOSED_QUIZ_CATEGORIES,
        )
        return UserStatsSummary(
            quizzes_started=row[0] or 0,
            quizzes_completed=row[1] or 0,
            quizzes_abandoned=row[2] or 0,
            resolved_questions=row[3] or 0,
            correct_answers=row[4] or 0,
            skipped_answers=row[5] or 0,
            wrong_attempts=row[6] or 0,
            completed_last_7_days=row[7] or 0,
            last_completed_at=row[8],
            tracked_items=tracked_items,
            mastered_items=mastered_items,
            due_items=due_items,
            due_countries=due_countries,
            category_breakdown=category_breakdown,
        )

    async def get_last_quiz_preferences(self, user_id: int) -> LastQuizPreferences | None:
        stmt = (
            select(QuizRun.countries_count, QuizRun.categories_csv, QuizRun.mode)
            .where(QuizRun.user_id == user_id)
            .order_by(QuizRun.started_at.desc(), QuizRun.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if row is None:
            return None

        categories = [
            QuizCategory(value)
            for value in row[1].split(",")
            if value
        ]
        return LastQuizPreferences(
            countries_count=int(row[0]),
            categories=categories,
            mode=QuizMode(row[2] or QuizMode.MIXED.value),
        )
