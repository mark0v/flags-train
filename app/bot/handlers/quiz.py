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
from app.constants import (
    QuizAnswerOutcome,
    QuizCategory,
    QuizMode,
    QuizRunStatus,
    SupportedLanguage,
)
from app.db.models import User
from app.repositories.learning_progress import LearningProgressRepository
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
from app.services.country_store import CountryStore
from app.services.i18n import I18nService
from app.services.quiz.engine import Question, QuizEngine, QuizSession

router = Router()


async def _send_question_media(
    bot: Bot,
    chat_id: int,
    question: Question,
    caption: str,
    i18n: I18nService,
    language: SupportedLanguage,
) -> None:
    if question.flag_path is None:
        raise ValueError("Question media is missing.")

    media = FSInputFile(question.flag_path)
    reply_markup = answer_keyboard(question.options, language, i18n)
    if question.flag_path.suffix.lower() == ".svg":
        await bot.send_document(
            chat_id=chat_id,
            document=media,
            caption=caption,
            reply_markup=reply_markup,
        )
        return

    await bot.send_photo(
        chat_id=chat_id,
        photo=media,
        caption=caption,
        reply_markup=reply_markup,
    )


async def _get_user(session: AsyncSession, callback: CallbackQuery) -> User:
    users = UserRepository(session)
    return await users.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )


async def _user_language(session: AsyncSession, callback: CallbackQuery) -> SupportedLanguage:
    user = await _get_user(session, callback)
    return SupportedLanguage(user.language)


async def _render_quiz_setup(
    callback: CallbackQuery,
    state: FSMContext,
    language: SupportedLanguage,
    i18n: I18nService,
) -> None:
    data = await state.get_data()
    selected_count = data.get("selected_count", 10)
    selected_mode = QuizMode(data.get("selected_mode", QuizMode.MIXED.value))
    selected_categories = [
        QuizCategory(value) for value in data.get("selected_categories", [QuizCategory.FLAG.value])
    ]
    text = (
        f"<b>{i18n.text('quiz_setup_title', language)}</b>\n\n"
        f"{i18n.text('quiz_choose_count', language)}: <b>{selected_count}</b>\n"
        f"{i18n.text('quiz_choose_mode', language)}: "
        f"<b>{i18n.mode_label(selected_mode, language)}</b>\n"
        f"{i18n.text('quiz_choose_categories', language)}: "
        f"{', '.join(i18n.category_label(category, language) for category in selected_categories)}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=quiz_setup_keyboard(
            language,
            i18n,
            selected_count,
            selected_categories,
            selected_mode,
        ),
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
            i18n.text(
                "quiz_complete_stats",
                language,
                resolved=str(session_obj.resolved_questions),
                correct=str(session_obj.correct_answers),
                skipped=str(session_obj.skipped_answers),
                mistakes=str(session_obj.mistakes),
                menu_hint=i18n.text("quiz_back_to_menu", language),
            ),
            reply_markup=main_menu_keyboard(language, i18n),
        )
        await state.clear()
        return

    await state.update_data(current_question_id=question.id)
    caption = f"{question.prompt}\n\n<i>{session_obj.progress_text()}</i>"
    if question.flag_path:
        await _send_question_media(
            bot,
            callback.message.chat.id,
            question,
            caption,
            i18n,
            session_obj.language,
        )
        return
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
        await _send_question_media(
            callback.bot,
            callback.message.chat.id,
            question,
            question.prompt,
            i18n,
            language,
        )
        return
    await callback.message.answer(
        question.prompt,
        reply_markup=answer_keyboard(question.options, language, i18n),
    )


async def _persist_resolution(
    session: AsyncSession,
    user_id: int,
    quiz_run_id: int,
    quiz_session: QuizSession,
    question: Question,
    selected_option: str | None,
    outcome: QuizAnswerOutcome,
) -> None:
    await QuizRunRepository(session).save_question_result(
        quiz_run_id=quiz_run_id,
        question=question,
        selected_option=selected_option,
        outcome=outcome,
        wrong_attempts=quiz_session.wrong_attempts(question.id),
    )
    await LearningProgressRepository(session).record_result(
        user_id=user_id,
        question=question,
        outcome=outcome,
        wrong_attempts=quiz_session.wrong_attempts(question.id),
    )


async def _finalize_run(
    session: AsyncSession,
    state: FSMContext,
    quiz_session: QuizSession,
    status: QuizRunStatus,
) -> None:
    data = await state.get_data()
    quiz_run_id = data.get("quiz_run_id")
    if quiz_run_id is None:
        return
    await QuizRunRepository(session).finish_run(
        quiz_run_id=quiz_run_id,
        status=status,
        resolved_questions=quiz_session.resolved_questions,
        correct_answers=quiz_session.correct_answers,
        skipped_answers=quiz_session.skipped_answers,
        wrong_attempts=quiz_session.mistakes,
    )


async def _finalize_run_if_complete(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    quiz_session: QuizSession,
    i18n: I18nService,
) -> bool:
    if quiz_session.current_question() is not None:
        return False
    await _finalize_run(session, state, quiz_session, QuizRunStatus.COMPLETED)
    await _show_question(callback.bot, callback, state, quiz_session, i18n)
    return True


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
        selected_mode=QuizMode.MIXED.value,
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


@router.callback_query(QuizStates.setup, F.data.startswith("quiz:mode:"))
async def update_mode(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    language = await _user_language(session, callback)
    mode = callback.data.split(":")[2]
    await state.update_data(selected_mode=mode)
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
    user = await _get_user(session, callback)
    language = SupportedLanguage(user.language)
    data = await state.get_data()
    categories = [QuizCategory(value) for value in data.get("selected_categories", [])]
    quiz_mode = QuizMode(data.get("selected_mode", QuizMode.MIXED.value))
    if not categories:
        await callback.answer(i18n.text("not_enough_categories", language), show_alert=True)
        return

    progress_repo = LearningProgressRepository(session)
    due_country_codes = await progress_repo.get_due_country_codes(
        user.id,
        categories,
        data["selected_count"],
    )
    excluded_country_codes: list[str] = []
    priority_country_codes: list[str] = []

    if quiz_mode is QuizMode.REVIEW:
        if len(due_country_codes) < data["selected_count"]:
            await callback.answer(i18n.text("review_not_enough", language), show_alert=True)
            return
        priority_country_codes = due_country_codes
    elif quiz_mode is QuizMode.NEW:
        studied_country_codes = await progress_repo.get_studied_country_codes(user.id, categories)
        excluded_country_codes = studied_country_codes
        available_new = len(
            [
                country
                for country in country_store.countries
                if country.code not in studied_country_codes
            ]
        )
        if available_new < data["selected_count"]:
            await callback.answer(i18n.text("new_not_enough", language), show_alert=True)
            return
    else:
        priority_country_codes = due_country_codes

    engine = QuizEngine(country_store)
    try:
        quiz_session = engine.create_session(
            language=language,
            countries_count=data["selected_count"],
            categories=categories,
            priority_country_codes=priority_country_codes,
            excluded_country_codes=excluded_country_codes,
        )
    except ValueError:
        await callback.answer(i18n.text("dataset_too_small", language), show_alert=True)
        return

    quiz_run = await QuizRunRepository(session).create_run(
        user_id=user.id,
        language=language,
        countries_count=data["selected_count"],
        categories=categories,
        total_questions=quiz_session.total_questions,
    )

    await state.set_state(QuizStates.in_progress)
    await state.update_data(
        language=language.value,
        quiz_session=quiz_session,
        quiz_run_id=quiz_run.id,
        user_id=user.id,
        selected_categories=[item.value for item in categories],
    )
    await callback.message.edit_text(
        f"<b>{i18n.text('quiz_setup_title', language)}</b>\n\n"
        f"{i18n.text('quiz_start', language)}..."
    )
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
        f"{i18n.text('quiz_setup_cancelled', language)}\n\n"
        f"{i18n.text('main_menu', language)}",
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()


@router.callback_query(QuizStates.in_progress, F.data.startswith("answer:"))
async def answer_question(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
    i18n: I18nService,
) -> None:
    if callback.data == "answer:locked":
        await callback.answer()
        return

    data = await state.get_data()
    language = SupportedLanguage(data["language"])
    quiz_session: QuizSession = data["quiz_session"]
    quiz_run_id: int = data["quiz_run_id"]
    user_id: int = data["user_id"]
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
        resolution = quiz_session.on_correct(selected_option)
        if resolution.resolved:
            await _persist_resolution(
                session,
                user_id,
                quiz_run_id,
                quiz_session,
                resolution.question,
                selected_option,
                QuizAnswerOutcome.CORRECT,
            )
        await state.update_data(quiz_session=quiz_session)
        await callback.answer("✅")
        if await _finalize_run_if_complete(callback, state, session, quiz_session, i18n):
            return
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
    session: AsyncSession,
    i18n: I18nService,
) -> None:
    data = await state.get_data()
    language = SupportedLanguage(data["language"])
    quiz_session: QuizSession = data["quiz_session"]
    question: Question = data["wrong_question"]
    quiz_run_id: int = data["quiz_run_id"]
    user_id: int = data["user_id"]
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

    resolution = quiz_session.skip_current()
    if resolution.resolved:
        await _persist_resolution(
            session,
            user_id,
            quiz_run_id,
            quiz_session,
            resolution.question,
            None,
            QuizAnswerOutcome.SKIPPED,
        )
    await state.update_data(quiz_session=quiz_session)
    await callback.answer()
    if await _finalize_run_if_complete(callback, state, session, quiz_session, i18n):
        return
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
    data = await state.get_data()
    quiz_session: QuizSession | None = data.get("quiz_session")
    if quiz_session is not None:
        await _finalize_run(session, state, quiz_session, QuizRunStatus.ABANDONED)
    await state.clear()
    await callback.message.answer(
        f"{i18n.text('quiz_abandoned', language)}\n\n"
        f"{i18n.text('main_menu', language)}",
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()
