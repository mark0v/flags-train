from __future__ import annotations

import asyncio

from app.config import get_settings
from app.db.session import create_session_factory
from app.repositories.countries import CountryCatalogRepository
from app.services.catalog_health import build_catalog_health_report
from app.services.country_store import CountryStore


async def main() -> None:
    settings = get_settings()
    dataset_path = settings.resolve_path(settings.countries_data_path)
    flags_dir = settings.resolve_path(settings.flags_dir)
    store = CountryStore.from_path(dataset_path, flags_dir)
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        report = build_catalog_health_report(
            store=store,
            db_codes=await repository.list_codes(),
            flags_dir=flags_dir,
        )

    print(f"Dataset countries: {report.dataset_count}")
    print(f"DB countries: {report.db_count}")
    print(f"Missing in DB: {', '.join(report.missing_in_db) if report.missing_in_db else '-'}")
    print(f"Stale in DB: {', '.join(report.stale_in_db) if report.stale_in_db else '-'}")
    print(
        "Missing flag files: "
        f"{', '.join(report.missing_flag_files) if report.missing_flag_files else '-'}"
    )

    if not report.is_healthy:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
