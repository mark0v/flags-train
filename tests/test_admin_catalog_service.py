from datetime import UTC
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import CountryCatalog
from app.repositories.countries import CountryCatalogRepository
from app.services.admin_catalog import AdminCatalogService
from app.services.country_store import CountryStore


def _settings(tmp_path: Path) -> Settings:
    flags_dir = tmp_path / "flags"
    flags_dir.mkdir()
    for flag in ["de.svg", "es.svg", "fr.svg", "it.svg", "pl.svg", "ua.svg"]:
        (flags_dir / flag).write_text("<svg />", encoding="utf-8")

    return Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path=Path("tests/fixtures/countries.json"),
        flags_dir=flags_dir,
        quiz_autonext_seconds=1.2,
        admin_ids_raw="",
    )


async def test_admin_catalog_service_reports_validation_health_preview_and_sync(
    tmp_path: Path,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = _settings(tmp_path)

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        store = CountryStore.from_path(
            Path("tests/fixtures/countries.json"),
            Path("tests/fixtures"),
        )
        await repository.upsert_many(store.countries[:2])
        await session.commit()

        service = AdminCatalogService(session, settings)
        validation = await service.dataset_validation()
        health = await service.catalog_health()
        preview = await service.sync_preview()
        sync_result = await service.apply_sync()

    await engine.dispose()

    assert validation.is_valid is True
    assert health.dataset_count == 6
    assert sorted(health.missing_in_db) == ["ESP", "ITA", "POL", "UKR"]
    assert preview.to_create == ["ESP", "ITA", "POL", "UKR"]
    assert preview.to_update == []
    assert preview.to_delete == []
    assert sync_result.synced_count == 6
    assert sync_result.preview.to_create == ["ESP", "ITA", "POL", "UKR"]


async def test_admin_catalog_service_preview_detects_updates_and_deletes(tmp_path: Path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = _settings(tmp_path)

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        store = CountryStore.from_path(
            Path("tests/fixtures/countries.json"),
            Path("tests/fixtures"),
        )
        await repository.upsert_many(store.countries[:1])
        existing = (await repository.list_countries())[0]
        existing.population = 1

        session.add(
            CountryCatalog(
                code="ZZZ",
                localized_name={"ru": "Старое", "en": "Old", "de": "Alt"},
                capital={"ru": "Старое", "en": "Old", "de": "Alt"},
                official_language={"ru": "Старое", "en": "Old", "de": "Alt"},
                population=1,
                population_display={"ru": "1", "en": "1", "de": "1"},
                currency_name={"ru": "Старое", "en": "Old", "de": "Alt"},
                currency_code="OLD",
                flag_file="old.svg",
            )
        )
        await session.commit()

        service = AdminCatalogService(session, settings)
        preview = await service.sync_preview()

    await engine.dispose()

    assert preview.to_update == ["DEU"]
    assert preview.to_delete == ["ZZZ"]


async def test_admin_catalog_service_apply_sync_is_noop_when_catalog_is_current(
    tmp_path: Path,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = _settings(tmp_path)

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        store = CountryStore.from_path(
            Path("tests/fixtures/countries.json"),
            settings.flags_dir,
        )
        await repository.upsert_many(store.countries)
        await session.commit()

        service = AdminCatalogService(session, settings)
        result = await service.apply_sync()

    await engine.dispose()

    assert result.synced_count == 6
    assert result.preview.has_changes is False


async def test_admin_catalog_service_sync_preview_requires_valid_dataset(tmp_path: Path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path=tmp_path / "countries.json",
        flags_dir=tmp_path / "flags",
        quiz_autonext_seconds=1.2,
        admin_ids_raw="",
    )
    settings.flags_dir.mkdir()
    settings.countries_data_path.write_text("[]", encoding="utf-8")

    async with session_factory() as session:
        service = AdminCatalogService(session, settings)
        try:
            await service.sync_preview()
        except ValueError as exc:
            error = str(exc)
        else:
            error = ""

    await engine.dispose()

    assert error == "Dataset is empty."


async def test_admin_catalog_service_dashboard_returns_invalid_state_when_dataset_is_broken(
    tmp_path: Path,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        countries_data_path=tmp_path / "countries.json",
        flags_dir=tmp_path / "flags",
        quiz_autonext_seconds=1.2,
        admin_ids_raw="",
    )
    settings.flags_dir.mkdir()
    settings.countries_data_path.write_text("[]", encoding="utf-8")

    async with session_factory() as session:
        service = AdminCatalogService(session, settings)
        dashboard = await service.dashboard()

    await engine.dispose()

    assert dashboard.validation.is_valid is False
    assert dashboard.health is None
    assert dashboard.preview is None


async def test_admin_catalog_service_dashboard_aggregates_valid_state(tmp_path: Path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = _settings(tmp_path)

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        store = CountryStore.from_path(
            Path("tests/fixtures/countries.json"),
            Path("tests/fixtures"),
        )
        await repository.upsert_many(store.countries[:2])
        await session.commit()

        service = AdminCatalogService(session, settings)
        dashboard = await service.dashboard()

    await engine.dispose()

    assert dashboard.validation.is_valid is True
    assert dashboard.health is not None
    assert dashboard.preview is not None
    assert dashboard.preview.to_create == ["ESP", "ITA", "POL", "UKR"]
    assert dashboard.checked_at is not None
    assert dashboard.dataset_updated_at is not None
    assert dashboard.dataset_updated_at.tzinfo == UTC


async def test_admin_catalog_service_dashboard_includes_db_updated_at(tmp_path: Path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = _settings(tmp_path)

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        store = CountryStore.from_path(
            Path("tests/fixtures/countries.json"),
            Path("tests/fixtures"),
        )
        await repository.upsert_many(store.countries[:1])
        await session.commit()

        service = AdminCatalogService(session, settings)
        dashboard = await service.dashboard()

    await engine.dispose()

    assert dashboard.db_updated_at is not None
