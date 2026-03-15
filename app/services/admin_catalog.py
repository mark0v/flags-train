from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.repositories.countries import CountryCatalogRepository
from app.services.catalog_health import CatalogHealthReport, build_catalog_health_report
from app.services.catalog_sync_preview import CatalogSyncPreview, build_catalog_sync_preview
from app.services.country_catalog_sync import sync_country_catalog
from app.services.country_store import CountryStore
from app.services.dataset_validation import DatasetValidationReport, validate_local_dataset


@dataclass(slots=True)
class AdminCatalogSyncResult:
    preview: CatalogSyncPreview
    synced_count: int


@dataclass(slots=True)
class AdminCatalogDashboard:
    validation: DatasetValidationReport
    health: CatalogHealthReport | None = None
    preview: CatalogSyncPreview | None = None
    checked_at: datetime | None = None
    dataset_updated_at: datetime | None = None
    db_updated_at: datetime | None = None


class AdminCatalogService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._repository = CountryCatalogRepository(session)

    def _dataset_path(self):
        return self._settings.resolve_path(self._settings.countries_data_path)

    def _flags_dir(self):
        return self._settings.resolve_path(self._settings.flags_dir)

    def _dataset_updated_at(self) -> datetime | None:
        dataset_path = self._dataset_path()
        if not dataset_path.exists():
            return None
        return datetime.fromtimestamp(dataset_path.stat().st_mtime, tz=UTC)

    def _load_store(self) -> CountryStore:
        return CountryStore.from_path(self._dataset_path(), self._flags_dir())

    async def _validated_store(self) -> CountryStore:
        report = await self.dataset_validation()
        if not report.is_valid:
            raise ValueError(report.error or "Dataset validation failed.")
        return self._load_store()

    async def dataset_validation(self) -> DatasetValidationReport:
        return validate_local_dataset(self._dataset_path(), self._flags_dir())

    async def dashboard(self) -> AdminCatalogDashboard:
        checked_at = datetime.now(UTC)
        dataset_updated_at = self._dataset_updated_at()
        db_updated_at = await self._repository.latest_updated_at()
        validation = await self.dataset_validation()
        if not validation.is_valid:
            return AdminCatalogDashboard(
                validation=validation,
                checked_at=checked_at,
                dataset_updated_at=dataset_updated_at,
                db_updated_at=db_updated_at,
            )

        store = self._load_store()
        health = build_catalog_health_report(
            store=store,
            db_codes=await self._repository.list_codes(),
            flags_dir=self._flags_dir(),
        )
        preview = build_catalog_sync_preview(store, await self._repository.list_countries())
        return AdminCatalogDashboard(
            validation=validation,
            health=health,
            preview=preview,
            checked_at=checked_at,
            dataset_updated_at=dataset_updated_at,
            db_updated_at=db_updated_at,
        )

    async def catalog_health(self) -> CatalogHealthReport:
        store = self._load_store()
        return build_catalog_health_report(
            store=store,
            db_codes=await self._repository.list_codes(),
            flags_dir=self._flags_dir(),
        )

    async def sync_preview(self) -> CatalogSyncPreview:
        store = await self._validated_store()
        return build_catalog_sync_preview(store, await self._repository.list_countries())

    async def apply_sync(self) -> AdminCatalogSyncResult:
        store = await self._validated_store()
        preview = build_catalog_sync_preview(store, await self._repository.list_countries())
        if not preview.has_changes:
            return AdminCatalogSyncResult(preview=preview, synced_count=preview.db_count)
        synced_count = await sync_country_catalog(self._repository, store)
        await self._session.commit()
        return AdminCatalogSyncResult(preview=preview, synced_count=synced_count)
