from collections import deque
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.handlers import menu as menu_handlers
from app.bot.handlers import quiz as quiz_handlers
from app.bot.keyboards.common import answer_feedback_keyboard
from app.bot.states import QuizStates
from app.config import Settings
from app.constants import (
    QuizAnswerOutcome,
    QuizCategory,
    QuizMode,
    QuizRunStatus,
    SupportedLanguage,
)
from app.db.base import Base
from app.db.models import QuizAnswer, UserLearningProgress
from app.repositories.learning_progress import LearningProgressRepository
from app.repositories.users import UserRepository
from app.services.admin_catalog import AdminCatalogDashboard
from app.services.catalog_health import CatalogHealthReport
from app.services.catalog_sync_preview import CatalogSyncPreview
from app.services.country_store import Country, CountryStore
from app.services.dataset_validation import DatasetValidationReport
from app.services.i18n import I18nService
from app.services.quiz.engine import Question
from app.services.quiz_display import quiz_option_label
from app.services.statistics import CategoryProgressStat, UserStatsSummary


def _build_callback(user_id: int = 42, username: str = "tester", first_name: str = "Test"):
    message = SimpleNamespace(
        edit_text=AsyncMock(),
        answer=AsyncMock(),
        edit_reply_markup=AsyncMock(),
        delete=AsyncMock(),
        message_id=501,
        chat=SimpleNamespace(id=100),
    )
    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=user_id, username=username, first_name=first_name),
        message=message,
        answer=AsyncMock(),
        data="",
    )
    return callback


def _build_bot():
    return SimpleNamespace(
        send_photo=AsyncMock(),
        send_document=AsyncMock(),
        edit_message_reply_markup=AsyncMock(),
    )


def _build_state() -> FSMContext:
    storage = MemoryStorage()
    return FSMContext(storage=storage, key=StorageKey(bot_id=1, chat_id=1, user_id=42))


def _build_country_store(total: int = 12) -> CountryStore:
    countries = [
        Country(
            code=f"C{i:02d}",
            localized_name={"en": f"Country {i}", "ru": f"Страна {i}", "de": f"Land {i}"},
            capital={"en": f"Capital {i}", "ru": f"Столица {i}", "de": f"Hauptstadt {i}"},
            official_language={"en": f"Language {i}", "ru": f"Язык {i}", "de": f"Sprache {i}"},
            population=1_000_000 + i,
            population_display={"en": f"{i} M", "ru": f"{i} млн", "de": f"{i} Mio"},
            currency_name={"en": f"Currency {i}", "ru": f"Валюта {i}", "de": f"Wahrung {i}"},
            currency_code=f"X{i:02d}",
            flag_file=f"c{i:02d}.svg",
        )
        for i in range(1, total + 1)
    ]
    return CountryStore(countries=countries, flags_dir=Path("data/flags"))


def _keyboard_texts(markup: InlineKeyboardMarkup) -> list[str]:
    return [button.text for row in markup.inline_keyboard for button in row]


async def test_start_quiz_setup_initializes_state_and_renders_setup() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    state = _build_state()
    i18n = I18nService()

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()

        await quiz_handlers.start_quiz_setup(callback, state, session, i18n)
        data = await state.get_data()

    await engine.dispose()

    assert await state.get_state() == QuizStates.setup.state
    assert data["selected_count"] == 10
    assert data["selected_mode"] == QuizMode.MIXED.value
    assert data["selected_categories"] == ["flag"]
    callback.message.answer.assert_awaited()
    callback.answer.assert_awaited()


async def test_cancel_setup_clears_state_and_returns_to_main_menu() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    state = _build_state()
    i18n = I18nService()

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()
        await state.set_state(QuizStates.setup)
        await state.update_data(selected_count=25)

        await quiz_handlers.cancel_setup(callback, state, session, i18n)

    await engine.dispose()

    assert await state.get_state() is None
    assert await state.get_data() == {}
    callback.message.edit_text.assert_awaited()
    rendered_text = callback.message.edit_text.await_args.args[0]
    assert rendered_text == "Quiz setup cancelled."
    callback.answer.assert_awaited()


async def test_admin_catalog_dashboard_callback_renders_dashboard(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "admin:catalog_dashboard"
    i18n = I18nService()
    settings = Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path="data/normalized/countries.json",
        flags_dir="data/flags",
        quiz_autonext_seconds=1.2,
        admin_ids_raw="42",
    )

    class FakeCatalogService:
        def __init__(self, session, settings):
            self.session = session
            self.settings = settings

        async def dashboard(self) -> AdminCatalogDashboard:
            return AdminCatalogDashboard(
                validation=DatasetValidationReport(
                    is_valid=True,
                    countries_count=193,
                    first_country_code="AFG",
                    last_country_code="ZWE",
                ),
                health=CatalogHealthReport(
                    dataset_count=193,
                    db_count=190,
                    missing_in_db=["ARG"],
                    stale_in_db=["OLD"],
                    missing_flag_files=[],
                ),
                preview=CatalogSyncPreview(
                    dataset_count=193,
                    db_count=190,
                    to_create=["ARG"],
                    to_update=[],
                    to_delete=["OLD"],
                ),
            )

    monkeypatch.setattr(menu_handlers, "AdminCatalogService", FakeCatalogService)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()

        await menu_handlers.admin_actions(callback, session, settings, i18n)

    await engine.dispose()

    callback.message.edit_text.assert_awaited()
    rendered_text = callback.message.edit_text.await_args.args[0]
    assert "Catalog status" in rendered_text
    assert "Pending sync: <b>yes</b>" in rendered_text
    callback.answer.assert_awaited()


async def test_admin_sync_prepare_no_changes_returns_to_admin_keyboard(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "admin:sync_prepare"
    i18n = I18nService()
    settings = Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path="data/normalized/countries.json",
        flags_dir="data/flags",
        quiz_autonext_seconds=1.2,
        admin_ids_raw="42",
    )

    class FakeCatalogService:
        def __init__(self, session, settings):
            self.session = session
            self.settings = settings

        async def sync_preview(self) -> CatalogSyncPreview:
            return CatalogSyncPreview(
                dataset_count=193,
                db_count=193,
                to_create=[],
                to_update=[],
                to_delete=[],
            )

    monkeypatch.setattr(menu_handlers, "AdminCatalogService", FakeCatalogService)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()

        await menu_handlers.admin_actions(callback, session, settings, i18n)

    await engine.dispose()

    callback.message.edit_text.assert_awaited()
    rendered_text = callback.message.edit_text.await_args.args[0]
    assert "No sync needed" in rendered_text
    callback.answer.assert_awaited()


async def test_exit_yes_sends_abandoned_quiz_message() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    state = _build_state()
    i18n = I18nService()

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()
        await state.set_state(QuizStates.exit_confirm)

        await quiz_handlers.exit_yes(callback, state, session, i18n)

    await engine.dispose()

    assert await state.get_state() is None
    callback.message.answer.assert_awaited()
    rendered_text = callback.message.answer.await_args.args[0]
    assert rendered_text == "Quiz ended early."
    callback.answer.assert_awaited()


async def test_show_menu_renders_buttons_without_visible_title() -> None:
    callback = _build_callback()
    i18n = I18nService()

    await menu_handlers._show_menu(callback, SupportedLanguage.EN, i18n)

    callback.message.edit_text.assert_awaited_once()
    assert callback.message.edit_text.await_args.args[0] == menu_handlers.MENU_SCREEN_TEXT
    callback.answer.assert_awaited_once()


async def test_stats_review_setup_preconfigures_review_mode(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "stats:review_setup"
    state = _build_state()
    i18n = I18nService()
    render_setup = AsyncMock()

    class FakeQuizRunRepository:
        def __init__(self, session) -> None:
            self.session = session

        async def get_user_summary(self, user_id: int) -> UserStatsSummary:
            return UserStatsSummary(
                quizzes_started=5,
                quizzes_completed=4,
                due_countries=12,
                category_breakdown=[
                    CategoryProgressStat(category=QuizCategory.FLAG, due_items=4),
                    CategoryProgressStat(category=QuizCategory.CAPITAL, due_items=8),
                    CategoryProgressStat(category=QuizCategory.LANGUAGE, due_items=0),
                ],
            )

    monkeypatch.setattr(menu_handlers, "QuizRunRepository", FakeQuizRunRepository)
    monkeypatch.setattr(menu_handlers, "render_quiz_setup", render_setup)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()

        await menu_handlers.stats_review_setup(callback, state, session, i18n)

        data = await state.get_data()

    await engine.dispose()

    assert await state.get_state() == QuizStates.setup.state
    assert data["selected_count"] == 10
    assert data["selected_mode"] == menu_handlers.QuizMode.REVIEW.value
    assert data["selected_categories"] == ["flag", "capital"]
    render_setup.assert_awaited_once()
    assert render_setup.await_args.kwargs["edit_existing"] is False


async def test_begin_quiz_starts_review_mode_when_due_countries_are_available() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    bot = _build_bot()
    state = _build_state()
    i18n = I18nService()
    country_store = _build_country_store(12)
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        progress_repo = LearningProgressRepository(session)

        for index, country in enumerate(country_store.countries[:10], start=1):
            question = Question(
                id=f"{country.code}:capital",
                country_code=country.code,
                category=QuizCategory.CAPITAL,
                prompt=f"Capital of {country.name(SupportedLanguage.EN)}?",
                options=[
                    country.capital_name(SupportedLanguage.EN),
                    "Wrong 1",
                    "Wrong 2",
                    "Wrong 3",
                ],
                correct_option=country.capital_name(SupportedLanguage.EN),
                answer_context=country.capital_name(SupportedLanguage.EN),
            )
            progress = await progress_repo.record_result(
                user_id=user.id,
                question=question,
                outcome=QuizAnswerOutcome.SKIPPED,
                wrong_attempts=0,
            )
            progress.next_review_at = now - timedelta(hours=index)

        await session.commit()
        await state.set_state(QuizStates.setup)
        await state.update_data(
            selected_count=10,
            selected_mode=QuizMode.REVIEW.value,
            selected_categories=[QuizCategory.CAPITAL.value],
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.begin_quiz(callback, bot, state, session, i18n, country_store)
        data = await state.get_data()

    await engine.dispose()

    assert await state.get_state() == QuizStates.in_progress.state
    assert data["selected_categories"] == ["capital"]
    assert data["quiz_session"].total_questions == 10
    callback.message.edit_text.assert_awaited()
    assert callback.message.answer.await_count == 2
    assert callback.message.answer.await_args_list[0].args[0] == quiz_handlers.QUIZ_SPACER_TEXT
    rendered_question = callback.message.answer.await_args.args[0]
    assert "What is the capital of" in rendered_question
    callback.answer.assert_awaited()
    bot.send_photo.assert_not_called()


async def test_begin_quiz_review_mode_shows_alert_when_due_countries_are_missing() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    bot = _build_bot()
    state = _build_state()
    i18n = I18nService()
    country_store = _build_country_store(12)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()
        await state.set_state(QuizStates.setup)
        await state.update_data(
            selected_count=10,
            selected_mode=QuizMode.REVIEW.value,
            selected_categories=[QuizCategory.CAPITAL.value],
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.begin_quiz(callback, bot, state, session, i18n, country_store)

    await engine.dispose()

    assert await state.get_state() == QuizStates.setup.state
    callback.answer.assert_awaited()
    assert callback.answer.await_args.kwargs["show_alert"] is True
    assert "There are not enough cards due for review" in callback.answer.await_args.args[0]
    callback.message.answer.assert_not_awaited()


async def test_show_question_uses_document_for_svg_flags(tmp_path: Path) -> None:
    callback = _build_callback()
    bot = _build_bot()
    callback.bot = bot
    state = _build_state()
    i18n = I18nService()
    svg_path = tmp_path / "de.svg"
    svg_path.write_text("<svg />", encoding="utf-8")
    question = Question(
        id="DEU:flag",
        country_code="DEU",
        category=QuizCategory.FLAG,
        prompt="Which country does this flag belong to?",
        options=["Germany", "France", "Italy", "Belgium"],
        correct_option="Germany",
        answer_context="Germany",
        flag_path=svg_path,
    )
    session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG],
        questions=deque([question]),
        total_questions=10,
    )

    await quiz_handlers._show_question(bot, callback, state, session, i18n)

    bot.send_document.assert_awaited()
    bot.send_photo.assert_not_called()
    callback.message.answer.assert_not_awaited()


async def test_show_question_prefers_png_preview_when_available(tmp_path: Path) -> None:
    callback = _build_callback()
    bot = _build_bot()
    callback.bot = bot
    state = _build_state()
    i18n = I18nService()
    svg_path = tmp_path / "de.svg"
    png_path = tmp_path / "de.png"
    svg_path.write_text("<svg />", encoding="utf-8")
    png_path.write_bytes(b"png")
    question = Question(
        id="DEU:flag",
        country_code="DEU",
        category=QuizCategory.FLAG,
        prompt="Which country does this flag belong to?",
        options=["Germany", "France", "Italy", "Belgium"],
        correct_option="Germany",
        answer_context="Germany",
        flag_path=svg_path,
    )
    session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG],
        questions=deque([question]),
        total_questions=10,
    )

    await quiz_handlers._show_question(bot, callback, state, session, i18n)

    bot.send_photo.assert_awaited()
    bot.send_document.assert_not_called()


async def test_continue_learning_restores_last_quiz_setup() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "menu:continue_learning"
    state = _build_state()
    i18n = I18nService()

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        progress_repo = LearningProgressRepository(session)
        question = Question(
            id="C01:capital",
            country_code="C01",
            category=QuizCategory.CAPITAL,
            prompt="Capital?",
            options=["Capital 1", "Wrong 1", "Wrong 2", "Wrong 3"],
            correct_option="Capital 1",
            answer_context="Capital 1",
        )
        progress = await progress_repo.record_result(
            user_id=user.id,
            question=question,
            outcome=QuizAnswerOutcome.SKIPPED,
            wrong_attempts=0,
        )
        progress.next_review_at = datetime.now(UTC) - timedelta(hours=1)

        quiz_run = await quiz_handlers.QuizRunRepository(session).create_run(
            user_id=user.id,
            language=SupportedLanguage.EN,
            countries_count=10,
            categories=[QuizCategory.CAPITAL],
            total_questions=10,
        )
        await quiz_handlers.QuizRunRepository(session).finish_run(
            quiz_run_id=quiz_run.id,
            status=QuizRunStatus.COMPLETED,
            resolved_questions=1,
            correct_answers=0,
            skipped_answers=1,
            wrong_attempts=0,
        )
        await session.commit()

        await menu_handlers.continue_learning(callback, state, session, i18n)
        data = await state.get_data()

    await engine.dispose()

    assert await state.get_state() == QuizStates.setup.state
    assert data["selected_count"] == 10
    assert data["selected_categories"] == ["capital"]
    assert data["selected_mode"] == QuizMode.MIXED.value
    callback.message.answer.assert_awaited()
    rendered_text = callback.message.answer.await_args.args[0]
    assert "Quiz setup" in rendered_text
    assert "Capital" in rendered_text
    callback.answer.assert_awaited()
    assert callback.answer.await_args.args[0] == "Your recent quiz setup has been restored."


async def test_continue_learning_shows_alert_without_history() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "menu:continue_learning"
    state = _build_state()
    i18n = I18nService()

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()

        await menu_handlers.continue_learning(callback, state, session, i18n)

    await engine.dispose()

    assert await state.get_state() is None
    callback.answer.assert_awaited()
    assert callback.answer.await_args.kwargs["show_alert"] is True
    assert "There is no previous quiz setup to restore yet." in callback.answer.await_args.args[0]


async def test_answer_feedback_keyboard_hides_correct_option_until_revealed() -> None:
    markup = answer_feedback_keyboard(
        ["Peru", "Ghana", "Bulgaria", "Mali"],
        0,
        2,
        reveal_correct=False,
        exit_text="Exit",
    )

    assert _keyboard_texts(markup) == ["❌ Peru", "Ghana", "Bulgaria", "Mali", "Exit"]
    assert markup.inline_keyboard[-1][0].callback_data == "answer:locked"


async def test_answer_feedback_keyboard_reveals_correct_option_for_success() -> None:
    markup = answer_feedback_keyboard(
        ["Peru", "Ghana", "Bulgaria", "Mali"],
        2,
        2,
        exit_text="Exit",
    )

    assert _keyboard_texts(markup) == ["Peru", "Ghana", "✅ Bulgaria", "Mali", "Exit"]


async def test_show_question_completion_message_omits_menu_hint_and_skipped_count() -> None:
    callback = _build_callback()
    bot = _build_bot()
    state = _build_state()
    i18n = I18nService()
    session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG],
        questions=deque(),
        total_questions=10,
        resolved_questions=10,
        correct_answers=1,
        mistakes=9,
    )
    await state.update_data(language=SupportedLanguage.EN.value)

    await quiz_handlers._show_question(bot, callback, state, session, i18n)

    callback.message.answer.assert_awaited_once()
    rendered = callback.message.answer.await_args.args[0]
    assert "Questions: <b>10</b>" in rendered
    assert "Correct: <b>1</b>" in rendered
    assert "Mistakes: <b>9</b>" in rendered
    assert "Skipped" not in rendered
    assert "main menu" not in rendered.lower()


async def test_wrong_answer_automatically_reveals_correct_option_and_advances() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "answer:0"
    bot = _build_bot()
    callback.bot = bot
    state = _build_state()
    i18n = I18nService()
    settings = Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path="data/normalized/countries.json",
        flags_dir="data/flags",
        quiz_autonext_seconds=0,
        admin_ids_raw="42",
    )
    current_question = Question(
        id="BGR:flag",
        country_code="BGR",
        category=QuizCategory.FLAG,
        prompt="Which country is this?",
        options=["Peru", "Ghana", "Bulgaria", "Mali"],
        option_labels=["Peru", "Ghana", "Bulgaria", "Mali"],
        correct_option="Bulgaria",
        answer_context="Bulgaria",
    )
    next_question = Question(
        id="GHA:flag",
        country_code="GHA",
        category=QuizCategory.FLAG,
        prompt="Which country is this?",
        options=["Ukraine", "Ghana", "Tanzania", "Moldova"],
        option_labels=["Ukraine", "Ghana", "Tanzania", "Moldova"],
        correct_option="Ghana",
        answer_context="Ghana",
    )
    quiz_session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG],
        questions=deque([current_question, next_question]),
        total_questions=2,
    )

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        quiz_run = await quiz_handlers.QuizRunRepository(session).create_run(
            user_id=user.id,
            language=SupportedLanguage.EN,
            countries_count=2,
            categories=[QuizCategory.FLAG],
            total_questions=2,
        )
        await session.commit()
        await state.set_state(QuizStates.in_progress)
        await state.update_data(
            language=SupportedLanguage.EN.value,
            quiz_session=quiz_session,
            quiz_run_id=quiz_run.id,
            user_id=user.id,
        )

        await quiz_handlers.answer_question(callback, bot, state, session, settings, i18n)
        data = await state.get_data()
        await session.commit()

    assert callback.message.edit_reply_markup.await_count == 2
    first_markup = callback.message.edit_reply_markup.await_args_list[0].kwargs["reply_markup"]
    second_markup = callback.message.edit_reply_markup.await_args_list[1].kwargs["reply_markup"]
    assert _keyboard_texts(first_markup) == ["❌ Peru", "Ghana", "Bulgaria", "Mali", "Exit"]
    assert _keyboard_texts(second_markup) == ["❌ Peru", "Ghana", "✅ Bulgaria", "Mali", "Exit"]
    callback.message.answer.assert_awaited_once()
    rendered_question = callback.message.answer.await_args.args[0]
    assert rendered_question.startswith("Which country is this?")
    assert data["quiz_session"].resolved_questions == 1
    assert data["quiz_session"].mistakes == 1
    assert data["quiz_session"].current_question().id == next_question.id

    async with session_factory() as session:
        saved_answer = (
            await session.execute(
                select(QuizAnswer).where(
                    QuizAnswer.question_id == current_question.id,
                )
            )
        ).scalar_one()
        assert saved_answer.outcome == QuizAnswerOutcome.INCORRECT.value
        assert saved_answer.wrong_attempts == 1

        progress = (
            await session.execute(
                select(UserLearningProgress).where(
                    UserLearningProgress.user_id == user.id,
                    UserLearningProgress.country_code == "BGR",
                    UserLearningProgress.category == QuizCategory.FLAG.value,
                )
            )
        ).scalar_one()
        assert progress.skipped_answers == 0
        assert progress.wrong_attempts == 1

    await engine.dispose()


async def test_wrong_answer_on_last_question_completes_quiz_after_auto_reveal() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "answer:0"
    bot = _build_bot()
    callback.bot = bot
    state = _build_state()
    i18n = I18nService()
    settings = Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path="data/normalized/countries.json",
        flags_dir="data/flags",
        quiz_autonext_seconds=0,
        admin_ids_raw="42",
    )
    question = Question(
        id="BGR:flag",
        country_code="BGR",
        category=QuizCategory.FLAG,
        prompt="Which country is this?",
        options=["Peru", "Ghana", "Bulgaria", "Mali"],
        option_labels=["Peru", "Ghana", "Bulgaria", "Mali"],
        correct_option="Bulgaria",
        answer_context="Bulgaria",
    )
    quiz_session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG],
        questions=deque([question]),
        total_questions=1,
    )

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        quiz_run = await quiz_handlers.QuizRunRepository(session).create_run(
            user_id=user.id,
            language=SupportedLanguage.EN,
            countries_count=1,
            categories=[QuizCategory.FLAG],
            total_questions=1,
        )
        await session.commit()
        await state.set_state(QuizStates.in_progress)
        await state.update_data(
            language=SupportedLanguage.EN.value,
            quiz_session=quiz_session,
            quiz_run_id=quiz_run.id,
            user_id=user.id,
        )

        await quiz_handlers.answer_question(callback, bot, state, session, settings, i18n)

    assert callback.message.edit_reply_markup.await_count == 2
    first_markup = callback.message.edit_reply_markup.await_args_list[0].kwargs["reply_markup"]
    second_markup = callback.message.edit_reply_markup.await_args_list[1].kwargs["reply_markup"]
    assert _keyboard_texts(first_markup) == ["❌ Peru", "Ghana", "Bulgaria", "Mali", "Exit"]
    assert _keyboard_texts(second_markup) == ["❌ Peru", "Ghana", "✅ Bulgaria", "Mali", "Exit"]
    callback.message.answer.assert_awaited_once()
    rendered = callback.message.answer.await_args.args[0]
    assert "Quiz complete" in rendered
    assert "Questions: <b>1</b>" in rendered
    assert "Correct: <b>0</b>" in rendered
    assert "Mistakes: <b>1</b>" in rendered
    assert await state.get_state() is None

    await engine.dispose()


def test_quiz_option_label_shortens_long_flag_country_names() -> None:
    assert (
        quiz_option_label("Central African Republic", QuizCategory.FLAG, SupportedLanguage.EN)
        == "CAR"
    )
    assert (
        quiz_option_label("Сейшельские Острова", QuizCategory.FLAG, SupportedLanguage.RU)
        == "Сейшелы"
    )
    assert (
        quiz_option_label("Marshall Islands", QuizCategory.CAPITAL, SupportedLanguage.EN)
        == "Marshall Islands"
    )
