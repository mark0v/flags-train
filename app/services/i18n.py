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
    "stats_empty": {
        "ru": "Пока нет завершенных данных. Сыграйте первый квиз.",
        "en": "No completed data yet. Play your first quiz.",
        "de": "Noch keine abgeschlossenen Daten. Spielen Sie zuerst ein Quiz.",
    },
    "stats_text": {
        "ru": (
            "<b>Статистика</b>\n\n"
            "Запусков: <b>{started}</b>\n"
            "Завершено: <b>{completed}</b>\n"
            "Завершенных вопросов: <b>{resolved}</b>\n"
            "Правильно: <b>{correct}</b>\n"
            "Пропущено: <b>{skipped}</b>\n"
            "Ошибок: <b>{mistakes}</b>\n"
            "Отслеживаемых карточек: <b>{tracked}</b>\n"
            "Освоено: <b>{mastered}</b>\n"
            "Готово к повтору: <b>{due}</b>\n"
            "Точность: <b>{accuracy}%</b>\n"
            "Последний завершенный квиз: <b>{last_completed}</b>"
        ),
        "en": (
            "<b>Statistics</b>\n\n"
            "Started: <b>{started}</b>\n"
            "Completed: <b>{completed}</b>\n"
            "Resolved questions: <b>{resolved}</b>\n"
            "Correct: <b>{correct}</b>\n"
            "Skipped: <b>{skipped}</b>\n"
            "Mistakes: <b>{mistakes}</b>\n"
            "Tracked cards: <b>{tracked}</b>\n"
            "Mastered: <b>{mastered}</b>\n"
            "Due for review: <b>{due}</b>\n"
            "Accuracy: <b>{accuracy}%</b>\n"
            "Last completed quiz: <b>{last_completed}</b>"
        ),
        "de": (
            "<b>Statistik</b>\n\n"
            "Gestartet: <b>{started}</b>\n"
            "Abgeschlossen: <b>{completed}</b>\n"
            "Abgeschlossene Fragen: <b>{resolved}</b>\n"
            "Richtig: <b>{correct}</b>\n"
            "Ubersprungen: <b>{skipped}</b>\n"
            "Fehler: <b>{mistakes}</b>\n"
            "Verfolgte Karten: <b>{tracked}</b>\n"
            "Beherrscht: <b>{mastered}</b>\n"
            "Fallig zur Wiederholung: <b>{due}</b>\n"
            "Genauigkeit: <b>{accuracy}%</b>\n"
            "Letztes abgeschlossenes Quiz: <b>{last_completed}</b>"
        ),
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
    "quiz_complete_stats": {
        "ru": (
            "Квиз завершен.\n\n"
            "Правильно: <b>{correct}</b>\n"
            "Пропущено: <b>{skipped}</b>\n"
            "Ошибок: <b>{mistakes}</b>"
        ),
        "en": (
            "Quiz complete.\n\n"
            "Correct: <b>{correct}</b>\n"
            "Skipped: <b>{skipped}</b>\n"
            "Mistakes: <b>{mistakes}</b>"
        ),
        "de": (
            "Quiz abgeschlossen.\n\n"
            "Richtig: <b>{correct}</b>\n"
            "Ubersprungen: <b>{skipped}</b>\n"
            "Fehler: <b>{mistakes}</b>"
        ),
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
