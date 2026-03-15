from app.constants import QuizCategory, QuizMode, SupportedLanguage

TRANSLATIONS: dict[str, dict[str, str]] = {
    "choose_language": {
        "ru": "Vyberite yazyk",
        "en": "Choose your language",
        "de": "Sprache auswaehlen",
    },
    "language_changed": {
        "ru": "Yazyk obnovlen.",
        "en": "Language updated.",
        "de": "Sprache aktualisiert.",
    },
    "main_menu": {
        "ru": "Glavnoe menyu",
        "en": "Main menu",
        "de": "Hauptmenue",
    },
    "menu_start_quiz": {
        "ru": "Nachat kviz",
        "en": "Start quiz",
        "de": "Quiz starten",
    },
    "menu_settings": {
        "ru": "Nastroiki",
        "en": "Settings",
        "de": "Einstellungen",
    },
    "menu_change_language": {
        "ru": "Smenit yazyk",
        "en": "Change language",
        "de": "Sprache wechseln",
    },
    "menu_stats": {
        "ru": "Statistika",
        "en": "Statistics",
        "de": "Statistik",
    },
    "stats_empty": {
        "ru": "Poka net zavershennykh dannykh. Sygrayte pervyi kviz.",
        "en": "No completed data yet. Play your first quiz.",
        "de": "Noch keine abgeschlossenen Daten. Spielen Sie zuerst ein Quiz.",
    },
    "stats_text": {
        "ru": (
            "<b>Statistika</b>\n\n"
            "Zapuskov: <b>{started}</b>\n"
            "Zaversheno: <b>{completed}</b>\n"
            "Zavershennykh voprosov: <b>{resolved}</b>\n"
            "Pravilno: <b>{correct}</b>\n"
            "Propushcheno: <b>{skipped}</b>\n"
            "Oshibok: <b>{mistakes}</b>\n"
            "Otslezhivaemykh kartochek: <b>{tracked}</b>\n"
            "Osvoeno: <b>{mastered}</b>\n"
            "Gotovo k povtoru: <b>{due}</b>\n"
            "Tochnost: <b>{accuracy}%</b>\n"
            "Poslednii zavershennyi kviz: <b>{last_completed}</b>"
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
            "Uebersprungen: <b>{skipped}</b>\n"
            "Fehler: <b>{mistakes}</b>\n"
            "Verfolgte Karten: <b>{tracked}</b>\n"
            "Beherrscht: <b>{mastered}</b>\n"
            "Faellig zur Wiederholung: <b>{due}</b>\n"
            "Genauigkeit: <b>{accuracy}%</b>\n"
            "Letztes abgeschlossenes Quiz: <b>{last_completed}</b>"
        ),
    },
    "quiz_setup_title": {
        "ru": "Nastroika kviza",
        "en": "Quiz setup",
        "de": "Quiz-Einstellungen",
    },
    "quiz_choose_count": {
        "ru": "Kolichestvo stran",
        "en": "Number of countries",
        "de": "Anzahl der Laender",
    },
    "quiz_choose_mode": {
        "ru": "Rezhim",
        "en": "Mode",
        "de": "Modus",
    },
    "quiz_choose_categories": {
        "ru": "Kategorii",
        "en": "Categories",
        "de": "Kategorien",
    },
    "quiz_start": {"ru": "Start", "en": "Start", "de": "Start"},
    "quiz_exit": {"ru": "Vyiti", "en": "Exit", "de": "Beenden"},
    "quiz_exit_confirm": {
        "ru": "Vyiti iz kviza? Tekushchii progress budet poteryan.",
        "en": "Exit the quiz? Current progress will be lost.",
        "de": "Quiz beenden? Der aktuelle Fortschritt geht verloren.",
    },
    "confirm_yes": {"ru": "Da", "en": "Yes", "de": "Ja"},
    "confirm_no": {"ru": "Net", "en": "No", "de": "Nein"},
    "answer_show": {"ru": "Pokazat otvet", "en": "Show answer", "de": "Antwort zeigen"},
    "answer_retry": {"ru": "Povtorit popytku", "en": "Try again", "de": "Nochmal versuchen"},
    "answer_skip": {"ru": "Propustit", "en": "Skip", "de": "Ueberspringen"},
    "quiz_complete_stats": {
        "ru": (
            "Kviz zavershen.\n\n"
            "Pravilno: <b>{correct}</b>\n"
            "Propushcheno: <b>{skipped}</b>\n"
            "Oshibok: <b>{mistakes}</b>"
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
            "Uebersprungen: <b>{skipped}</b>\n"
            "Fehler: <b>{mistakes}</b>"
        ),
    },
    "not_enough_categories": {
        "ru": "Vyberite hotya by odnu kategoriyu.",
        "en": "Choose at least one category.",
        "de": "Waehlen Sie mindestens eine Kategorie.",
    },
    "dataset_too_small": {
        "ru": "Nedostatochno lokalnykh dannykh dlya takogo razmera kviza.",
        "en": "The local dataset is too small for this quiz size.",
        "de": "Der lokale Datensatz ist fuer diese Quizgroesse zu klein.",
    },
    "review_not_enough": {
        "ru": "Nedostatochno kartochek, gotovykh k povtoru, dlya takogo kviza.",
        "en": "There are not enough cards due for review for this quiz.",
        "de": "Es gibt nicht genug faellige Karten fuer dieses Quiz.",
    },
    "new_not_enough": {
        "ru": "Nedostatochno novykh kartochek dlya takogo kviza.",
        "en": "There are not enough new cards for this quiz.",
        "de": "Es gibt nicht genug neue Karten fuer dieses Quiz.",
    },
    "show_answer_text": {
        "ru": "Pravilnyi otvet: <b>{answer}</b>",
        "en": "Correct answer: <b>{answer}</b>",
        "de": "Richtige Antwort: <b>{answer}</b>",
    },
    "settings_text": {
        "ru": "Nastroiki: yazyk interfeisa mozhno menyat v lyuboi moment.",
        "en": "Settings: you can change the interface language any time.",
        "de": "Einstellungen: Die Sprache kann jederzeit geaendert werden.",
    },
}

CATEGORY_LABELS: dict[QuizCategory, dict[str, str]] = {
    QuizCategory.FLAG: {"ru": "Flag", "en": "Flag", "de": "Flagge"},
    QuizCategory.CAPITAL: {"ru": "Stolitsa", "en": "Capital", "de": "Hauptstadt"},
    QuizCategory.LANGUAGE: {"ru": "Yazyk", "en": "Language", "de": "Sprache"},
    QuizCategory.POPULATION: {"ru": "Naselenie", "en": "Population", "de": "Bevoelkerung"},
    QuizCategory.CURRENCY: {"ru": "Valyuta", "en": "Currency", "de": "Wahrung"},
}

MODE_LABELS: dict[QuizMode, dict[str, str]] = {
    QuizMode.MIXED: {"ru": "Smeshannyi", "en": "Mixed", "de": "Gemischt"},
    QuizMode.REVIEW: {"ru": "Povtorenie", "en": "Review", "de": "Wiederholung"},
    QuizMode.NEW: {"ru": "Novyi", "en": "New", "de": "Neu"},
}


class I18nService:
    def text(self, key: str, language: SupportedLanguage, **kwargs: str) -> str:
        return TRANSLATIONS[key][language.value].format(**kwargs)

    def category_label(self, category: QuizCategory, language: SupportedLanguage) -> str:
        return CATEGORY_LABELS[category][language.value]

    def mode_label(self, mode: QuizMode, language: SupportedLanguage) -> str:
        return MODE_LABELS[mode][language.value]
