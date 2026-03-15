from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import QUESTION_ORDER, QuizAnswerOutcome, QuizCategory
from app.db.models import UserLearningProgress
from app.services.quiz.engine import Question
from app.services.srs import schedule_next_review
from app.services.statistics import CategoryProgressStat


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
        progress.next_review_at = schedule_next_review(
            outcome,
            progress.proficiency_score,
            wrong_attempts,
            progress.current_streak,
            now=progress.last_reviewed_at,
        )

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

    async def get_category_breakdown(
        self,
        user_id: int,
        *,
        now: datetime | None = None,
    ) -> list[CategoryProgressStat]:
        current_time = now or datetime.now(UTC)
        stmt = (
            select(
                UserLearningProgress.category,
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
                func.coalesce(
                    func.sum(
                        case(
                            (
                                UserLearningProgress.next_review_at.is_not(None)
                                & (UserLearningProgress.next_review_at <= current_time),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(func.sum(UserLearningProgress.correct_answers), 0),
                func.coalesce(func.sum(UserLearningProgress.attempts_count), 0),
            )
            .where(UserLearningProgress.user_id == user_id)
            .group_by(UserLearningProgress.category)
        )
        result = await self._session.execute(stmt)
        stats_by_category = {
            QuizCategory(row[0]): CategoryProgressStat(
                category=QuizCategory(row[0]),
                tracked_items=int(row[1] or 0),
                mastered_items=int(row[2] or 0),
                due_items=int(row[3] or 0),
                correct_answers=int(row[4] or 0),
                attempts_count=int(row[5] or 0),
            )
            for row in result.all()
        }
        return [
            stats_by_category[category]
            for category in QUESTION_ORDER
            if category in stats_by_category
        ]

    async def get_due_country_codes(
        self,
        user_id: int,
        categories: list[QuizCategory],
        limit: int,
        *,
        now: datetime | None = None,
    ) -> list[str]:
        current_time = now or datetime.now(UTC)
        stmt = (
            select(
                UserLearningProgress.country_code,
                func.min(UserLearningProgress.next_review_at).label("next_due"),
            )
            .where(
                UserLearningProgress.user_id == user_id,
                UserLearningProgress.category.in_([category.value for category in categories]),
                UserLearningProgress.next_review_at.is_not(None),
                UserLearningProgress.next_review_at <= current_time,
            )
            .group_by(UserLearningProgress.country_code)
            .order_by("next_due")
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_due_items_count(
        self,
        user_id: int,
        *,
        now: datetime | None = None,
    ) -> int:
        current_time = now or datetime.now(UTC)
        stmt = select(func.count(UserLearningProgress.id)).where(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.next_review_at.is_not(None),
            UserLearningProgress.next_review_at <= current_time,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def get_studied_country_codes(
        self,
        user_id: int,
        categories: list[QuizCategory],
    ) -> list[str]:
        stmt = (
            select(UserLearningProgress.country_code)
            .where(
                UserLearningProgress.user_id == user_id,
                UserLearningProgress.category.in_([category.value for category in categories]),
            )
            .group_by(UserLearningProgress.country_code)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]
