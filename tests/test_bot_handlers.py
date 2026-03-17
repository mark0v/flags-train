from collections import deque
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
from app.bot.keyboards.common import answer_feedback_keyboard, quiz_setup_keyboard
from app.bot.states import QuizStates
from app.config import Settings
from app.constants import QuizAnswerOutcome, QuizCategory, SupportedLanguage
from app.db.base import Base
from app.db.models import QuizAnswer, UserLearningProgress
from app.repositories.users import UserRepository
from app.services.admin_catalog import AdminCatalogDashboard
from app.services.catalog_health import CatalogHealthReport
from app.services.catalog_sync_preview import CatalogSyncPreview
from app.services.country_store import Country, CountryStore
from app.services.dataset_validation import DatasetValidationReport
from app.services.i18n import I18nService
from app.services.quiz.engine import Question
from app.services.quiz_display import quiz_option_label


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


def _build_settings(autonext_seconds: float = 0) -> Settings:
    return Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path="data/normalized/countries.json",
        flags_dir="data/flags",
        quiz_autonext_seconds=autonext_seconds,
        admin_ids_raw="42",
    )


def _build_state() -> FSMContext:
    storage = MemoryStorage()
    return FSMContext(storage=storage, key=StorageKey(bot_id=1, chat_id=1, user_id=42))


def _build_country_store(total: int = 12) -> CountryStore:
    countries = [
        Country(
            code=f"C{i:02d}",
            localized_name={"en": f"Country {i}", "ru": f"Ð¡Ñ‚Ñ€Ð°Ð½Ð° {i}", "de": f"Land {i}"},
            capital={"en": f"Capital {i}", "ru": f"Ð¡Ñ‚Ð¾Ð»Ð¸Ñ†Ð° {i}", "de": f"Hauptstadt {i}"},
            official_language={"en": f"Language {i}", "ru": f"Ð¯Ð·Ñ‹Ðº {i}", "de": f"Sprache {i}"},
            population=1_000_000 + i,
            population_display={"en": f"{i} M", "ru": f"{i} Ð¼Ð»Ð½", "de": f"{i} Mio"},
            currency_name={"en": f"Currency {i}", "ru": f"Ð’Ð°Ð»ÑŽÑ‚Ð° {i}", "de": f"Wahrung {i}"},
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
    assert data["selected_categories"] == ["flag"]
    callback.message.answer.assert_awaited()
    callback.answer.assert_awaited()


async def test_begin_quiz_uses_selected_count_as_total_questions() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    bot = _build_bot()
    state = _build_state()
    i18n = I18nService()
    country_store = _build_country_store(20)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()
        await state.set_state(QuizStates.setup)
        await state.update_data(
            selected_count=20,
            selected_categories=[QuizCategory.FLAG.value, QuizCategory.CAPITAL.value],
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.begin_quiz(callback, bot, state, session, i18n, country_store)
        data = await state.get_data()

    await engine.dispose()

    assert await state.get_state() == QuizStates.in_progress.state
    assert data["quiz_session"].countries_count == 10
    assert data["quiz_session"].total_questions == 20


async def test_begin_quiz_excludes_hidden_countries() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    bot = _build_bot()
    state = _build_state()
    i18n = I18nService()
    country_store = _build_country_store(40)

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        hidden_repo = quiz_handlers.HiddenCountriesRepository(session)
        await hidden_repo.hide_country(
            user.id,
            "C01",
            total_country_count=len(country_store.countries),
            min_available_countries=30,
        )
        await session.commit()
        await state.set_state(QuizStates.setup)
        await state.update_data(
            selected_count=10,
            selected_categories=[QuizCategory.FLAG.value],
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.begin_quiz(callback, bot, state, session, i18n, country_store)
        data = await state.get_data()

    await engine.dispose()

    country_codes = [question.country_code for question in data["quiz_session"].questions]
    assert "C01" not in country_codes


def test_quiz_setup_keyboard_hides_non_core_categories() -> None:
    markup = quiz_setup_keyboard(
        SupportedLanguage.EN,
        I18nService(),
        10,
        [QuizCategory.FLAG],
    )

    texts = _keyboard_texts(markup)
    assert any(text.endswith("Flag") for text in texts)
    assert "Capital" in texts
    assert "Language" not in texts
    assert "Population" not in texts
    assert "Currency" not in texts
    assert "Mixed" not in texts
    assert "Review" not in texts
    assert "New" not in texts


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
        await state.update_data(selected_count=20)

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


async def test_answer_feedback_keyboard_hides_correct_option_until_revealed() -> None:
    markup = answer_feedback_keyboard(
        ["Peru", "Ghana", "Bulgaria", "Mali"],
        0,
        2,
        reveal_correct=False,
        hide_country_text="Don't repeat this country",
        exit_text="Exit",
    )

    texts = _keyboard_texts(markup)
    assert texts[-1] == "Exit"
    assert texts[-2] == "Don't repeat this country"
    assert texts[0].endswith("Peru")
    assert texts[1:4] == ["Ghana", "Bulgaria", "Mali"]
    assert markup.inline_keyboard[-1][0].callback_data == "answer:locked"


async def test_answer_feedback_keyboard_reveals_correct_option_for_success() -> None:
    markup = answer_feedback_keyboard(
        ["Peru", "Ghana", "Bulgaria", "Mali"],
        2,
        2,
        hide_country_text="Don't repeat this country",
        exit_text="Exit",
    )

    texts = _keyboard_texts(markup)
    assert texts[:2] == ["Peru", "Ghana"]
    assert texts[2].endswith("Bulgaria")
    assert texts[3:] == ["Mali", "Don't repeat this country", "Exit"]


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
    settings = _build_settings()
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

    first_markup = callback.message.edit_reply_markup.await_args_list[0].kwargs["reply_markup"]
    second_markup = callback.message.edit_reply_markup.await_args_list[1].kwargs["reply_markup"]
    first_texts = _keyboard_texts(first_markup)
    second_texts = _keyboard_texts(second_markup)
    assert first_texts[-1] == "Exit"
    assert first_texts[-2] == "Don't repeat this country"
    assert first_texts[0].endswith("Peru")
    assert first_texts[1:4] == ["Ghana", "Bulgaria", "Mali"]
    assert second_texts[-1] == "Exit"
    assert second_texts[-2] == "Don't repeat this country"
    assert second_texts[0].endswith("Peru")
    assert second_texts[1] == "Ghana"
    assert second_texts[2].endswith("Bulgaria")
    assert second_texts[3] == "Mali"
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
    settings = _build_settings()
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

    first_markup = callback.message.edit_reply_markup.await_args_list[0].kwargs["reply_markup"]
    second_markup = callback.message.edit_reply_markup.await_args_list[1].kwargs["reply_markup"]
    first_texts = _keyboard_texts(first_markup)
    second_texts = _keyboard_texts(second_markup)
    assert first_texts[-1] == "Exit"
    assert first_texts[-2] == "Don't repeat this country"
    assert first_texts[0].endswith("Peru")
    assert first_texts[1:4] == ["Ghana", "Bulgaria", "Mali"]
    assert second_texts[-1] == "Exit"
    assert second_texts[-2] == "Don't repeat this country"
    assert second_texts[0].endswith("Peru")
    assert second_texts[1] == "Ghana"
    assert second_texts[2].endswith("Bulgaria")
    assert second_texts[3] == "Mali"
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
        quiz_option_label("United Arab Emirates", QuizCategory.FLAG, SupportedLanguage.EN) == "UAE"
    )
    assert (
        quiz_option_label("Marshall Islands", QuizCategory.CAPITAL, SupportedLanguage.EN)
        == "Marshall Islands"
    )


async def test_start_quiz_setup_keeps_previous_stats_message_in_chat() -> None:
    callback = _build_callback()
    bot = _build_bot()
    callback.bot = bot
    state = _build_state()
    i18n = I18nService()
    completed_session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG],
        questions=deque(),
        total_questions=10,
        resolved_questions=10,
        correct_answers=7,
        mistakes=3,
    )
    await state.update_data(language=SupportedLanguage.EN.value)

    await quiz_handlers._show_question(bot, callback, state, completed_session, i18n)

    completion_calls = callback.message.answer.await_count
    completion_message = callback.message.answer.await_args_list[-1].args[0]
    assert "Quiz complete" in completion_message

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        await session.commit()

        await quiz_handlers.start_quiz_setup(callback, state, session, i18n)

    await engine.dispose()

    assert callback.message.answer.await_count == completion_calls + 1
    callback.message.edit_text.assert_not_awaited()


async def test_hide_country_removes_future_questions_from_current_session() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "quiz:hide_country"
    state = _build_state()
    i18n = I18nService()
    country_store = _build_country_store(40)
    quiz_session = quiz_handlers.QuizSession(
        language=SupportedLanguage.EN,
        countries_count=10,
        categories=[QuizCategory.FLAG, QuizCategory.CAPITAL],
        questions=deque(
            [
                Question(
                    id="UKR:capital",
                    country_code="UKR",
                    category=QuizCategory.CAPITAL,
                    prompt="Capital?",
                    options=["Kyiv", "Paris", "Rome", "Madrid"],
                    correct_option="Kyiv",
                    answer_context="Kyiv",
                ),
                Question(
                    id="UKR:flag",
                    country_code="UKR",
                    category=QuizCategory.FLAG,
                    prompt="Flag?",
                    options=["Ukraine", "France", "Italy", "Spain"],
                    correct_option="Ukraine",
                    answer_context="Ukraine",
                ),
                Question(
                    id="DEU:flag",
                    country_code="DEU",
                    category=QuizCategory.FLAG,
                    prompt="Flag?",
                    options=["Germany", "France", "Italy", "Spain"],
                    correct_option="Germany",
                    answer_context="Germany",
                ),
            ]
        ),
        total_questions=3,
    )

    async with session_factory() as session:
        user = await UserRepository(session).get_or_create(42, "tester", "Test")
        user.language = SupportedLanguage.EN.value
        quiz_run = await quiz_handlers.QuizRunRepository(session).create_run(
            user_id=user.id,
            language=SupportedLanguage.EN,
            countries_count=10,
            categories=[QuizCategory.FLAG, QuizCategory.CAPITAL],
            total_questions=3,
        )
        await session.commit()
        await state.set_state(QuizStates.in_progress)
        await state.update_data(
            quiz_session=quiz_session,
            quiz_run_id=quiz_run.id,
            user_id=user.id,
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.hide_country(
            callback,
            state,
            session,
            i18n,
            country_store,
        )
        data = await state.get_data()
        await session.commit()
        saved_answers = (
            await session.execute(
                select(QuizAnswer).where(
                    QuizAnswer.question_id == "UKR:capital",
                )
            )
        ).scalars().all()
        assert saved_answers == []

        progress = (
            await session.execute(
                select(UserLearningProgress).where(
                    UserLearningProgress.user_id == user.id,
                    UserLearningProgress.country_code == "UKR",
                    UserLearningProgress.category == QuizCategory.CAPITAL.value,
                )
            )
        ).scalars().all()
        assert progress == []

    await engine.dispose()

    assert data["quiz_session"].total_questions == 3
    assert data["quiz_session"].resolved_questions == 0
    assert data["quiz_session"].skipped_answers == 0
    assert [question.country_code for question in data["quiz_session"].questions] == [
        "UKR",
        "UKR",
        "DEU",
    ]
    locked_markup = callback.message.edit_reply_markup.await_args.kwargs["reply_markup"]
    assert _keyboard_texts(locked_markup)[-2] == "Don't repeat this country"
    assert locked_markup.inline_keyboard[-1][0].callback_data == "answer:locked"
    callback.answer.assert_awaited_once()
    assert callback.answer.await_args.args[0] == "Country hidden."


async def test_hide_country_shows_limit_alert_when_only_thirty_countries_would_remain() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.data = "quiz:hide_country"
    state = _build_state()
    i18n = I18nService()
    country_store = _build_country_store(30)

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
            quiz_session=quiz_handlers.QuizSession(
                language=SupportedLanguage.EN,
                countries_count=1,
                categories=[QuizCategory.FLAG],
                questions=deque(
                    [
                        Question(
                            id="UKR:flag",
                            country_code="UKR",
                            category=QuizCategory.FLAG,
                            prompt="Flag?",
                            options=["Ukraine", "France", "Italy", "Spain"],
                            correct_option="Ukraine",
                            answer_context="Ukraine",
                        )
                    ]
                ),
                total_questions=1,
            ),
            quiz_run_id=quiz_run.id,
            user_id=user.id,
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.hide_country(
            callback,
            state,
            session,
            i18n,
            country_store,
        )

    await engine.dispose()

    callback.answer.assert_awaited_once()
    assert callback.answer.await_args.kwargs["show_alert"] is True
    assert callback.answer.await_args.args[0] == "At least 30 countries must remain."


async def test_settings_shows_hidden_country_count_and_resets_it() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    callback = _build_callback()
    callback.bot = _build_bot()
    i18n = I18nService()
    country_store = _build_country_store(40)

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
        state = _build_state()
        await state.set_state(QuizStates.in_progress)
        await state.update_data(
            quiz_session=quiz_handlers.QuizSession(
                language=SupportedLanguage.EN,
                countries_count=1,
                categories=[QuizCategory.FLAG],
                questions=deque(
                    [
                        Question(
                            id="UKR:flag",
                            country_code="UKR",
                            category=QuizCategory.FLAG,
                            prompt="Flag?",
                            options=["Ukraine", "France", "Italy", "Spain"],
                            correct_option="Ukraine",
                            answer_context="Ukraine",
                        )
                    ]
                ),
                total_questions=1,
            ),
            quiz_run_id=quiz_run.id,
            user_id=user.id,
            language=SupportedLanguage.EN.value,
        )

        await quiz_handlers.hide_country(
            callback,
            state,
            session,
            i18n,
            country_store,
        )

        callback.message.edit_text.reset_mock()
        callback.answer.reset_mock()
        await menu_handlers.settings(callback, session, i18n)
        settings_text = callback.message.edit_text.await_args.args[0]

        callback.message.edit_text.reset_mock()
        callback.answer.reset_mock()
        await menu_handlers.reset_hidden_countries(callback, session, i18n)

    await engine.dispose()

    assert "Hidden countries: <b>1</b>" in settings_text
    reset_text = callback.message.edit_text.await_args.args[0]
    assert "Hidden countries: <b>0</b>" in reset_text
    assert callback.answer.await_args.args[0] == "Reset: 1"
