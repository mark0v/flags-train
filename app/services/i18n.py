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
    "quiz_back_to_menu": {
        "ru": "Вы вернулись в главное меню.",
        "en": "You are back in the main menu.",
        "de": "Sie sind wieder im Hauptmenü.",
    },
    "menu_start_quiz": {
        "ru": "Начать квиз",
        "en": "Start quiz",
        "de": "Quiz starten",
    },
    "menu_continue_learning": {
        "ru": "Продолжить обучение",
        "en": "Continue learning",
        "de": "Weiter lernen",
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
    "stats_back": {
        "ru": "Назад в меню",
        "en": "Back to menu",
        "de": "Zurück zum Menü",
    },
    "continue_learning_missing": {
        "ru": "Пока нет предыдущего квиза, который можно восстановить.",
        "en": "There is no previous quiz setup to restore yet.",
        "de": "Es gibt noch kein vorheriges Quiz-Setup zum Wiederherstellen.",
    },
    "continue_learning_restored": {
        "ru": "Последняя настройка квиза восстановлена.",
        "en": "Your recent quiz setup has been restored.",
        "de": "Ihr letztes Quiz-Setup wurde wiederhergestellt.",
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
    "admin_catalog_dashboard_button": {
        "ru": "Каталог dashboard",
        "en": "Catalog dashboard",
        "de": "Katalog-Dashboard",
    },
    "admin_revalidate_button": {
        "ru": "Проверить dataset",
        "en": "Revalidate dataset",
        "de": "Datensatz prufen",
    },
    "admin_sync_preview_button": {
        "ru": "Предпросмотр sync",
        "en": "Sync preview",
        "de": "Sync-Vorschau",
    },
    "admin_sync_button": {
        "ru": "Синхронизировать каталог",
        "en": "Sync catalog",
        "de": "Katalog synchronisieren",
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
    "admin_catalog_dashboard_title": {
        "ru": "<b>Состояние каталога</b>",
        "en": "<b>Catalog status</b>",
        "de": "<b>Katalogstatus</b>",
    },
    "admin_catalog_dashboard_text": {
        "ru": (
            "{title}\n\n"
            "Проверено: <b>{checked_at}</b>\n"
            "Dataset обновлён: <b>{dataset_updated_at}</b>\n"
            "DB catalog обновлён: <b>{db_updated_at}</b>\n"
            "Dataset: <b>{validation_status}</b>\n"
            "Стран в dataset: <b>{countries}</b>\n"
            "Health-check: <b>{health_status}</b>\n"
            "Нет в DB: <b>{missing_in_db}</b>\n"
            "Лишнее в DB: <b>{stale_in_db}</b>\n"
            "Pending sync: <b>{pending_sync}</b>"
        ),
        "en": (
            "{title}\n\n"
            "Checked at: <b>{checked_at}</b>\n"
            "Dataset updated: <b>{dataset_updated_at}</b>\n"
            "DB catalog updated: <b>{db_updated_at}</b>\n"
            "Dataset: <b>{validation_status}</b>\n"
            "Dataset countries: <b>{countries}</b>\n"
            "Health check: <b>{health_status}</b>\n"
            "Missing in DB: <b>{missing_in_db}</b>\n"
            "Stale in DB: <b>{stale_in_db}</b>\n"
            "Pending sync: <b>{pending_sync}</b>"
        ),
        "de": (
            "{title}\n\n"
            "Gepruft um: <b>{checked_at}</b>\n"
            "Datensatz aktualisiert: <b>{dataset_updated_at}</b>\n"
            "DB-Katalog aktualisiert: <b>{db_updated_at}</b>\n"
            "Datensatz: <b>{validation_status}</b>\n"
            "Datensatz-Lander: <b>{countries}</b>\n"
            "Health-Check: <b>{health_status}</b>\n"
            "Fehlt in DB: <b>{missing_in_db}</b>\n"
            "Veraltet in DB: <b>{stale_in_db}</b>\n"
            "Ausstehender Sync: <b>{pending_sync}</b>"
        ),
    },
    "admin_catalog_dashboard_invalid": {
        "ru": (
            "{title}\n\n"
            "Проверено: <b>{checked_at}</b>\n"
            "Dataset обновлён: <b>{dataset_updated_at}</b>\n"
            "DB catalog обновлён: <b>{db_updated_at}</b>\n"
            "Dataset: <b>{validation_status}</b>\n"
            "Ошибка: <b>{error}</b>\n"
            "Health-check и sync preview недоступны, пока dataset не исправлен."
        ),
        "en": (
            "{title}\n\n"
            "Checked at: <b>{checked_at}</b>\n"
            "Dataset updated: <b>{dataset_updated_at}</b>\n"
            "DB catalog updated: <b>{db_updated_at}</b>\n"
            "Dataset: <b>{validation_status}</b>\n"
            "Error: <b>{error}</b>\n"
            "Health check and sync preview are unavailable until the dataset is fixed."
        ),
        "de": (
            "{title}\n\n"
            "Gepruft um: <b>{checked_at}</b>\n"
            "Datensatz aktualisiert: <b>{dataset_updated_at}</b>\n"
            "DB-Katalog aktualisiert: <b>{db_updated_at}</b>\n"
            "Datensatz: <b>{validation_status}</b>\n"
            "Fehler: <b>{error}</b>\n"
            "Health-Check und Sync-Vorschau sind erst nach einer Korrektur verfugbar."
        ),
    },
    "admin_catalog_sync_pending_yes": {
        "ru": "да",
        "en": "yes",
        "de": "ja",
    },
    "admin_catalog_sync_pending_no": {
        "ru": "нет",
        "en": "no",
        "de": "nein",
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
    "admin_sync_preview_title": {
        "ru": "<b>Предпросмотр sync каталога</b>",
        "en": "<b>Catalog sync preview</b>",
        "de": "<b>Katalog-Sync-Vorschau</b>",
    },
    "admin_sync_preview_text": {
        "ru": (
            "{title}\n\n"
            "В dataset: <b>{dataset}</b>\n"
            "В DB: <b>{db}</b>\n"
            "Будет создано: <b>{create_count}</b> ({create_codes})\n"
            "Будет обновлено: <b>{update_count}</b> ({update_codes})\n"
            "Будет удалено: <b>{delete_count}</b> ({delete_codes})"
        ),
        "en": (
            "{title}\n\n"
            "Dataset countries: <b>{dataset}</b>\n"
            "DB countries: <b>{db}</b>\n"
            "Will create: <b>{create_count}</b> ({create_codes})\n"
            "Will update: <b>{update_count}</b> ({update_codes})\n"
            "Will delete: <b>{delete_count}</b> ({delete_codes})"
        ),
        "de": (
            "{title}\n\n"
            "Datensatz-Lander: <b>{dataset}</b>\n"
            "DB-Lander: <b>{db}</b>\n"
            "Wird erstellt: <b>{create_count}</b> ({create_codes})\n"
            "Wird aktualisiert: <b>{update_count}</b> ({update_codes})\n"
            "Wird entfernt: <b>{delete_count}</b> ({delete_codes})"
        ),
    },
    "admin_sync_preview_error": {
        "ru": "Не удалось построить предпросмотр sync. Проверьте dataset и доступность БД.",
        "en": "Failed to build sync preview. Verify dataset and database availability.",
        "de": "Die Sync-Vorschau konnte nicht erstellt werden. Bitte Datensatz und DB prufen.",
    },
    "admin_sync_confirm_title": {
        "ru": "<b>Подтверждение sync каталога</b>",
        "en": "<b>Confirm catalog sync</b>",
        "de": "<b>Katalog-Sync bestatigen</b>",
    },
    "admin_sync_confirm_text": {
        "ru": (
            "{title}\n\n"
            "Сейчас будут применены изменения в таблице `countries`.\n"
            "Создать: <b>{create_count}</b> ({create_codes})\n"
            "Обновить: <b>{update_count}</b> ({update_codes})\n"
            "Удалить: <b>{delete_count}</b> ({delete_codes})\n\n"
            "Продолжить?"
        ),
        "en": (
            "{title}\n\n"
            "The following changes will be applied to the `countries` table.\n"
            "Create: <b>{create_count}</b> ({create_codes})\n"
            "Update: <b>{update_count}</b> ({update_codes})\n"
            "Delete: <b>{delete_count}</b> ({delete_codes})\n\n"
            "Continue?"
        ),
        "de": (
            "{title}\n\n"
            "Die folgenden Anderungen werden auf die Tabelle `countries` angewendet.\n"
            "Erstellen: <b>{create_count}</b> ({create_codes})\n"
            "Aktualisieren: <b>{update_count}</b> ({update_codes})\n"
            "Entfernen: <b>{delete_count}</b> ({delete_codes})\n\n"
            "Fortfahren?"
        ),
    },
    "admin_sync_result_title": {
        "ru": "<b>Sync каталога завершён</b>",
        "en": "<b>Catalog sync completed</b>",
        "de": "<b>Katalog-Sync abgeschlossen</b>",
    },
    "admin_sync_result_text": {
        "ru": (
            "{title}\n\n"
            "Итоговый размер каталога: <b>{synced_count}</b>\n"
            "Создано: <b>{create_count}</b>\n"
            "Обновлено: <b>{update_count}</b>\n"
            "Удалено: <b>{delete_count}</b>"
        ),
        "en": (
            "{title}\n\n"
            "Final catalog size: <b>{synced_count}</b>\n"
            "Created: <b>{create_count}</b>\n"
            "Updated: <b>{update_count}</b>\n"
            "Deleted: <b>{delete_count}</b>"
        ),
        "de": (
            "{title}\n\n"
            "Endgultige Kataloggrose: <b>{synced_count}</b>\n"
            "Erstellt: <b>{create_count}</b>\n"
            "Aktualisiert: <b>{update_count}</b>\n"
            "Entfernt: <b>{delete_count}</b>"
        ),
    },
    "admin_sync_no_changes_title": {
        "ru": "<b>Sync не требуется</b>",
        "en": "<b>No sync needed</b>",
        "de": "<b>Kein Sync erforderlich</b>",
    },
    "admin_sync_no_changes_text": {
        "ru": (
            "{title}\n\n"
            "Каталог уже синхронизирован.\n"
            "В dataset: <b>{dataset}</b>\n"
            "В DB: <b>{db}</b>"
        ),
        "en": (
            "{title}\n\n"
            "The catalog is already in sync.\n"
            "Dataset countries: <b>{dataset}</b>\n"
            "DB countries: <b>{db}</b>"
        ),
        "de": (
            "{title}\n\n"
            "Der Katalog ist bereits synchronisiert.\n"
            "Datensatz-Lander: <b>{dataset}</b>\n"
            "DB-Lander: <b>{db}</b>"
        ),
    },
    "admin_sync_error": {
        "ru": "Не удалось выполнить sync каталога. Проверьте dataset, БД и логи.",
        "en": "Failed to sync the catalog. Verify dataset, database, and logs.",
        "de": (
            "Der Katalog konnte nicht synchronisiert werden. "
            "Bitte Datensatz, DB und Logs prufen."
        ),
    },
    "admin_sync_error_text": {
        "ru": "{title}\n\nОшибка: <b>{error}</b>",
        "en": "{title}\n\nError: <b>{error}</b>",
        "de": "{title}\n\nFehler: <b>{error}</b>",
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
            "Досрочно завершено: <b>{abandoned}</b>\n"
            "Completion rate: <b>{completion_rate}%</b>\n"
            "Завершено за 7 дней: <b>{recent_completed}</b>\n"
            "Завершенных вопросов: <b>{resolved}</b>\n"
            "Правильно: <b>{correct}</b>\n"
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
            "Abandoned: <b>{abandoned}</b>\n"
            "Completion rate: <b>{completion_rate}%</b>\n"
            "Completed in 7 days: <b>{recent_completed}</b>\n"
            "Resolved questions: <b>{resolved}</b>\n"
            "Correct: <b>{correct}</b>\n"
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
            "Vorzeitig beendet: <b>{abandoned}</b>\n"
            "Abschlussquote: <b>{completion_rate}%</b>\n"
            "Abgeschlossen in 7 Tagen: <b>{recent_completed}</b>\n"
            "Abgeschlossene Fragen: <b>{resolved}</b>\n"
            "Richtig: <b>{correct}</b>\n"
            "Fehler: <b>{mistakes}</b>\n"
            "Verfolgte Karten: <b>{tracked}</b>\n"
            "Beherrscht: <b>{mastered}</b>\n"
            "Fällig zur Wiederholung: <b>{due}</b>\n"
            "Genauigkeit: <b>{accuracy}%</b>\n"
            "Letztes abgeschlossenes Quiz: <b>{last_completed}</b>"
        ),
    },
    "stats_category_breakdown_title": {
        "ru": "<b>Прогресс по категориям</b>",
        "en": "<b>Progress by category</b>",
        "de": "<b>Fortschritt nach Kategorien</b>",
    },
    "stats_category_breakdown_line": {
        "ru": (
            "• {category}: к повтору <b>{due}</b>, "
            "освоено <b>{mastered}/{tracked}</b>, "
            "точность <b>{accuracy}%</b>"
        ),
        "en": (
            "• {category}: due <b>{due}</b>, "
            "mastered <b>{mastered}/{tracked}</b>, "
            "accuracy <b>{accuracy}%</b>"
        ),
        "de": (
            "• {category}: fällig <b>{due}</b>, "
            "beherrscht <b>{mastered}/{tracked}</b>, "
            "Genauigkeit <b>{accuracy}%</b>"
        ),
    },
    "stats_focus_now": {
        "ru": "Сейчас стоит повторить: <b>{category}</b>",
        "en": "Best focus right now: <b>{category}</b>",
        "de": "Aktueller Fokus: <b>{category}</b>",
    },
    "stats_review_readiness": {
        "ru": (
            "Готово стран для review mode: <b>{due_countries}</b>\n"
            "Review-ready: <b>{status}</b>"
        ),
        "en": (
            "Countries ready for review mode: <b>{due_countries}</b>\n"
            "Review-ready: <b>{status}</b>"
        ),
        "de": (
            "Für den Review-Modus bereit: <b>{due_countries}</b> Länder\n"
            "Review-bereit: <b>{status}</b>"
        ),
    },
    "stats_review_ready_yes": {
        "ru": "да",
        "en": "yes",
        "de": "ja",
    },
    "stats_review_ready_no": {
        "ru": "пока нет",
        "en": "not yet",
        "de": "noch nicht",
    },
    "stats_review_hint": {
        "ru": "Быстрый review станет доступен, когда накопится хотя бы 10 due-стран.",
        "en": "Quick review becomes available once you have at least 10 due countries.",
        "de": "Schnell-Review wird verfügbar, sobald mindestens 10 fällige Länder vorhanden sind.",
    },
    "stats_review_cta": {
        "ru": "Начать review",
        "en": "Start review",
        "de": "Review starten",
    },
    "stats_review_unavailable": {
        "ru": "Для review mode пока недостаточно due-стран.",
        "en": "There are not enough due countries for review mode yet.",
        "de": "Für den Review-Modus gibt es noch nicht genug fällige Länder.",
    },
    "quiz_setup_title": {
        "ru": "Настройка квиза",
        "en": "Quiz setup",
        "de": "Quiz-Einstellungen",
    },
    "quiz_choose_count": {
        "ru": "Количество стран",
        "en": "Number of questions",
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
    "quiz_setup_cancelled": {
        "ru": "Настройка квиза отменена.",
        "en": "Quiz setup cancelled.",
        "de": "Die Quiz-Einrichtung wurde abgebrochen.",
    },
    "quiz_abandoned": {
        "ru": "Квиз завершён досрочно.",
        "en": "Quiz ended early.",
        "de": "Das Quiz wurde vorzeitig beendet.",
    },
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
    "answer_next": {"ru": "Дальше", "en": "Next", "de": "Weiter"},
    "quiz_complete_stats": {
        "ru": (
            "<b>Квиз завершён</b>\n\n"
            "Вопросов: <b>{resolved}</b>\n"
            "Правильно: <b>{correct}</b>\n"
            "Ошибок: <b>{mistakes}</b>"
        ),
        "en": (
            "<b>Quiz complete</b>\n\n"
            "Questions: <b>{resolved}</b>\n"
            "Correct: <b>{correct}</b>\n"
            "Mistakes: <b>{mistakes}</b>"
        ),
        "de": (
            "<b>Quiz abgeschlossen</b>\n\n"
            "Fragen: <b>{resolved}</b>\n"
            "Richtig: <b>{correct}</b>\n"
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
