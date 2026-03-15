from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constants import QuizAnswerOutcome, QuizCategory, QuizRunStatus, SupportedLanguage
from app.db.base import Base
from app.repositories.learning_progress import LearningProgressRepository
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
from app.services.quiz.engine import Question
from app.services.statistics import UserStatsSummary


def test_accuracy_percent_handles_zero_and_rounding() -> None:
    assert UserStatsSummary().accuracy_percent == 0
    assert UserStatsSummary(resolved_questions=3, correct_answers=2).accuracy_percent == 67


async def test_quiz_run_repository_aggregates_user_summary() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(1, "tester", "Tester")
        user.language = SupportedLanguage.EN.value

        repo = QuizRunRepository(session)
        run = await repo.create_run(
            user_id=user.id,
            language=SupportedLanguage.EN,
            countries_count=10,
            categories=[QuizCategory.FLAG, QuizCategory.CAPITAL],
            total_questions=20,
        )
        question = Question(
            id="DEU:capital",
            country_code="DEU",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Berlin", "Paris", "Rome", "Madrid"],
            correct_option="Berlin",
            answer_context="Berlin",
        )
        await repo.save_question_result(
            quiz_run_id=run.id,
            question=question,
            selected_option="Berlin",
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=1,
        )
        await LearningProgressRepository(session).record_result(
            user_id=user.id,
            question=question,
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=1,
        )
        await repo.finish_run(
            quiz_run_id=run.id,
            status=QuizRunStatus.COMPLETED,
            resolved_questions=1,
            correct_answers=1,
            skipped_answers=0,
            wrong_attempts=1,
        )
        await session.commit()

        summary = await repo.get_user_summary(user.id)

    await engine.dispose()

    assert summary.quizzes_started == 1
    assert summary.quizzes_completed == 1
    assert summary.resolved_questions == 1
    assert summary.correct_answers == 1
    assert summary.wrong_attempts == 1
    assert summary.tracked_items == 1
    assert summary.due_items == 0
    assert summary.last_completed_at is not None


async def test_learning_progress_repository_tracks_mastery() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(2, "student", "Student")
        user.language = SupportedLanguage.EN.value
        progress_repo = LearningProgressRepository(session)
        question = Question(
            id="FRA:capital",
            country_code="FRA",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Paris", "Berlin", "Rome", "Madrid"],
            correct_option="Paris",
            answer_context="Paris",
        )

        await progress_repo.record_result(
            user_id=user.id,
            question=question,
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=0,
        )
        await progress_repo.record_result(
            user_id=user.id,
            question=question,
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=0,
        )
        await progress_repo.record_result(
            user_id=user.id,
            question=question,
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=0,
        )
        await session.commit()

        tracked_items, mastered_items = await progress_repo.get_progress_counters(user.id)

    await engine.dispose()

    assert tracked_items == 1
    assert mastered_items == 1


async def test_due_country_codes_returns_only_due_items_for_selected_categories() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(3, "reviewer", "Reviewer")
        user.language = SupportedLanguage.EN.value
        progress_repo = LearningProgressRepository(session)
        now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
        due_question = Question(
            id="UKR:capital",
            country_code="UKR",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Kyiv", "Paris", "Rome", "Madrid"],
            correct_option="Kyiv",
            answer_context="Kyiv",
        )
        future_question = Question(
            id="DEU:flag",
            country_code="DEU",
            category=QuizCategory.FLAG,
            prompt="Flag?",
            options=["Germany", "France", "Italy", "Spain"],
            correct_option="Germany",
            answer_context="Germany",
        )

        due_progress = await progress_repo.record_result(
            user_id=user.id,
            question=due_question,
            outcome=QuizAnswerOutcome.SKIPPED,
            wrong_attempts=0,
        )
        due_progress.next_review_at = now - timedelta(hours=1)

        future_progress = await progress_repo.record_result(
            user_id=user.id,
            question=future_question,
            outcome=QuizAnswerOutcome.CORRECT,
            wrong_attempts=0,
        )
        future_progress.next_review_at = now + timedelta(days=2)
        await session.commit()

        due_codes = await progress_repo.get_due_country_codes(
            user.id,
            [QuizCategory.CAPITAL, QuizCategory.FLAG],
            10,
            now=now,
        )
        due_count = await progress_repo.get_due_items_count(user.id, now=now)

    await engine.dispose()

    assert due_codes == ["UKR"]
    assert due_count == 1
