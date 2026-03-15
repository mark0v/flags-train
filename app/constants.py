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


QUESTION_ORDER = [
    QuizCategory.FLAG,
    QuizCategory.CAPITAL,
    QuizCategory.LANGUAGE,
    QuizCategory.POPULATION,
    QuizCategory.CURRENCY,
]

QUIZ_SIZES = [10, 25, 50]
