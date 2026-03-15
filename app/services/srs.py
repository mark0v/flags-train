from datetime import UTC, datetime, timedelta

from app.constants import QuizAnswerOutcome


def schedule_next_review(
    outcome: QuizAnswerOutcome,
    proficiency_score: int,
    wrong_attempts: int,
    *,
    now: datetime | None = None,
) -> datetime:
    current_time = now or datetime.now(UTC)

    if outcome is QuizAnswerOutcome.SKIPPED:
        return current_time + timedelta(hours=12)

    if wrong_attempts > 0:
        return current_time + timedelta(days=1)

    if proficiency_score <= 1:
        return current_time + timedelta(days=1)
    if proficiency_score <= 3:
        return current_time + timedelta(days=2)
    if proficiency_score <= 5:
        return current_time + timedelta(days=4)
    if proficiency_score <= 7:
        return current_time + timedelta(days=7)
    if proficiency_score <= 9:
        return current_time + timedelta(days=14)
    return current_time + timedelta(days=30)
