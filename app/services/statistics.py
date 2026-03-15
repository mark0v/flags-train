from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserStatsSummary:
    quizzes_started: int = 0
    quizzes_completed: int = 0
    resolved_questions: int = 0
    correct_answers: int = 0
    skipped_answers: int = 0
    wrong_attempts: int = 0
    tracked_items: int = 0
    mastered_items: int = 0
    last_completed_at: datetime | None = None

    @property
    def has_data(self) -> bool:
        return self.quizzes_started > 0

    @property
    def accuracy_percent(self) -> int:
        if self.resolved_questions == 0:
            return 0
        return round((self.correct_answers / self.resolved_questions) * 100)
