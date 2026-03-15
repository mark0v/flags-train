from datetime import UTC, datetime

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import QuizRunStatus
from app.db.models import QuizRun, User, UserLearningProgress
from app.services.admin_summary import AdminOverview, ProgressCountryStat, accuracy_ratio


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def overview(self, *, now: datetime | None = None) -> AdminOverview:
        current_time = now or datetime.now(UTC)
        users_count = int(await self._session.scalar(select(func.count(User.id))) or 0)
        quiz_runs_count = int(await self._session.scalar(select(func.count(QuizRun.id))) or 0)
        completed_quiz_runs_count = int(
            await self._session.scalar(
                select(func.count(QuizRun.id)).where(
                    QuizRun.status == QuizRunStatus.COMPLETED.value
                )
            )
            or 0
        )
        in_progress_quiz_runs_count = int(
            await self._session.scalar(
                select(func.count(QuizRun.id)).where(
                    QuizRun.status == QuizRunStatus.IN_PROGRESS.value
                )
            )
            or 0
        )
        tracked_progress_items = int(
            await self._session.scalar(select(func.count(UserLearningProgress.id))) or 0
        )
        due_progress_items = int(
            await self._session.scalar(
                select(func.count(UserLearningProgress.id)).where(
                    UserLearningProgress.next_review_at.is_not(None),
                    UserLearningProgress.next_review_at <= current_time,
                )
            )
            or 0
        )
        return AdminOverview(
            users_count=users_count,
            quiz_runs_count=quiz_runs_count,
            completed_quiz_runs_count=completed_quiz_runs_count,
            in_progress_quiz_runs_count=in_progress_quiz_runs_count,
            tracked_progress_items=tracked_progress_items,
            due_progress_items=due_progress_items,
        )

    async def weakest_countries(self, limit: int = 5) -> list[ProgressCountryStat]:
        stmt = select(UserLearningProgress).order_by(
            asc(UserLearningProgress.proficiency_score),
            desc(UserLearningProgress.wrong_attempts),
            desc(UserLearningProgress.attempts_count),
            asc(UserLearningProgress.country_code),
        ).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_progress_stat(row) for row in rows]

    async def strongest_countries(self, limit: int = 5) -> list[ProgressCountryStat]:
        stmt = select(UserLearningProgress).order_by(
            desc(UserLearningProgress.proficiency_score),
            desc(UserLearningProgress.current_streak),
            desc(UserLearningProgress.correct_answers),
            asc(UserLearningProgress.country_code),
        ).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_progress_stat(row) for row in rows]

    @staticmethod
    def _to_progress_stat(progress: UserLearningProgress) -> ProgressCountryStat:
        return ProgressCountryStat(
            country_code=progress.country_code,
            attempts_count=progress.attempts_count,
            correct_answers=progress.correct_answers,
            skipped_answers=progress.skipped_answers,
            wrong_attempts=progress.wrong_attempts,
            proficiency_score=progress.proficiency_score,
        )


def format_progress_country_stat(stat: ProgressCountryStat) -> str:
    accuracy = round(accuracy_ratio(stat.correct_answers, stat.attempts_count) * 100)
    return (
        f"{stat.country_code}: attempts={stat.attempts_count}, "
        f"correct={stat.correct_answers}, skipped={stat.skipped_answers}, "
        f"wrong={stat.wrong_attempts}, score={stat.proficiency_score}, accuracy={accuracy}%"
    )
