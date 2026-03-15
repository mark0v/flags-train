from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import language_keyboard, main_menu_keyboard
from app.constants import SupportedLanguage
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
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
