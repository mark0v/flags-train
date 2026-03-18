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


def test_app_base_dir_overrides_default_base_dir() -> None:
    settings = Settings(
        BOT_TOKEN="token",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        COUNTRIES_DATA_PATH=Path("data/normalized/countries.json"),
        FLAGS_DIR=Path("data/flags"),
        APP_BASE_DIR=Path("/app"),
    )

    assert settings.base_dir == Path("/app")
    assert settings.resolve_path(Path("data/flags")) == Path("/app/data/flags")
