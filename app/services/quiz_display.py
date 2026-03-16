from app.constants import QuizCategory, SupportedLanguage

SHORT_FLAG_OPTION_LABELS: dict[SupportedLanguage, dict[str, str]] = {
    SupportedLanguage.EN: {
        "Bosnia and Herzegovina": "Bosnia & Herz.",
        "Central African Republic": "CAR",
        "Dominican Republic": "Dominican Rep.",
        "Equatorial Guinea": "Eq. Guinea",
        "Federated States of Micronesia": "Micronesia",
        "Marshall Islands": "Marshall Is.",
        "Republic of the Congo": "Congo",
        "Solomon Islands": "Solomon Is.",
        "United Arab Emirates": "UAE",
        "United Kingdom": "UK",
        "United States": "USA",
    },
    SupportedLanguage.RU: {
        "Босния и Герцеговина": "Босния и Герц.",
        "Доминиканская Республика": "Доминикана",
        "Маршалловы Острова": "Маршалловы",
        "Объединённые Арабские Эмираты": "ОАЭ",
        "Республика Конго": "Конго",
        "Сейшельские Острова": "Сейшелы",
        "Соломоновы Острова": "Соломоновы",
        "Соединённое Королевство": "Великобритания",
        "Соединённые Штаты": "США",
        "Федеративные Штаты Микронезии": "Микронезия",
        "Центральноафриканская Республика": "ЦАР",
    },
    SupportedLanguage.DE: {
        "Bosnien und Herzegowina": "Bosnien & Herz.",
        "Dominikanische Republik": "Dominik. Rep.",
        "Marshallinseln": "Marshallins.",
        "Mikronesien": "Mikronesien",
        "Republik Kongo": "Kongo",
        "Solomoninseln": "Solomonins.",
        "Vereinigte Arabische Emirate": "VAE",
        "Vereinigte Staaten": "USA",
        "Vereinigtes Königreich": "UK",
        "Zentralafrikanische Republik": "ZAR",
    },
}


def quiz_option_label(
    option: str,
    category: QuizCategory,
    language: SupportedLanguage,
) -> str:
    if category is not QuizCategory.FLAG:
        return option
    return SHORT_FLAG_OPTION_LABELS.get(language, {}).get(option, option)
