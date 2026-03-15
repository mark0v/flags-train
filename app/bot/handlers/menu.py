from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import language_keyboard, main_menu_keyboard
from app.constants import SupportedLanguage
from app.repositories.users import UserRepository
from app.services.i18n import I18nService

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
    await callback.message.edit_text(
        i18n.text("stats_stub", language),
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()
