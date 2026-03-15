from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.config import Settings
from app.db.session import create_engine
from app.services.dataset_validation import DatasetValidationReport, validate_local_dataset


@dataclass(slots=True)
class RuntimeDatabaseReport:
    is_reachable: bool
    expected_revision: str
    current_revision: str | None = None
    error: str | None = None

    @property
    def migrations_match(self) -> bool:
        return self.is_reachable and self.current_revision == self.expected_revision


@dataclass(slots=True)
class RuntimePreflightReport:
    dataset: DatasetValidationReport
    database: RuntimeDatabaseReport

    @property
    def is_ready(self) -> bool:
        return self.dataset.is_valid and self.database.migrations_match


def format_runtime_preflight_report(report: RuntimePreflightReport) -> str:
    dataset_status = "OK" if report.dataset.is_valid else "FAILED"
    dataset_detail = (
        f"countries={report.dataset.countries_count}, "
        f"range={report.dataset.first_country_code}-{report.dataset.last_country_code}"
        if report.dataset.is_valid
        else f"error={report.dataset.error or '-'}"
    )
    database_status = "OK" if report.database.is_reachable else "FAILED"
    migration_status = "OK" if report.database.migrations_match else "FAILED"
    database_detail = (
        f"revision={report.database.current_revision or '-'}"
        if report.database.is_reachable
        else f"error={report.database.error or '-'}"
    )
    return "\n".join(
        [
            f"Overall: {'READY' if report.is_ready else 'NOT READY'}",
            f"Dataset: {dataset_status} ({dataset_detail})",
            f"Database: {database_status} ({database_detail})",
            (
                "Migrations: "
                f"{migration_status} "
                f"(current={report.database.current_revision or '-'}, "
                f"expected={report.database.expected_revision})"
            ),
        ]
    )


def runtime_preflight_failure_message(report: RuntimePreflightReport) -> str:
    if not report.dataset.is_valid:
        return report.dataset.error or "Dataset validation failed."
    if not report.database.is_reachable:
        return report.database.error or "Database is not reachable."
    if not report.database.migrations_match:
        return (
            "Database schema is out of date. "
            f"Current revision: {report.database.current_revision or '-'}. "
            f"Expected revision: {report.database.expected_revision}."
        )
    return "Runtime preflight is OK."


def resolve_expected_alembic_revision(base_dir: Path) -> str:
    config = Config(str(base_dir / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    return ",".join(heads)


async def check_database_ready(settings: Settings) -> RuntimeDatabaseReport:
    expected_revision = resolve_expected_alembic_revision(settings.base_dir)
    engine = create_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            current_revision = await connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )
            return RuntimeDatabaseReport(
                is_reachable=True,
                expected_revision=expected_revision,
                current_revision=current_revision,
            )
    except Exception as exc:
        return RuntimeDatabaseReport(
            is_reachable=False,
            expected_revision=expected_revision,
            error=str(exc),
        )
    finally:
        await engine.dispose()


async def run_runtime_preflight(settings: Settings) -> RuntimePreflightReport:
    dataset = validate_local_dataset(
        settings.resolve_path(settings.countries_data_path),
        settings.resolve_path(settings.flags_dir),
    )
    database = await check_database_ready(settings)
    return RuntimePreflightReport(dataset=dataset, database=database)
