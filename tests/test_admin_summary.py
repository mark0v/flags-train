from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constants import QuizAnswerOutcome, QuizCategory, QuizRunStatus, SupportedLanguage
from app.db.base import Base
from app.repositories.admin import AdminRepository
from app.repositories.learning_progress import LearningProgressRepository
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
from app.services.quiz.engine import Question


async def test_admin_overview_aggregates_users_runs_and_due_items() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(10, "admin-user", "Admin")
        user.language = SupportedLanguage.EN.value

        run = await QuizRunRepository(session).create_run(
            user_id=user.id,
            language=SupportedLanguage.EN,
            countries_count=10,
            categories=[QuizCategory.CAPITAL],
            total_questions=10,
        )
        await QuizRunRepository(session).finish_run(
            quiz_run_id=run.id,
            status=QuizRunStatus.COMPLETED,
            resolved_questions=1,
            correct_answers=1,
            skipped_answers=0,
            wrong_attempts=0,
        )
        question = Question(
            id="UKR:capital",
            country_code="UKR",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Kyiv", "Paris", "Rome", "Madrid"],
            correct_option="Kyiv",
            answer_context="Kyiv",
        )
        progress = await LearningProgressRepository(session).record_result(
            user_id=user.id,
            question=question,
            outcome=QuizAnswerOutcome.SKIPPED,
            wrong_attempts=0,
        )
        progress.next_review_at = now - timedelta(hours=1)
        await session.commit()

        overview = await AdminRepository(session).overview(now=now)

    await engine.dispose()

    assert overview.users_count == 1
    assert overview.quiz_runs_count == 1
    assert overview.completed_quiz_runs_count == 1
    assert overview.in_progress_quiz_runs_count == 0
    assert overview.tracked_progress_items == 1
    assert overview.due_progress_items == 1


async def test_admin_progress_lists_weakest_and_strongest_countries() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(11, "progress-user", "Progress")
        user.language = SupportedLanguage.EN.value
        progress_repo = LearningProgressRepository(session)

        weak_question = Question(
            id="ESP:capital",
            country_code="ESP",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Madrid", "Paris", "Rome", "Berlin"],
            correct_option="Madrid",
            answer_context="Madrid",
        )
        strong_question = Question(
            id="DEU:capital",
            country_code="DEU",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Berlin", "Paris", "Rome", "Madrid"],
            correct_option="Berlin",
            answer_context="Berlin",
        )

        weak = await progress_repo.record_result(
            user_id=user.id,
            question=weak_question,
            outcome=QuizAnswerOutcome.SKIPPED,
            wrong_attempts=2,
        )
        strong = await progress_repo.record_result(
            user_id=user.id,
            question=strong_question,
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=0,
        )
        strong.proficiency_score = 8
        strong.current_streak = 4
        weak.proficiency_score = 0
        weak.current_streak = 0
        await session.commit()

        repository = AdminRepository(session)
        weakest = await repository.weakest_countries(limit=1)
        strongest = await repository.strongest_countries(limit=1)

    await engine.dispose()

    assert weakest[0].country_code == "ESP"
    assert strongest[0].country_code == "DEU"
