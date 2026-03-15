from datetime import UTC, datetime, timedelta

from app.constants import QuizAnswerOutcome
from app.services.srs import schedule_next_review


def test_schedule_next_review_for_clean_correct_answer() -> None:
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    next_review = schedule_next_review(
        QuizAnswerOutcome.CORRECT,
        proficiency_score=6,
        wrong_attempts=0,
        now=now,
    )

    assert next_review == now + timedelta(days=7)


def test_schedule_next_review_for_skipped_answer_is_soon() -> None:
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    next_review = schedule_next_review(
        QuizAnswerOutcome.SKIPPED,
        proficiency_score=3,
        wrong_attempts=0,
        now=now,
    )

    assert next_review == now + timedelta(hours=12)
