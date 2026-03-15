from pathlib import Path

from app.db.models import CountryCatalog
from app.services.catalog_sync_preview import build_catalog_sync_preview
from app.services.country_store import CountryStore


def test_catalog_sync_preview_detects_create_update_and_delete() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    db_countries = [
        CountryCatalog(
            code="DEU",
            localized_name={"ru": "Германия", "en": "Germany", "de": "Deutschland"},
            capital={"ru": "Берлин", "en": "Berlin", "de": "Berlin"},
            official_language={"ru": "Немецкий", "en": "German", "de": "Deutsch"},
            population=1,
            population_display={"ru": "1", "en": "1", "de": "1"},
            currency_name={"ru": "Евро", "en": "Euro", "de": "Euro"},
            currency_code="EUR",
            flag_file="de.svg",
        ),
        CountryCatalog(
            code="ZZZ",
            localized_name={"ru": "Старое", "en": "Old", "de": "Alt"},
            capital={"ru": "Старое", "en": "Old", "de": "Alt"},
            official_language={"ru": "Старое", "en": "Old", "de": "Alt"},
            population=1,
            population_display={"ru": "1", "en": "1", "de": "1"},
            currency_name={"ru": "Старое", "en": "Old", "de": "Alt"},
            currency_code="OLD",
            flag_file="old.svg",
        ),
    ]

    preview = build_catalog_sync_preview(store, db_countries)

    assert "ESP" in preview.to_create
    assert preview.to_update == ["DEU"]
    assert preview.to_delete == ["ZZZ"]


def test_catalog_sync_preview_is_empty_when_dataset_matches_db() -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    db_countries = [
        CountryCatalog(
            code=country.code,
            localized_name=country.localized_name,
            capital=country.capital,
            official_language=country.official_language,
            population=country.population,
            population_display=country.population_display,
            currency_name=country.currency_name,
            currency_code=country.currency_code,
            flag_file=country.flag_file,
        )
        for country in store.countries
    ]

    preview = build_catalog_sync_preview(store, db_countries)

    assert preview.to_create == []
    assert preview.to_update == []
    assert preview.to_delete == []
