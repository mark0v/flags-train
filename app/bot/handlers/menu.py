from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import admin_keyboard, language_keyboard, main_menu_keyboard
from app.config import Settings
from app.constants import SupportedLanguage
from app.repositories.admin import AdminRepository, format_progress_country_stat
from app.repositories.countries import CountryCatalogRepository
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
from app.services.catalog_health import build_catalog_health_report, format_code_list
from app.services.country_store import CountryStore
from app.services.i18n import I18nService
from app.services.statistics import UserStatsSummary

router = Router()


async def _show_menu(
    target: Message | CallbackQuery,
    language: SupportedLanguage,
    i18n: I18nService,
) -> None:
    text = i18n.text("main_menu", language)
    markup = main_menu_keyboard(language, i18n)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=markup)
        return
    await target.message.edit_text(text, reply_markup=markup)
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
    return i18n.text(
        "stats_text",
        language,
        started=str(summary.quizzes_started),
        completed=str(summary.quizzes_completed),
        resolved=str(summary.resolved_questions),
        correct=str(summary.correct_answers),
        skipped=str(summary.skipped_answers),
        mistakes=str(summary.wrong_attempts),
        tracked=str(summary.tracked_items),
        mastered=str(summary.mastered_items),
        due=str(summary.due_items),
        accuracy=str(summary.accuracy_percent),
        last_completed=last_completed,
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
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()


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

    if action == "back":
        await callback.message.edit_text(
            i18n.text("main_menu", language),
            reply_markup=main_menu_keyboard(language, i18n),
        )
        await callback.answer()
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
    elif action == "health":
        try:
            dataset_path = settings.resolve_path(settings.countries_data_path)
            flags_dir = settings.resolve_path(settings.flags_dir)
            store = CountryStore.from_path(dataset_path, flags_dir)
            report = build_catalog_health_report(
                store=store,
                db_codes=await CountryCatalogRepository(session).list_codes(),
                flags_dir=flags_dir,
            )
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
