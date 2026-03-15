from __future__ import annotations

import asyncio

from app.config import get_settings
from app.db.session import create_session_factory
from app.repositories.admin import AdminRepository


async def main() -> None:
    settings = get_settings()
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        overview = await AdminRepository(session).overview()

    print(f"Users: {overview.users_count}")
    print(f"Quiz runs: {overview.quiz_runs_count}")
    print(f"Completed quiz runs: {overview.completed_quiz_runs_count}")
    print(f"In-progress quiz runs: {overview.in_progress_quiz_runs_count}")
    print(f"Tracked progress items: {overview.tracked_progress_items}")
    print(f"Due progress items: {overview.due_progress_items}")


if __name__ == "__main__":
    asyncio.run(main())
