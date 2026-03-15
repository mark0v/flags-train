from datetime import UTC, datetime, timedelta

from app.constants import QuizAnswerOutcome


def schedule_next_review(
    outcome: QuizAnswerOutcome,
    proficiency_score: int,
    wrong_attempts: int,
    current_streak: int,
    *,
    now: datetime | None = None,
) -> datetime:
    current_time = now or datetime.now(UTC)

    if outcome is QuizAnswerOutcome.SKIPPED:
        return current_time + timedelta(hours=8)

    if wrong_attempts > 0:
        if wrong_attempts >= 2:
            return current_time + timedelta(hours=8)
        return current_time + timedelta(hours=16)

    if proficiency_score <= 1:
        interval = timedelta(hours=12)
    elif proficiency_score <= 3:
        interval = timedelta(days=1)
    elif proficiency_score <= 5:
        interval = timedelta(days=3)
    elif proficiency_score <= 7:
        interval = timedelta(days=7)
    elif proficiency_score <= 9:
        interval = timedelta(days=14)
    else:
        interval = timedelta(days=30)

    if current_streak >= 4:
        interval = min(interval * 2, timedelta(days=45))
    return current_time + interval
