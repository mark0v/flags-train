from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bot.handlers import menu as menu_handlers
from app.bot.handlers import quiz as quiz_handlers
from app.bot.states import QuizStates
from app.config import Settings
from app.constants import QuizMode, SupportedLanguage
from app.db.base import Base
from app.repositories.users import UserRepository
from app.services.admin_catalog import AdminCatalogDashboard
from app.services.catalog_health import CatalogHealthReport
from app.services.catalog_sync_preview import CatalogSyncPreview
from app.services.dataset_validation import DatasetValidationReport
from app.services.i18n import I18nService


def _build_callback(user_id: int = 42, username: str = "tester", first_name: str = "Test"):
    message = SimpleNamespace(
        edit_text=AsyncMock(),
        answer=AsyncMock(),
        edit_reply_markup=AsyncMock(),
    )
    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=user_id, username=username, first_name=first_name),
        message=message,
        answer=AsyncMock(),
        data="",
    )
    return callback


def _build_state() -> FSMContext:
    storage = MemoryStorage()
    return FSMContext(storage=storage, key=StorageKey(bot_id=1, chat_id=1, user_id=42))


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
    callback.message.edit_text.assert_awaited()
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
