from __future__ import annotations

import asyncio

from app.config import get_settings
from app.main import main as run_bot
from app.services.country_store import CountryStore


def validate_local_dataset() -> None:
    settings = get_settings()
    CountryStore.from_path(
        settings.resolve_path(settings.countries_data_path),
        settings.resolve_path(settings.flags_dir),
    )


def main() -> None:
    validate_local_dataset()
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
