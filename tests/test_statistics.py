from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constants import QuizAnswerOutcome, QuizCategory, QuizRunStatus, SupportedLanguage
from app.db.base import Base
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
    assert summary.last_completed_at is not None
