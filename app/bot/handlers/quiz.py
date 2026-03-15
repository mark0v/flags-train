import asyncio

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import (
    answer_feedback_keyboard,
    answer_keyboard,
    exit_confirmation_keyboard,
    main_menu_keyboard,
    quiz_setup_keyboard,
    wrong_answer_actions,
)
from app.bot.states import QuizStates
from app.config import Settings
from app.constants import QuizCategory, SupportedLanguage
from app.repositories.users import UserRepository
from app.services.country_store import CountryStore
from app.services.i18n import I18nService
from app.services.quiz.engine import Question, QuizEngine, QuizSession

router = Router()


async def _user_language(session: AsyncSession, callback: CallbackQuery) -> SupportedLanguage:
    users = UserRepository(session)
    user = await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    return SupportedLanguage(user.language)


async def _render_quiz_setup(
    callback: CallbackQuery,
    state: FSMContext,
    language: SupportedLanguage,
    i18n: I18nService,
) -> None:
    data = await state.get_data()
    selected_count = data.get("selected_count", 10)
    selected_categories = [
        QuizCategory(value) for value in data.get("selected_categories", [QuizCategory.FLAG.value])
    ]
    text = (
        f"<b>{i18n.text('quiz_setup_title', language)}</b>\n\n"
        f"{i18n.text('quiz_choose_count', language)}: <b>{selected_count}</b>\n"
        f"{i18n.text('quiz_choose_categories', language)}: "
        f"{', '.join(i18n.category_label(category, language) for category in selected_categories)}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=quiz_setup_keyboard(language, i18n, selected_count, selected_categories),
    )
    await callback.answer()


async def _show_question(
    bot: Bot,
    callback: CallbackQuery,
    state: FSMContext,
    session_obj: QuizSession,
    i18n: I18nService,
) -> None:
    question = session_obj.current_question()
    if question is None:
        data = await state.get_data()
        language = SupportedLanguage(data["language"])
        await callback.message.answer(
            i18n.text("quiz_complete", language),
            reply_markup=main_menu_keyboard(language, i18n),
        )
        await state.clear()
        return

    await state.update_data(current_question_id=question.id)
    caption = f"{question.prompt}\n\n<i>{session_obj.progress_text()}</i>"
    if question.flag_path:
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(question.flag_path),
            caption=caption,
            reply_markup=answer_keyboard(question.options, session_obj.language, i18n),
        )
    else:
        await callback.message.answer(
            caption,
            reply_markup=answer_keyboard(question.options, session_obj.language, i18n),
        )


async def _show_retry_question(
    callback: CallbackQuery,
    question: Question,
    language: SupportedLanguage,
    i18n: I18nService,
) -> None:
    if question.flag_path:
        await callback.message.answer_photo(
            photo=FSInputFile(question.flag_path),
            caption=question.prompt,
            reply_markup=answer_keyboard(question.options, language, i18n),
        )
        return
    await callback.message.answer(
        question.prompt,
        reply_markup=answer_keyboard(question.options, language, i18n),
    )


@router.callback_query(F.data == "menu:start_quiz")
async def start_quiz_setup(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    await state.set_state(QuizStates.setup)
    await state.update_data(
        selected_count=10,
        selected_categories=[QuizCategory.FLAG.value],
        language=language.value,
    )
    await _render_quiz_setup(callback, state, language, i18n)


@router.callback_query(QuizStates.setup, F.data.startswith("quiz:size:"))
async def update_size(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    size = int(callback.data.split(":")[2])
    await state.update_data(selected_count=size)
    await _render_quiz_setup(callback, state, language, i18n)


@router.callback_query(QuizStates.setup, F.data.startswith("quiz:category:"))
async def toggle_category(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    category = callback.data.split(":")[2]
    data = await state.get_data()
    selected = set(data.get("selected_categories", []))
    if category in selected:
        selected.remove(category)
    else:
        selected.add(category)
    await state.update_data(selected_categories=sorted(selected))
    await _render_quiz_setup(callback, state, language, i18n)


@router.callback_query(QuizStates.setup, F.data == "quiz:begin")
async def begin_quiz(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
    country_store: CountryStore,
) -> None:
    language = await _user_language(session, callback)
    data = await state.get_data()
    categories = [QuizCategory(value) for value in data.get("selected_categories", [])]
    if not categories:
        await callback.answer(i18n.text("not_enough_categories", language), show_alert=True)
        return
    engine = QuizEngine(country_store)
    try:
        quiz_session = engine.create_session(
            language=language,
            countries_count=data["selected_count"],
            categories=categories,
        )
    except ValueError:
        await callback.answer(i18n.text("dataset_too_small", language), show_alert=True)
        return

    await state.set_state(QuizStates.in_progress)
    await state.update_data(
        language=language.value,
        quiz_session=quiz_session,
        selected_categories=[item.value for item in categories],
    )
    await callback.message.edit_text(" ")
    await _show_question(bot, callback, state, quiz_session, i18n)
    await callback.answer()


@router.callback_query(QuizStates.setup, F.data == "quiz:cancel")
async def cancel_setup(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    await state.clear()
    await callback.message.edit_text(
        i18n.text("main_menu", language),
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()


@router.callback_query(QuizStates.in_progress, F.data.startswith("answer:"))
async def answer_question(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    settings: Settings,
    i18n: I18nService,
) -> None:
    if callback.data == "answer:locked":
        await callback.answer()
        return

    data = await state.get_data()
    language = SupportedLanguage(data["language"])
    quiz_session: QuizSession = data["quiz_session"]
    question = quiz_session.current_question()
    if question is None:
        await callback.answer()
        return

    selected_index = int(callback.data.split(":")[1])
    selected_option = question.options[selected_index]
    await callback.message.edit_reply_markup(
        reply_markup=answer_feedback_keyboard(
            question.options,
            selected_index,
            question.correct_option,
        )
    )

    if selected_option == question.correct_option:
        quiz_session.on_correct()
        await state.update_data(quiz_session=quiz_session)
        await callback.answer("✅")
        await asyncio.sleep(settings.quiz_autonext_seconds)
        await _show_question(bot, callback, state, quiz_session, i18n)
        return

    quiz_session.on_wrong()
    await state.update_data(quiz_session=quiz_session, wrong_question=question)
    await callback.message.answer(
        question.prompt,
        reply_markup=wrong_answer_actions(language, i18n),
    )
    await callback.answer("❌")


@router.callback_query(QuizStates.in_progress, F.data.startswith("answer_action:"))
async def answer_action(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    i18n: I18nService,
) -> None:
    data = await state.get_data()
    language = SupportedLanguage(data["language"])
    quiz_session: QuizSession = data["quiz_session"]
    question: Question = data["wrong_question"]
    action = callback.data.split(":")[1]

    if action == "show":
        await callback.message.answer(
            i18n.text("show_answer_text", language, answer=question.correct_option),
            reply_markup=wrong_answer_actions(language, i18n),
        )
        await callback.answer()
        return

    if action == "retry":
        await _show_retry_question(callback, question, language, i18n)
        await callback.answer()
        return

    quiz_session.skip_current()
    await state.update_data(quiz_session=quiz_session)
    await callback.answer()
    await _show_question(bot, callback, state, quiz_session, i18n)


@router.callback_query(QuizStates.in_progress, F.data == "quiz:cancel")
async def confirm_exit(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    await state.set_state(QuizStates.exit_confirm)
    await callback.message.answer(
        i18n.text("quiz_exit_confirm", language),
        reply_markup=exit_confirmation_keyboard(language, i18n),
    )
    await callback.answer()


@router.callback_query(QuizStates.exit_confirm, F.data == "quiz_exit:no")
async def exit_no(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    i18n: I18nService,
) -> None:
    data = await state.get_data()
    await state.set_state(QuizStates.in_progress)
    await _show_question(bot, callback, state, data["quiz_session"], i18n)
    await callback.answer()


@router.callback_query(QuizStates.exit_confirm, F.data == "quiz_exit:yes")
async def exit_yes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    await state.clear()
    await callback.message.answer(
        i18n.text("main_menu", language),
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()
