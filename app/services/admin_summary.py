from dataclasses import dataclass


@dataclass(slots=True)
class AdminOverview:
    users_count: int
    quiz_runs_count: int
    completed_quiz_runs_count: int
    in_progress_quiz_runs_count: int
    tracked_progress_items: int
    due_progress_items: int


@dataclass(slots=True)
class ProgressCountryStat:
    country_code: str
    attempts_count: int
    correct_answers: int
    skipped_answers: int
    wrong_attempts: int
    proficiency_score: int


def accuracy_ratio(correct_answers: int, attempts_count: int) -> float:
    if attempts_count == 0:
        return 0.0
    return correct_answers / attempts_count
