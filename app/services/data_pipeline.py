from app.services.formatters import format_population_short


def pick_translation(data: dict, fallback: str) -> dict[str, str]:
    translations = data.get("translations", {})
    return {
        "en": fallback,
        "ru": translations.get("rus", {}).get("common") or fallback,
        "de": translations.get("deu", {}).get("common") or fallback,
    }


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
