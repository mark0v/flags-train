from __future__ import annotations

import asyncio

from app.config import get_settings
from app.db.session import create_session_factory
from app.repositories.admin import AdminRepository, format_progress_country_stat


async def main() -> None:
    settings = get_settings()
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        repository = AdminRepository(session)
        weakest = await repository.weakest_countries()
        strongest = await repository.strongest_countries()

    print("Weakest countries:")
    for item in weakest:
        print(f"- {format_progress_country_stat(item)}")

    print("Strongest countries:")
    for item in strongest:
        print(f"- {format_progress_country_stat(item)}")


if __name__ == "__main__":
    asyncio.run(main())
