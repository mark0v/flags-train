from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.quiz import _render_quiz_setup as render_quiz_setup
from app.bot.keyboards.common import (
    admin_keyboard,
    admin_sync_confirmation_keyboard,
    language_keyboard,
    main_menu_keyboard,
    stats_keyboard,
)
from app.bot.states import QuizStates
from app.config import Settings
from app.constants import QUIZ_SIZES, QuizMode, SupportedLanguage
from app.repositories.admin import AdminRepository, format_progress_country_stat
from app.repositories.learning_progress import LearningProgressRepository
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
from app.services.admin_catalog import AdminCatalogDashboard, AdminCatalogService
from app.services.catalog_health import format_code_list
from app.services.catalog_sync_preview import CatalogSyncPreview
from app.services.dataset_validation import DatasetValidationReport
from app.services.i18n import I18nService
from app.services.statistics import (
    CategoryProgressStat,
    LastQuizPreferences,
    UserStatsSummary,
)

router = Router()
MENU_SCREEN_TEXT = "\u2060"


def _format_optional_datetime(value) -> str:
    if value is None:
        return "-"
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


async def _show_menu(
    target: Message | CallbackQuery,
    language: SupportedLanguage,
    i18n: I18nService,
) -> None:
    markup = main_menu_keyboard(language, i18n)
    if isinstance(target, Message):
        await target.answer(MENU_SCREEN_TEXT, reply_markup=markup)
        return
    await target.message.edit_text(MENU_SCREEN_TEXT, reply_markup=markup)
    await target.answer()


def _format_stats(
    summary: UserStatsSummary,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    if not summary.has_data:
        return i18n.text("stats_empty", language)

    last_completed = (
        summary.last_completed_at.astimezone().strftime("%Y-%m-%d %H:%M")
        if summary.last_completed_at
        else "-"
    )
    stats_text = i18n.text(
        "stats_text",
        language,
        started=str(summary.quizzes_started),
        completed=str(summary.quizzes_completed),
        abandoned=str(summary.quizzes_abandoned),
        resolved=str(summary.resolved_questions),
        correct=str(summary.correct_answers),
        mistakes=str(summary.wrong_attempts),
        tracked=str(summary.tracked_items),
        mastered=str(summary.mastered_items),
        due=str(summary.due_items),
        accuracy=str(summary.accuracy_percent),
        completion_rate=str(summary.completion_rate_percent),
        recent_completed=str(summary.completed_last_7_days),
        last_completed=last_completed,
    )
    category_section = _format_stats_category_breakdown(summary, language, i18n)
    review_section = _format_stats_review_readiness(summary, language, i18n)
    sections = [stats_text]
    if category_section:
        sections.append(category_section)
    if review_section:
        sections.append(review_section)
    return "\n\n".join(sections)


def _format_stats_review_readiness(
    summary: UserStatsSummary,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    review_size = _recommended_review_size(summary.due_countries)
    readiness_text = i18n.text(
        "stats_review_readiness",
        language,
        due_countries=str(summary.due_countries),
        status=i18n.text(
            "stats_review_ready_yes" if review_size is not None else "stats_review_ready_no",
            language,
        ),
    )
    if review_size is not None:
        return readiness_text
    return f"{readiness_text}\n{i18n.text('stats_review_hint', language)}"


def _recommended_review_size(due_countries: int) -> int | None:
    for size in reversed(QUIZ_SIZES):
        if due_countries >= size:
            return size
    return None


def _resolved_continue_mode(preferences: LastQuizPreferences, due_country_count: int) -> QuizMode:
    if due_country_count >= preferences.countries_count:
        return QuizMode.REVIEW
    return preferences.mode


def _due_review_categories(summary: UserStatsSummary) -> list[str]:
    return [
        item.category.value
        for item in summary.category_breakdown or []
        if item.due_items > 0
    ]


def _stats_reply_markup(summary: UserStatsSummary, language: SupportedLanguage, i18n: I18nService):
    return stats_keyboard(
        language,
        i18n,
        review_ready=_recommended_review_size(summary.due_countries) is not None,
    )


def _format_stats_category_breakdown(
    summary: UserStatsSummary,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    breakdown = summary.category_breakdown or []
    if not breakdown:
        return ""

    focus_category = max(
        breakdown,
        key=lambda item: (item.due_items, -item.accuracy_percent, item.tracked_items),
    )
    lines = [
        i18n.text("stats_category_breakdown_title", language),
        i18n.text(
            "stats_focus_now",
            language,
            category=i18n.category_label(focus_category.category, language),
        ),
    ]
    lines.extend(_format_stats_category_line(item, language, i18n) for item in breakdown)
    return "\n".join(lines)


def _format_stats_category_line(
    item: CategoryProgressStat,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "stats_category_breakdown_line",
        language,
        category=i18n.category_label(item.category, language),
        due=str(item.due_items),
        mastered=str(item.mastered_items),
        tracked=str(item.tracked_items),
        accuracy=str(item.accuracy_percent),
    )


def _format_admin_overview(
    users_count: int,
    quiz_runs_count: int,
    completed_quiz_runs_count: int,
    in_progress_quiz_runs_count: int,
    tracked_progress_items: int,
    due_progress_items: int,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "admin_overview_text",
        language,
        title=i18n.text("admin_overview_title", language),
        users=str(users_count),
        quiz_runs=str(quiz_runs_count),
        completed=str(completed_quiz_runs_count),
        in_progress=str(in_progress_quiz_runs_count),
        tracked=str(tracked_progress_items),
        due=str(due_progress_items),
    )


def _format_admin_progress_list(
    items: list[str],
    title: str,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    if not items:
        return f"{title}\n\n{i18n.text('admin_empty_progress', language)}"
    return f"{title}\n\n" + "\n".join(f"- {item}" for item in items)


def _format_admin_catalog_health(
    dataset_count: int,
    db_count: int,
    missing_in_db: list[str],
    stale_in_db: list[str],
    missing_flag_files: list[str],
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    status_key = "admin_health_ok" if not (
        missing_in_db or stale_in_db or missing_flag_files
    ) else "admin_health_issue"
    return i18n.text(
        "admin_health_text",
        language,
        title=i18n.text("admin_health_title", language),
        status=i18n.text(status_key, language),
        dataset=str(dataset_count),
        db=str(db_count),
        missing_in_db=format_code_list(missing_in_db),
        stale_in_db=format_code_list(stale_in_db),
        missing_flags=format_code_list(missing_flag_files),
    )


def _format_admin_dataset_validation(
    report: DatasetValidationReport,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    title = i18n.text("admin_revalidate_title", language)
    if report.is_valid:
        return i18n.text(
            "admin_revalidate_text",
            language,
            title=title,
            status=i18n.text("admin_revalidate_ok", language),
            countries=str(report.countries_count),
            first_code=report.first_country_code,
            last_code=report.last_country_code,
        )
    return i18n.text(
        "admin_revalidate_error_text",
        language,
        title=title,
        status=i18n.text("admin_revalidate_error", language),
        error=report.error or "-",
    )


def _format_admin_catalog_dashboard(
    dashboard: AdminCatalogDashboard,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    title = i18n.text("admin_catalog_dashboard_title", language)
    validation_status = i18n.text(
        "admin_revalidate_ok" if dashboard.validation.is_valid else "admin_revalidate_error",
        language,
    )
    if not dashboard.validation.is_valid:
        return i18n.text(
            "admin_catalog_dashboard_invalid",
            language,
            title=title,
            validation_status=validation_status,
            error=dashboard.validation.error or "-",
            checked_at=_format_optional_datetime(dashboard.checked_at),
            dataset_updated_at=_format_optional_datetime(dashboard.dataset_updated_at),
            db_updated_at=_format_optional_datetime(dashboard.db_updated_at),
        )

    assert dashboard.health is not None
    assert dashboard.preview is not None
    return i18n.text(
        "admin_catalog_dashboard_text",
        language,
        title=title,
        validation_status=validation_status,
        countries=str(dashboard.validation.countries_count),
        health_status=i18n.text(
            "admin_health_ok" if dashboard.health.is_healthy else "admin_health_issue",
            language,
        ),
        missing_in_db=format_code_list(dashboard.health.missing_in_db),
        stale_in_db=format_code_list(dashboard.health.stale_in_db),
        pending_sync=i18n.text(
            "admin_catalog_sync_pending_yes"
            if dashboard.preview.has_changes
            else "admin_catalog_sync_pending_no",
            language,
        ),
        checked_at=_format_optional_datetime(dashboard.checked_at),
        dataset_updated_at=_format_optional_datetime(dashboard.dataset_updated_at),
        db_updated_at=_format_optional_datetime(dashboard.db_updated_at),
    )


def _format_admin_sync_preview(
    preview: CatalogSyncPreview,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "admin_sync_preview_text",
        language,
        title=i18n.text("admin_sync_preview_title", language),
        dataset=str(preview.dataset_count),
        db=str(preview.db_count),
        create_count=str(len(preview.to_create)),
        create_codes=format_code_list(preview.to_create),
        update_count=str(len(preview.to_update)),
        update_codes=format_code_list(preview.to_update),
        delete_count=str(len(preview.to_delete)),
        delete_codes=format_code_list(preview.to_delete),
    )


def _format_admin_sync_confirmation(
    preview: CatalogSyncPreview,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "admin_sync_confirm_text",
        language,
        title=i18n.text("admin_sync_confirm_title", language),
        create_count=str(len(preview.to_create)),
        create_codes=format_code_list(preview.to_create),
        update_count=str(len(preview.to_update)),
        update_codes=format_code_list(preview.to_update),
        delete_count=str(len(preview.to_delete)),
        delete_codes=format_code_list(preview.to_delete),
    )


def _format_admin_sync_result(
    preview: CatalogSyncPreview,
    synced_count: int,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "admin_sync_result_text",
        language,
        title=i18n.text("admin_sync_result_title", language),
        synced_count=str(synced_count),
        create_count=str(len(preview.to_create)),
        update_count=str(len(preview.to_update)),
        delete_count=str(len(preview.to_delete)),
    )


def _format_admin_sync_no_changes(
    preview: CatalogSyncPreview,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "admin_sync_no_changes_text",
        language,
        title=i18n.text("admin_sync_no_changes_title", language),
        dataset=str(preview.dataset_count),
        db=str(preview.db_count),
    )


def _format_admin_sync_error(
    error: str,
    language: SupportedLanguage,
    i18n: I18nService,
) -> str:
    return i18n.text(
        "admin_sync_error_text",
        language,
        title=i18n.text("admin_sync_button", language),
        error=error,
    )


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


@router.message(CommandStart())
async def start_command(message: Message, session: AsyncSession, i18n: I18nService) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    if not user.language:
        await message.answer(
            i18n.text("choose_language", SupportedLanguage.RU),
            reply_markup=language_keyboard(),
        )
        return
    await _show_menu(message, SupportedLanguage(user.language), i18n)


@router.callback_query(F.data == "menu:change_language")
async def change_language(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    users = UserRepository(session)
    await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    await callback.message.edit_text(
        i18n.text("choose_language", SupportedLanguage.RU),
        reply_markup=language_keyboard(),
    )
    await callback.answer()


@router.message(Command("admin"))
async def admin_panel(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    i18n: I18nService,
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(i18n.text("admin_denied", SupportedLanguage.EN))
        return

    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    language = SupportedLanguage(user.language or SupportedLanguage.EN.value)
    overview = await AdminRepository(session).overview()
    await message.answer(
        _format_admin_overview(
            overview.users_count,
            overview.quiz_runs_count,
            overview.completed_quiz_runs_count,
            overview.in_progress_quiz_runs_count,
            overview.tracked_progress_items,
            overview.due_progress_items,
            language,
            i18n,
        ),
        reply_markup=admin_keyboard(language, i18n),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nService,
) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    language = SupportedLanguage(callback.data.split(":")[1])
    await users.set_language(user, language)
    await state.clear()
    await callback.answer(i18n.text("language_changed", language))
    await _show_menu(callback, language, i18n)


@router.callback_query(F.data == "menu:settings")
async def settings(callback: CallbackQuery, session: AsyncSession, i18n: I18nService) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    language = SupportedLanguage(user.language)
    await callback.message.edit_text(
        i18n.text("settings_text", language),
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:continue_learning")
async def continue_learning(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    language = SupportedLanguage(user.language)
    quiz_runs = QuizRunRepository(session)
    preferences = await quiz_runs.get_last_quiz_preferences(user.id)
    if preferences is None:
        await callback.answer(i18n.text("continue_learning_missing", language), show_alert=True)
        return

    progress_repo = LearningProgressRepository(session)
    due_country_count = len(
        await progress_repo.get_due_country_codes(
            user.id,
            preferences.categories,
            preferences.countries_count,
        )
    )
    selected_mode = _resolved_continue_mode(preferences, due_country_count)
    await state.set_state(QuizStates.setup)
    await state.update_data(
        selected_count=preferences.countries_count,
        selected_mode=selected_mode.value,
        selected_categories=[category.value for category in preferences.categories],
        language=language.value,
    )
    await render_quiz_setup(callback, state, language, i18n)
    await callback.answer(i18n.text("continue_learning_restored", language))


@router.callback_query(F.data == "menu:back")
async def menu_back(callback: CallbackQuery, session: AsyncSession, i18n: I18nService) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    await _show_menu(callback, SupportedLanguage(user.language), i18n)


@router.callback_query(F.data == "menu:stats")
async def stats(callback: CallbackQuery, session: AsyncSession, i18n: I18nService) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    language = SupportedLanguage(user.language)
    summary = await QuizRunRepository(session).get_user_summary(user.id)
    await callback.message.edit_text(
        _format_stats(summary, language, i18n),
        reply_markup=_stats_reply_markup(summary, language, i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "stats:review_setup")
async def stats_review_setup(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    language = SupportedLanguage(user.language)
    summary = await QuizRunRepository(session).get_user_summary(user.id)
    review_size = _recommended_review_size(summary.due_countries)
    due_categories = _due_review_categories(summary)
    if review_size is None or not due_categories:
        await callback.answer(i18n.text("stats_review_unavailable", language), show_alert=True)
        return

    await state.set_state(QuizStates.setup)
    await state.update_data(
        selected_count=review_size,
        selected_mode=QuizMode.REVIEW.value,
        selected_categories=due_categories,
        language=language.value,
    )
    await render_quiz_setup(callback, state, language, i18n)


@router.callback_query(F.data.startswith("admin:"))
async def admin_actions(
    callback: CallbackQuery,
    session: AsyncSession,
    settings: Settings,
    i18n: I18nService,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(i18n.text("admin_denied", SupportedLanguage.EN), show_alert=True)
        return

    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    language = SupportedLanguage(user.language or SupportedLanguage.EN.value)
    action = callback.data.split(":")[1]
    repository = AdminRepository(session)
    catalog_service = AdminCatalogService(session, settings)

    if action == "back":
        await _show_menu(callback, language, i18n)
        return

    if action == "overview":
        overview = await repository.overview()
        text = _format_admin_overview(
            overview.users_count,
            overview.quiz_runs_count,
            overview.completed_quiz_runs_count,
            overview.in_progress_quiz_runs_count,
            overview.tracked_progress_items,
            overview.due_progress_items,
            language,
            i18n,
        )
    elif action == "catalog_dashboard":
        dashboard = await catalog_service.dashboard()
        text = _format_admin_catalog_dashboard(dashboard, language, i18n)
    elif action == "health":
        try:
            report = await catalog_service.catalog_health()
            text = _format_admin_catalog_health(
                report.dataset_count,
                report.db_count,
                report.missing_in_db,
                report.stale_in_db,
                report.missing_flag_files,
                language,
                i18n,
            )
        except Exception:
            text = i18n.text("admin_health_error", language)
    elif action == "revalidate":
        report = await catalog_service.dataset_validation()
        text = _format_admin_dataset_validation(report, language, i18n)
    elif action == "sync_preview":
        try:
            preview = await catalog_service.sync_preview()
            text = (
                _format_admin_sync_preview(preview, language, i18n)
                if preview.has_changes
                else _format_admin_sync_no_changes(preview, language, i18n)
            )
        except Exception as exc:
            text = _format_admin_sync_error(str(exc), language, i18n)
    elif action == "sync_prepare":
        try:
            preview = await catalog_service.sync_preview()
            if not preview.has_changes:
                text = _format_admin_sync_no_changes(preview, language, i18n)
                await callback.message.edit_text(
                    text,
                    reply_markup=admin_keyboard(language, i18n),
                )
                await callback.answer()
                return
            text = _format_admin_sync_confirmation(preview, language, i18n)
            await callback.message.edit_text(
                text,
                reply_markup=admin_sync_confirmation_keyboard(language, i18n),
            )
            await callback.answer()
            return
        except Exception as exc:
            text = _format_admin_sync_error(str(exc), language, i18n)
    elif action == "sync_apply":
        try:
            result = await catalog_service.apply_sync()
            text = (
                _format_admin_sync_result(
                    result.preview,
                    result.synced_count,
                    language,
                    i18n,
                )
                if result.preview.has_changes
                else _format_admin_sync_no_changes(result.preview, language, i18n)
            )
        except Exception as exc:
            text = _format_admin_sync_error(str(exc), language, i18n)
    elif action == "weakest":
        weakest = await repository.weakest_countries()
        text = _format_admin_progress_list(
            [format_progress_country_stat(item) for item in weakest],
            i18n.text("admin_weakest_title", language),
            language,
            i18n,
        )
    else:
        strongest = await repository.strongest_countries()
        text = _format_admin_progress_list(
            [format_progress_country_stat(item) for item in strongest],
            i18n.text("admin_strongest_title", language),
            language,
            i18n,
        )

    await callback.message.edit_text(text, reply_markup=admin_keyboard(language, i18n))
    await callback.answer()
