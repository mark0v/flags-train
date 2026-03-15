from app.constants import QuizCategory, QuizMode, SupportedLanguage

TRANSLATIONS: dict[str, dict[str, str]] = {
    "choose_language": {
        "ru": "Выберите язык",
        "en": "Choose your language",
        "de": "Sprache auswählen",
    },
    "language_changed": {
        "ru": "Язык обновлен.",
        "en": "Language updated.",
        "de": "Sprache aktualisiert.",
    },
    "main_menu": {
        "ru": "Главное меню",
        "en": "Main menu",
        "de": "Hauptmenü",
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
    "admin_denied": {
        "ru": "Доступ запрещен.",
        "en": "Access denied.",
        "de": "Zugriff verweigert.",
    },
    "admin_overview_title": {
        "ru": "<b>Админ-обзор</b>",
        "en": "<b>Admin overview</b>",
        "de": "<b>Admin-Ubersicht</b>",
    },
    "admin_overview_text": {
        "ru": (
            "{title}\n\n"
            "Пользователи: <b>{users}</b>\n"
            "Квизы: <b>{quiz_runs}</b>\n"
            "Завершено: <b>{completed}</b>\n"
            "В процессе: <b>{in_progress}</b>\n"
            "Карточек в прогрессе: <b>{tracked}</b>\n"
            "Готово к повтору: <b>{due}</b>"
        ),
        "en": (
            "{title}\n\n"
            "Users: <b>{users}</b>\n"
            "Quiz runs: <b>{quiz_runs}</b>\n"
            "Completed: <b>{completed}</b>\n"
            "In progress: <b>{in_progress}</b>\n"
            "Tracked items: <b>{tracked}</b>\n"
            "Due for review: <b>{due}</b>"
        ),
        "de": (
            "{title}\n\n"
            "Nutzer: <b>{users}</b>\n"
            "Quiz-Laufe: <b>{quiz_runs}</b>\n"
            "Abgeschlossen: <b>{completed}</b>\n"
            "In Bearbeitung: <b>{in_progress}</b>\n"
            "Verfolgte Karten: <b>{tracked}</b>\n"
            "Fallig zur Wiederholung: <b>{due}</b>"
        ),
    },
    "admin_weakest_title": {
        "ru": "<b>Слабые страны</b>",
        "en": "<b>Weak countries</b>",
        "de": "<b>Schwache Lander</b>",
    },
    "admin_strongest_title": {
        "ru": "<b>Сильные страны</b>",
        "en": "<b>Strong countries</b>",
        "de": "<b>Starke Lander</b>",
    },
    "admin_empty_progress": {
        "ru": "Пока нет данных о прогрессе.",
        "en": "No progress data yet.",
        "de": "Noch keine Fortschrittsdaten.",
    },
    "admin_refresh": {
        "ru": "Обновить",
        "en": "Refresh",
        "de": "Aktualisieren",
    },
    "admin_health_title": {
        "ru": "<b>Здоровье каталога</b>",
        "en": "<b>Catalog health</b>",
        "de": "<b>Katalogzustand</b>",
    },
    "admin_health_button": {
        "ru": "Проверка каталога",
        "en": "Catalog health",
        "de": "Katalogcheck",
    },
    "admin_revalidate_button": {
        "ru": "Проверить dataset",
        "en": "Revalidate dataset",
        "de": "Datensatz prufen",
    },
    "admin_health_ok": {
        "ru": "OK",
        "en": "OK",
        "de": "OK",
    },
    "admin_health_issue": {
        "ru": "Есть проблемы",
        "en": "Issues found",
        "de": "Probleme gefunden",
    },
    "admin_health_text": {
        "ru": (
            "{title}\n\n"
            "Статус: <b>{status}</b>\n"
            "В dataset: <b>{dataset}</b>\n"
            "В DB: <b>{db}</b>\n"
            "Нет в DB: <b>{missing_in_db}</b>\n"
            "Лишнее в DB: <b>{stale_in_db}</b>\n"
            "Нет файлов флагов: <b>{missing_flags}</b>"
        ),
        "en": (
            "{title}\n\n"
            "Status: <b>{status}</b>\n"
            "Dataset countries: <b>{dataset}</b>\n"
            "DB countries: <b>{db}</b>\n"
            "Missing in DB: <b>{missing_in_db}</b>\n"
            "Stale in DB: <b>{stale_in_db}</b>\n"
            "Missing flag files: <b>{missing_flags}</b>"
        ),
        "de": (
            "{title}\n\n"
            "Status: <b>{status}</b>\n"
            "Datensatz-Lander: <b>{dataset}</b>\n"
            "DB-Lander: <b>{db}</b>\n"
            "Fehlt in DB: <b>{missing_in_db}</b>\n"
            "Veraltet in DB: <b>{stale_in_db}</b>\n"
            "Fehlende Flaggendateien: <b>{missing_flags}</b>"
        ),
    },
    "admin_health_error": {
        "ru": "Не удалось проверить каталог. Проверьте локальные данные и логи.",
        "en": "Failed to check the catalog. Verify local data and logs.",
        "de": "Der Katalog konnte nicht gepruft werden. Bitte lokale Daten und Logs prufen.",
    },
    "admin_revalidate_title": {
        "ru": "<b>Проверка dataset</b>",
        "en": "<b>Dataset validation</b>",
        "de": "<b>Datensatzvalidierung</b>",
    },
    "admin_revalidate_ok": {
        "ru": "Dataset валиден",
        "en": "Dataset is valid",
        "de": "Datensatz ist gultig",
    },
    "admin_revalidate_error": {
        "ru": "Dataset невалиден",
        "en": "Dataset is invalid",
        "de": "Datensatz ist ungueltig",
    },
    "admin_revalidate_text": {
        "ru": (
            "{title}\n\n"
            "Статус: <b>{status}</b>\n"
            "Стран: <b>{countries}</b>\n"
            "Диапазон кодов: <b>{first_code} - {last_code}</b>"
        ),
        "en": (
            "{title}\n\n"
            "Status: <b>{status}</b>\n"
            "Countries: <b>{countries}</b>\n"
            "Code range: <b>{first_code} - {last_code}</b>"
        ),
        "de": (
            "{title}\n\n"
            "Status: <b>{status}</b>\n"
            "Lander: <b>{countries}</b>\n"
            "Code-Bereich: <b>{first_code} - {last_code}</b>"
        ),
    },
    "admin_revalidate_error_text": {
        "ru": "{title}\n\nСтатус: <b>{status}</b>\nОшибка: <b>{error}</b>",
        "en": "{title}\n\nStatus: <b>{status}</b>\nError: <b>{error}</b>",
        "de": "{title}\n\nStatus: <b>{status}</b>\nFehler: <b>{error}</b>",
    },
    "admin_weakest_button": {
        "ru": "Слабые",
        "en": "Weakest",
        "de": "Schwach",
    },
    "admin_strongest_button": {
        "ru": "Сильные",
        "en": "Strongest",
        "de": "Stark",
    },
    "admin_back": {
        "ru": "Назад",
        "en": "Back",
        "de": "Zuruck",
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
            "Übersprungen: <b>{skipped}</b>\n"
            "Fehler: <b>{mistakes}</b>\n"
            "Verfolgte Karten: <b>{tracked}</b>\n"
            "Beherrscht: <b>{mastered}</b>\n"
            "Fällig zur Wiederholung: <b>{due}</b>\n"
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
        "de": "Anzahl der Länder",
    },
    "quiz_choose_mode": {
        "ru": "Режим",
        "en": "Mode",
        "de": "Modus",
    },
    "quiz_choose_categories": {
        "ru": "Категории",
        "en": "Categories",
        "de": "Kategorien",
    },
    "quiz_start": {"ru": "Старт", "en": "Start", "de": "Start"},
    "quiz_exit": {"ru": "Выйти", "en": "Exit", "de": "Beenden"},
    "quiz_exit_confirm": {
        "ru": "Выйти из квиза? Текущий прогресс будет потерян.",
        "en": "Exit the quiz? Current progress will be lost.",
        "de": "Quiz beenden? Der aktuelle Fortschritt geht verloren.",
    },
    "confirm_yes": {"ru": "Да", "en": "Yes", "de": "Ja"},
    "confirm_no": {"ru": "Нет", "en": "No", "de": "Nein"},
    "answer_show": {"ru": "Показать ответ", "en": "Show answer", "de": "Antwort zeigen"},
    "answer_retry": {"ru": "Повторить попытку", "en": "Try again", "de": "Nochmal versuchen"},
    "answer_skip": {"ru": "Пропустить", "en": "Skip", "de": "Überspringen"},
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
            "Übersprungen: <b>{skipped}</b>\n"
            "Fehler: <b>{mistakes}</b>"
        ),
    },
    "not_enough_categories": {
        "ru": "Выберите хотя бы одну категорию.",
        "en": "Choose at least one category.",
        "de": "Wählen Sie mindestens eine Kategorie.",
    },
    "dataset_too_small": {
        "ru": "Недостаточно локальных данных для такого размера квиза.",
        "en": "The local dataset is too small for this quiz size.",
        "de": "Der lokale Datensatz ist für diese Quizgröße zu klein.",
    },
    "review_not_enough": {
        "ru": "Недостаточно карточек, готовых к повтору, для такого квиза.",
        "en": "There are not enough cards due for review for this quiz.",
        "de": "Es gibt nicht genug fällige Karten für dieses Quiz.",
    },
    "new_not_enough": {
        "ru": "Недостаточно новых карточек для такого квиза.",
        "en": "There are not enough new cards for this quiz.",
        "de": "Es gibt nicht genug neue Karten für dieses Quiz.",
    },
    "show_answer_text": {
        "ru": "Правильный ответ: <b>{answer}</b>",
        "en": "Correct answer: <b>{answer}</b>",
        "de": "Richtige Antwort: <b>{answer}</b>",
    },
    "settings_text": {
        "ru": "Настройки: язык интерфейса можно менять в любой момент.",
        "en": "Settings: you can change the interface language any time.",
        "de": "Einstellungen: Die Sprache kann jederzeit geändert werden.",
    },
}

CATEGORY_LABELS: dict[QuizCategory, dict[str, str]] = {
    QuizCategory.FLAG: {"ru": "Флаг", "en": "Flag", "de": "Flagge"},
    QuizCategory.CAPITAL: {"ru": "Столица", "en": "Capital", "de": "Hauptstadt"},
    QuizCategory.LANGUAGE: {"ru": "Язык", "en": "Language", "de": "Sprache"},
    QuizCategory.POPULATION: {"ru": "Население", "en": "Population", "de": "Bevölkerung"},
    QuizCategory.CURRENCY: {"ru": "Валюта", "en": "Currency", "de": "Wahrung"},
}

MODE_LABELS: dict[QuizMode, dict[str, str]] = {
    QuizMode.MIXED: {"ru": "Смешанный", "en": "Mixed", "de": "Gemischt"},
    QuizMode.REVIEW: {"ru": "Повторение", "en": "Review", "de": "Wiederholung"},
    QuizMode.NEW: {"ru": "Новый", "en": "New", "de": "Neu"},
}


class I18nService:
    def text(self, key: str, language: SupportedLanguage, **kwargs: str) -> str:
        return TRANSLATIONS[key][language.value].format(**kwargs)

    def category_label(self, category: QuizCategory, language: SupportedLanguage) -> str:
        return CATEGORY_LABELS[category][language.value]

    def mode_label(self, mode: QuizMode, language: SupportedLanguage) -> str:
        return MODE_LABELS[mode][language.value]
