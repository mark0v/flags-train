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
