from __future__ import annotations

import asyncio

from app.config import get_settings
from app.db.session import create_session_factory
from app.repositories.countries import CountryCatalogRepository
from app.services.country_catalog_sync import sync_country_catalog
from app.services.country_store import CountryStore


async def main() -> None:
    settings = get_settings()
    store = CountryStore.from_path(
        settings.resolve_path(settings.countries_data_path),
        settings.resolve_path(settings.flags_dir),
    )
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        synced_count = await sync_country_catalog(CountryCatalogRepository(session), store)
        await session.commit()

    print(f"Synchronized {synced_count} countries into the database catalog.")


if __name__ == "__main__":
    asyncio.run(main())
