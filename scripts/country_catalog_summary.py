from __future__ import annotations

import asyncio

from app.config import get_settings
from app.db.session import create_session_factory
from app.repositories.countries import CountryCatalogRepository


async def main() -> None:
    settings = get_settings()
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        summary = await CountryCatalogRepository(session).summary()

    print(f"Countries in DB catalog: {summary['countries_count']}")


if __name__ == "__main__":
    asyncio.run(main())
