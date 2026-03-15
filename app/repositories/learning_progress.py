from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import QuizAnswerOutcome
from app.db.models import UserLearningProgress
from app.services.quiz.engine import Question


class LearningProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_result(
        self,
        user_id: int,
        question: Question,
        outcome: QuizAnswerOutcome,
        wrong_attempts: int,
    ) -> UserLearningProgress:
        stmt = select(UserLearningProgress).where(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.country_code == question.country_code,
            UserLearningProgress.category == question.category.value,
        )
        result = await self._session.execute(stmt)
        progress = result.scalar_one_or_none()
        if progress is None:
            progress = UserLearningProgress(
                user_id=user_id,
                country_code=question.country_code,
                category=question.category.value,
                attempts_count=0,
                correct_answers=0,
                skipped_answers=0,
                wrong_attempts=0,
                current_streak=0,
                proficiency_score=0,
            )
            self._session.add(progress)

        progress.attempts_count += 1
        progress.wrong_attempts += wrong_attempts
        progress.last_outcome = outcome.value
        progress.last_reviewed_at = datetime.now(UTC)

        if outcome is QuizAnswerOutcome.CORRECT:
            progress.correct_answers += 1
            progress.current_streak = progress.current_streak + 1 if wrong_attempts == 0 else 1
            progress.proficiency_score += 2 if wrong_attempts == 0 else 1
        else:
            progress.skipped_answers += 1
            progress.current_streak = 0
            progress.proficiency_score = max(0, progress.proficiency_score - 1)

        await self._session.flush()
        return progress

    async def get_progress_counters(self, user_id: int) -> tuple[int, int]:
        stmt = select(
            func.count(UserLearningProgress.id),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (UserLearningProgress.proficiency_score >= 5)
                            & (UserLearningProgress.current_streak >= 2),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
        ).where(UserLearningProgress.user_id == user_id)
        result = await self._session.execute(stmt)
        row = result.one()
        return int(row[0] or 0), int(row[1] or 0)
