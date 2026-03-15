from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import Settings
from app.services.dataset_validation import DatasetValidationReport
from app.services.runtime_checks import (
    RuntimeDatabaseReport,
    RuntimePreflightReport,
    check_database_ready,
    format_runtime_preflight_report,
    resolve_expected_alembic_revision,
    run_runtime_preflight,
    runtime_preflight_failure_message,
)


def _settings(tmp_path: Path, database_url: str) -> Settings:
    flags_dir = tmp_path / "flags"
    flags_dir.mkdir()
    for flag in ["de.svg", "es.svg", "fr.svg", "it.svg", "pl.svg", "ua.svg"]:
        (flags_dir / flag).write_text("<svg />", encoding="utf-8")

    return Settings.model_construct(
        bot_token="token",
        app_env="test",
        database_url=database_url,
        countries_data_path=Path("tests/fixtures/countries.json"),
        flags_dir=flags_dir,
        quiz_autonext_seconds=1.2,
        admin_ids_raw="",
    )


async def test_check_database_ready_reports_matching_revision(tmp_path: Path) -> None:
    database_path = tmp_path / "runtime.db"
    settings = _settings(tmp_path, f"sqlite+aiosqlite:///{database_path}")
    expected_revision = resolve_expected_alembic_revision(settings.base_dir)
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": expected_revision},
        )
    await engine.dispose()

    report = await check_database_ready(settings)

    assert report.is_reachable is True
    assert report.current_revision == expected_revision
    assert report.migrations_match is True


async def test_check_database_ready_reports_unreachable_database(tmp_path: Path) -> None:
    settings = _settings(tmp_path, "postgresql+asyncpg://bad:bad@127.0.0.1:1/flags_train")

    report = await check_database_ready(settings)

    assert report.is_reachable is False
    assert report.error is not None
    assert report.migrations_match is False


async def test_run_runtime_preflight_combines_dataset_and_database_checks(tmp_path: Path) -> None:
    database_path = tmp_path / "runtime.db"
    settings = _settings(tmp_path, f"sqlite+aiosqlite:///{database_path}")
    expected_revision = resolve_expected_alembic_revision(settings.base_dir)
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": expected_revision},
        )
    await engine.dispose()

    report = await run_runtime_preflight(settings)

    assert report.dataset.is_valid is True
    assert report.database.migrations_match is True
    assert report.is_ready is True


def test_runtime_preflight_format_and_failure_message_are_human_readable() -> None:
    report = RuntimePreflightReport(
        dataset=DatasetValidationReport(
            is_valid=False,
            error="Dataset is empty.",
        ),
        database=RuntimeDatabaseReport(
            is_reachable=True,
            expected_revision="abc123",
            current_revision="abc123",
        ),
    )

    rendered = format_runtime_preflight_report(report)

    assert "Overall: NOT READY" in rendered
    assert "Dataset: FAILED (error=Dataset is empty.)" in rendered
    assert "Database: OK (revision=abc123)" in rendered
    assert runtime_preflight_failure_message(report) == "Dataset is empty."
