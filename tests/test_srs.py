from datetime import UTC, datetime, timedelta

from app.constants import QuizAnswerOutcome
from app.services.srs import schedule_next_review


def test_schedule_next_review_for_clean_correct_answer() -> None:
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    next_review = schedule_next_review(
        QuizAnswerOutcome.CORRECT,
        proficiency_score=6,
        wrong_attempts=0,
        current_streak=2,
        now=now,
    )

    assert next_review == now + timedelta(days=7)


def test_schedule_next_review_for_skipped_answer_is_soon() -> None:
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    next_review = schedule_next_review(
        QuizAnswerOutcome.SKIPPED,
        proficiency_score=3,
        wrong_attempts=0,
        current_streak=0,
        now=now,
    )

    assert next_review == now + timedelta(hours=8)


def test_schedule_next_review_with_high_streak_gets_interval_boost() -> None:
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    next_review = schedule_next_review(
        QuizAnswerOutcome.CORRECT,
        proficiency_score=8,
        wrong_attempts=0,
        current_streak=4,
        now=now,
    )

    assert next_review == now + timedelta(days=28)


def test_schedule_next_review_after_wrong_attempts_stays_short() -> None:
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    next_review = schedule_next_review(
        QuizAnswerOutcome.CORRECT,
        proficiency_score=6,
        wrong_attempts=2,
        current_streak=1,
        now=now,
    )

    assert next_review == now + timedelta(hours=8)
