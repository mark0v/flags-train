from enum import StrEnum


class SupportedLanguage(StrEnum):
    RU = "ru"
    EN = "en"
    DE = "de"


class QuizCategory(StrEnum):
    FLAG = "flag"
    CAPITAL = "capital"
    LANGUAGE = "language"
    POPULATION = "population"
    CURRENCY = "currency"


class QuizRunStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class QuizAnswerOutcome(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"


class QuizMode(StrEnum):
    MIXED = "mixed"
    REVIEW = "review"
    NEW = "new"


QUESTION_ORDER = [
    QuizCategory.FLAG,
    QuizCategory.CAPITAL,
    QuizCategory.LANGUAGE,
    QuizCategory.POPULATION,
    QuizCategory.CURRENCY,
]

QUIZ_SIZES = [10, 25, 50]
