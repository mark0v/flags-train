from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.constants import QUIZ_SIZES, QuizCategory, QuizMode, SupportedLanguage
from app.services.i18n import I18nService


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Русский", callback_data="lang:ru")
    builder.button(text="English", callback_data="lang:en")
    builder.button(text="Deutsch", callback_data="lang:de")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard(language: SupportedLanguage, i18n: I18nService) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.text("menu_start_quiz", language), callback_data="menu:start_quiz")
    builder.button(text=i18n.text("menu_settings", language), callback_data="menu:settings")
    builder.button(
        text=i18n.text("menu_change_language", language),
        callback_data="menu:change_language",
    )
    builder.button(text=i18n.text("menu_stats", language), callback_data="menu:stats")
    builder.adjust(1)
    return builder.as_markup()


def quiz_setup_keyboard(
    language: SupportedLanguage,
    i18n: I18nService,
    selected_count: int,
    selected_categories: list[QuizCategory],
    selected_mode: QuizMode,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in QUIZ_SIZES:
        prefix = "● " if size == selected_count else ""
        builder.button(text=f"{prefix}{size}", callback_data=f"quiz:size:{size}")

    for mode in QuizMode:
        prefix = "● " if mode == selected_mode else ""
        builder.button(
            text=f"{prefix}{i18n.mode_label(mode, language)}",
            callback_data=f"quiz:mode:{mode.value}",
        )

    for category in QuizCategory:
        mark = "✓ " if category in selected_categories else ""
        builder.button(
            text=f"{mark}{i18n.category_label(category, language)}",
            callback_data=f"quiz:category:{category.value}",
        )

    builder.button(text=i18n.text("quiz_start", language), callback_data="quiz:begin")
    builder.button(text=i18n.text("quiz_exit", language), callback_data="quiz:cancel")
    builder.adjust(3, 3, 2, 3, 1, 1)
    return builder.as_markup()


def answer_keyboard(
    options: list[str],
    language: SupportedLanguage,
    i18n: I18nService,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, option in enumerate(options):
        builder.button(text=option, callback_data=f"answer:{index}")
    builder.button(text=i18n.text("quiz_exit", language), callback_data="quiz:cancel")
    builder.adjust(2, 2)
    return builder.as_markup()


def answer_feedback_keyboard(
    options: list[str],
    selected_index: int,
    correct_option: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, option in enumerate(options):
        if option == correct_option:
            label = f"✅ {option}"
        elif index == selected_index:
            label = f"❌ {option}"
        else:
            label = option
        builder.button(text=label, callback_data="answer:locked")
    builder.adjust(2, 2)
    return builder.as_markup()


def wrong_answer_actions(language: SupportedLanguage, i18n: I18nService) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.text("answer_show", language), callback_data="answer_action:show")
    builder.button(text=i18n.text("answer_retry", language), callback_data="answer_action:retry")
    builder.button(text=i18n.text("answer_skip", language), callback_data="answer_action:skip")
    builder.adjust(1)
    return builder.as_markup()


def exit_confirmation_keyboard(
    language: SupportedLanguage,
    i18n: I18nService,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.text("confirm_yes", language), callback_data="quiz_exit:yes")
    builder.button(text=i18n.text("confirm_no", language), callback_data="quiz_exit:no")
    builder.adjust(2)
    return builder.as_markup()


def admin_keyboard(language: SupportedLanguage, i18n: I18nService) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.text("admin_refresh", language), callback_data="admin:overview")
    builder.button(
        text=i18n.text("admin_catalog_dashboard_button", language),
        callback_data="admin:catalog_dashboard",
    )
    builder.button(text=i18n.text("admin_health_button", language), callback_data="admin:health")
    builder.button(
        text=i18n.text("admin_revalidate_button", language),
        callback_data="admin:revalidate",
    )
    builder.button(
        text=i18n.text("admin_sync_preview_button", language),
        callback_data="admin:sync_preview",
    )
    builder.button(
        text=i18n.text("admin_sync_button", language),
        callback_data="admin:sync_prepare",
    )
    builder.button(text=i18n.text("admin_weakest_button", language), callback_data="admin:weakest")
    builder.button(
        text=i18n.text("admin_strongest_button", language),
        callback_data="admin:strongest",
    )
    builder.button(text=i18n.text("admin_back", language), callback_data="admin:back")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def admin_sync_confirmation_keyboard(
    language: SupportedLanguage,
    i18n: I18nService,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.text("confirm_yes", language), callback_data="admin:sync_apply")
    builder.button(text=i18n.text("confirm_no", language), callback_data="admin:sync_preview")
    builder.button(text=i18n.text("admin_back", language), callback_data="admin:overview")
    builder.adjust(2, 1)
    return builder.as_markup()
