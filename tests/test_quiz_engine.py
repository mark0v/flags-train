import random
from pathlib import Path

from app.constants import QuizCategory, SupportedLanguage
from app.services.country_store import CountryStore
from app.services.quiz.engine import QuizEngine


def test_quiz_builds_country_blocks() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    engine = QuizEngine(store, random.Random(7))

    session = engine.create_session(
        language=SupportedLanguage.RU,
        countries_count=3,
        categories=[QuizCategory.FLAG, QuizCategory.CAPITAL],
    )

    questions = list(session.questions)
    assert len(questions) == 6
    assert questions[0].country_code == questions[1].country_code
    assert questions[0].category == QuizCategory.FLAG
    assert questions[1].category == QuizCategory.CAPITAL


def test_wrong_answer_resolves_as_incorrect_on_next() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    engine = QuizEngine(store, random.Random(3))
    session = engine.create_session(
        language=SupportedLanguage.EN,
        countries_count=3,
        categories=[QuizCategory.CAPITAL],
    )

    first = session.current_question()
    session.on_wrong()
    assert session.current_question().id == first.id

    next_resolution = session.resolve_incorrect()

    assert next_resolution.resolved is True
    assert next_resolution.outcome == "incorrect"
    assert session.current_question().id != first.id


def test_progress_counts_only_resolved_questions() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    engine = QuizEngine(store, random.Random(5))
    session = engine.create_session(
        language=SupportedLanguage.EN,
        countries_count=3,
        categories=[QuizCategory.CAPITAL],
    )

    assert session.progress_text() == "1/3"

    session.on_wrong()
    session.resolve_incorrect()

    assert session.progress_text() == "2/3"


def test_quiz_prioritizes_due_countries() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    engine = QuizEngine(store, random.Random(11))
    session = engine.create_session(
        language=SupportedLanguage.EN,
        countries_count=3,
        categories=[QuizCategory.CAPITAL],
        priority_country_codes=["UKR", "POL"],
    )

    questions = list(session.questions)

    assert questions[0].country_code == "UKR"
    assert questions[1].country_code == "POL"


def test_quiz_excludes_already_studied_countries_for_new_mode() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    engine = QuizEngine(store, random.Random(13))
    session = engine.create_session(
        language=SupportedLanguage.EN,
        countries_count=2,
        categories=[QuizCategory.CAPITAL],
        excluded_country_codes=["UKR", "POL", "DEU", "FRA"],
    )

    country_codes = [question.country_code for question in session.questions]

    assert set(country_codes) == {"ESP", "ITA"}


def test_non_flag_questions_also_include_country_flag() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    engine = QuizEngine(store, random.Random(17))
    session = engine.create_session(
        language=SupportedLanguage.EN,
        countries_count=1,
        categories=[QuizCategory.CAPITAL, QuizCategory.POPULATION],
    )

    questions = list(session.questions)

    assert len(questions) == 2
    assert all(question.flag_path is not None for question in questions)
    assert questions[0].flag_path == questions[1].flag_path
