from app.constants import QuizCategory, SupportedLanguage

TRANSLATIONS: dict[str, dict[str, str]] = {
    "choose_language": {
        "ru": "Выберите язык",
        "en": "Choose your language",
        "de": "Sprache auswahlen",
    },
    "language_changed": {
        "ru": "Язык обновлен.",
        "en": "Language updated.",
        "de": "Sprache aktualisiert.",
    },
    "main_menu": {
        "ru": "Главное меню",
        "en": "Main menu",
        "de": "Hauptmenu",
    },
    "menu_start_quiz": {
        "ru": "Начать квиз",
        "en": "Start quiz",
        "de": "Quiz starten",
    },
    "menu_settings": {
        "ru": "Настройки",
        "en": "Settings",
        "de": "Einstellungen",
    },
    "menu_change_language": {
        "ru": "Сменить язык",
        "en": "Change language",
        "de": "Sprache wechseln",
    },
    "menu_stats": {
        "ru": "Статистика",
        "en": "Statistics",
        "de": "Statistik",
    },
    "stats_stub": {
        "ru": "Статистика скоро появится.",
        "en": "Statistics are coming soon.",
        "de": "Statistiken kommen bald.",
    },
    "quiz_setup_title": {
        "ru": "Настройка квиза",
        "en": "Quiz setup",
        "de": "Quiz-Einstellungen",
    },
    "quiz_choose_count": {
        "ru": "Количество стран",
        "en": "Number of countries",
        "de": "Anzahl der Lander",
    },
    "quiz_choose_categories": {
        "ru": "Категории",
        "en": "Categories",
        "de": "Kategorien",
    },
    "quiz_start": {
        "ru": "Старт",
        "en": "Start",
        "de": "Start",
    },
    "quiz_exit": {
        "ru": "Выйти",
        "en": "Exit",
        "de": "Beenden",
    },
    "quiz_exit_confirm": {
        "ru": "Выйти из квиза? Текущий прогресс будет потерян.",
        "en": "Exit the quiz? Current progress will be lost.",
        "de": "Quiz beenden? Der aktuelle Fortschritt geht verloren.",
    },
    "confirm_yes": {
        "ru": "Да",
        "en": "Yes",
        "de": "Ja",
    },
    "confirm_no": {
        "ru": "Нет",
        "en": "No",
        "de": "Nein",
    },
    "answer_show": {
        "ru": "Показать ответ",
        "en": "Show answer",
        "de": "Antwort zeigen",
    },
    "answer_retry": {
        "ru": "Повторить попытку",
        "en": "Try again",
        "de": "Nochmal versuchen",
    },
    "answer_skip": {
        "ru": "Пропустить",
        "en": "Skip",
        "de": "Uberspringen",
    },
    "quiz_complete": {
        "ru": "Квиз завершен. Верну вас в меню.",
        "en": "Quiz complete. Returning to menu.",
        "de": "Quiz abgeschlossen. Zuruck zum Menu.",
    },
    "not_enough_categories": {
        "ru": "Выберите хотя бы одну категорию.",
        "en": "Choose at least one category.",
        "de": "Wahlen Sie mindestens eine Kategorie.",
    },
    "dataset_too_small": {
        "ru": "Недостаточно локальных данных для такого размера квиза.",
        "en": "The local dataset is too small for this quiz size.",
        "de": "Der lokale Datensatz ist fur diese Quizgrosse zu klein.",
    },
    "show_answer_text": {
        "ru": "Правильный ответ: <b>{answer}</b>",
        "en": "Correct answer: <b>{answer}</b>",
        "de": "Richtige Antwort: <b>{answer}</b>",
    },
    "settings_text": {
        "ru": "Настройки: язык интерфейса можно менять в любой момент.",
        "en": "Settings: you can change the interface language any time.",
        "de": "Einstellungen: Die Sprache kann jederzeit geandert werden.",
    },
}

CATEGORY_LABELS: dict[QuizCategory, dict[str, str]] = {
    QuizCategory.FLAG: {"ru": "Флаг", "en": "Flag", "de": "Flagge"},
    QuizCategory.CAPITAL: {"ru": "Столица", "en": "Capital", "de": "Hauptstadt"},
    QuizCategory.LANGUAGE: {"ru": "Язык", "en": "Language", "de": "Sprache"},
    QuizCategory.POPULATION: {"ru": "Население", "en": "Population", "de": "Bevolkerung"},
    QuizCategory.CURRENCY: {"ru": "Валюта", "en": "Currency", "de": "Wahrung"},
}


class I18nService:
    def text(self, key: str, language: SupportedLanguage, **kwargs: str) -> str:
        translation = TRANSLATIONS[key][language.value]
        return translation.format(**kwargs)

    def category_label(self, category: QuizCategory, language: SupportedLanguage) -> str:
        return CATEGORY_LABELS[category][language.value]
