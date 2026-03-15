from pathlib import Path

from app.constants import SupportedLanguage
from app.services.formatters import format_population_short

REQUIRED_COUNTRY_KEYS = {
    "code",
    "localized_name",
    "capital",
    "official_language",
    "population",
    "population_display",
    "currency_name",
    "currency_code",
    "flag_file",
}


def pick_translation(data: dict, fallback: str) -> dict[str, str]:
    translations = data.get("translations", {})
    return {
        "en": fallback,
        "ru": translations.get("rus", {}).get("common") or fallback,
        "de": translations.get("deu", {}).get("common") or fallback,
    }


def is_supported_country(raw: dict) -> bool:
    return bool(
        raw.get("unMember")
        and raw.get("currencies")
        and raw.get("cca2")
        and raw.get("cca3")
    )


def normalize_country(raw: dict) -> dict:
    name_block = raw["name"]
    common_name = name_block["common"]
    capital = raw.get("capital", [common_name])[0]
    languages = list((raw.get("languages") or {}).values())
    currencies = raw.get("currencies") or {}
    currency_code, currency_data = next(iter(currencies.items()))
    population = int(raw["population"])

    return {
        "code": raw["cca3"],
        "localized_name": pick_translation(raw, common_name),
        "capital": {"en": capital, "ru": capital, "de": capital},
        "official_language": {
            "en": languages[0] if languages else "Unknown",
            "ru": languages[0] if languages else "Неизвестно",
            "de": languages[0] if languages else "Unbekannt",
        },
        "population": population,
        "population_display": {
            language: format_population_short(population, language)
            for language in ["ru", "en", "de"]
        },
        "currency_name": {
            "en": currency_data["name"],
            "ru": currency_data["name"],
            "de": currency_data["name"],
        },
        "currency_code": currency_code,
        "flag_file": f"{raw['cca2'].lower()}.svg",
    }


def validate_country_record(country: dict) -> None:
    missing_keys = REQUIRED_COUNTRY_KEYS - set(country)
    if missing_keys:
        raise ValueError(f"Country record is missing keys: {sorted(missing_keys)}")

    if len(country["code"]) != 3:
        raise ValueError(f"Country code must be 3 letters: {country['code']}")
    if not country["currency_code"]:
        raise ValueError(f"Currency code is required for {country['code']}")
    if country["population"] <= 0:
        raise ValueError(f"Population must be positive for {country['code']}")
    if not country["flag_file"].endswith(".svg"):
        raise ValueError(f"Flag file must be SVG for {country['code']}")

    for field_name in [
        "localized_name",
        "capital",
        "official_language",
        "population_display",
        "currency_name",
    ]:
        values = country[field_name]
        for language in SupportedLanguage:
            if not values.get(language.value):
                raise ValueError(f"{field_name}.{language.value} is required for {country['code']}")


def validate_dataset(countries: list[dict], flags_dir: Path | None = None) -> None:
    if not countries:
        raise ValueError("Dataset is empty.")

    seen_codes: set[str] = set()
    for country in countries:
        validate_country_record(country)
        if country["code"] in seen_codes:
            raise ValueError(f"Duplicate country code detected: {country['code']}")
        seen_codes.add(country["code"])

        if flags_dir is not None and not (flags_dir / country["flag_file"]).exists():
            raise ValueError(f"Missing flag file for {country['code']}: {country['flag_file']}")


def dataset_summary(countries: list[dict]) -> dict[str, int | str]:
    validate_dataset(countries)
    return {
        "countries_count": len(countries),
        "first_country_code": countries[0]["code"],
        "last_country_code": countries[-1]["code"],
    }
