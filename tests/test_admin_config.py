from pathlib import Path

from app.config import Settings


def test_admin_ids_are_parsed_from_env_style_string() -> None:
    settings = Settings(
        BOT_TOKEN="token",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        COUNTRIES_DATA_PATH=Path("data/normalized/countries.json"),
        FLAGS_DIR=Path("data/flags"),
        ADMIN_IDS="100, 200,300",
    )

    assert settings.admin_ids == {100, 200, 300}
