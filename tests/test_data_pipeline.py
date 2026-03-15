from pathlib import Path

import pytest

from app.services.data_pipeline import (
    dataset_summary,
    is_supported_country,
    normalize_country,
    validate_dataset,
)
from app.services.formatters import format_population_short


def test_population_formatter_respects_language() -> None:
    assert format_population_short(84_000_000, "ru") == "84 млн"
    assert format_population_short(84_000_000, "en") == "84M"
    assert format_population_short(84_000_000, "de") == "84 Mio."


def test_normalize_country_extracts_expected_fields() -> None:
    raw = {
        "name": {"common": "Germany"},
        "translations": {
            "rus": {"common": "Германия"},
            "deu": {"common": "Deutschland"},
        },
        "capital": ["Berlin"],
        "languages": {"deu": "German"},
        "currencies": {"EUR": {"name": "Euro"}},
        "population": 84_000_000,
        "cca3": "DEU",
        "cca2": "DE",
    }

    normalized = normalize_country(raw)

    assert normalized["code"] == "DEU"
    assert normalized["localized_name"]["ru"] == "Германия"
    assert normalized["currency_code"] == "EUR"
    assert normalized["flag_file"] == "de.svg"


def test_supported_country_requires_un_membership_and_flag_codes() -> None:
    assert is_supported_country(
        {"unMember": True, "currencies": {"EUR": {}}, "cca2": "DE", "cca3": "DEU"}
    )
    assert not is_supported_country(
        {"unMember": False, "currencies": {"EUR": {}}, "cca2": "DE", "cca3": "DEU"}
    )


def test_validate_dataset_detects_missing_flag(tmp_path: Path) -> None:
    countries = [
        {
            "code": "DEU",
            "localized_name": {"ru": "Германия", "en": "Germany", "de": "Deutschland"},
            "capital": {"ru": "Берлин", "en": "Berlin", "de": "Berlin"},
            "official_language": {"ru": "Немецкий", "en": "German", "de": "Deutsch"},
            "population": 84_000_000,
            "population_display": {"ru": "84 млн", "en": "84M", "de": "84 Mio."},
            "currency_name": {"ru": "Евро", "en": "Euro", "de": "Euro"},
            "currency_code": "EUR",
            "flag_file": "de.svg",
        }
    ]

    with pytest.raises(ValueError, match="Missing flag file"):
        validate_dataset(countries, tmp_path)


def test_dataset_summary_reports_basic_shape(tmp_path: Path) -> None:
    flag = tmp_path / "de.svg"
    flag.write_text("<svg></svg>", encoding="utf-8")
    countries = [
        {
            "code": "DEU",
            "localized_name": {"ru": "Германия", "en": "Germany", "de": "Deutschland"},
            "capital": {"ru": "Берлин", "en": "Berlin", "de": "Berlin"},
            "official_language": {"ru": "Немецкий", "en": "German", "de": "Deutsch"},
            "population": 84_000_000,
            "population_display": {"ru": "84 млн", "en": "84M", "de": "84 Mio."},
            "currency_name": {"ru": "Евро", "en": "Euro", "de": "Euro"},
            "currency_code": "EUR",
            "flag_file": "de.svg",
        }
    ]

    validate_dataset(countries, tmp_path)
    summary = dataset_summary(countries)

    assert summary["countries_count"] == 1
    assert summary["first_country_code"] == "DEU"
