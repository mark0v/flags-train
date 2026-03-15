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


def test_wrong_answer_keeps_question_active_until_skip() -> None:
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

    session.on_correct()
    assert any(item.id == first.id for item in session.retry_queue)

    session.current_question()
    session.skip_current()
    assert any(item.id == first.id for item in session.retry_queue)
