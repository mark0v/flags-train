from app.services.data_pipeline import normalize_country
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
