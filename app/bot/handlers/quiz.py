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
)
from app.bot.states import QuizStates
from app.config import Settings
from app.constants import (
    EXPOSED_QUIZ_CATEGORIES,
    QuizAnswerOutcome,
    QuizCategory,
    QuizRunStatus,
    SupportedLanguage,
)
from app.db.models import User
from app.repositories.hidden_countries import HiddenCountriesRepository
from app.repositories.learning_progress import LearningProgressRepository
from app.repositories.quiz_runs import QuizRunRepository
from app.repositories.users import UserRepository
from app.services.country_store import CountryStore
from app.services.i18n import I18nService
from app.services.quiz.engine import Question, QuizEngine, QuizSession

router = Router()
MIN_AVAILABLE_COUNTRIES = 30


def _sanitize_selected_categories(values: list[str] | None) -> list[QuizCategory]:
    exposed = set(EXPOSED_QUIZ_CATEGORIES)
    selected: list[QuizCategory] = []
    for value in values or []:
        category = QuizCategory(value)
        if category in exposed:
            selected.append(category)
    return selected or [QuizCategory.FLAG]


def _selected_country_count(question_count: int, categories: list[QuizCategory]) -> int:
    return question_count // max(len(categories), 1)


async def _send_question_media(
    bot: Bot,
    chat_id: int,
    question: Question,
    caption: str,
    i18n: I18nService,
    language: SupportedLanguage,
    *,
    hide_country_locked: bool = False,
) -> None:
    if question.flag_path is None:
        raise ValueError("Question media is missing.")

    media_path = question.flag_path
    if media_path.suffix.lower() == ".svg":
        png_path = media_path.with_suffix(".png")
        if png_path.exists():
            media_path = png_path

    media = FSInputFile(media_path)
    reply_markup = answer_keyboard(
        question.options,
        language,
        i18n,
        hide_country_locked=hide_country_locked,
    )
    if media_path.suffix.lower() == ".svg":
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
    *,
    edit_existing: bool = True,
) -> None:
    data = await state.get_data()
    selected_count = data.get("selected_count", 10)
    selected_categories = _sanitize_selected_categories(data.get("selected_categories"))
    text = (
        f"<b>{i18n.text('quiz_setup_title', language)}</b>\n\n"
        f"{i18n.text('quiz_choose_count', language)}: <b>{selected_count}</b>\n"
        f"{i18n.text('quiz_choose_categories', language)}: "
        f"{', '.join(i18n.category_label(category, language) for category in selected_categories)}"
    )
    markup = quiz_setup_keyboard(
        language,
        i18n,
        selected_count,
        selected_categories,
    )
    if edit_existing:
        await callback.message.edit_text(text, reply_markup=markup)
    else:
        await callback.message.answer(text, reply_markup=markup)
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
                mistakes=str(session_obj.mistakes),
            ),
            reply_markup=main_menu_keyboard(language, i18n),
        )
        await state.clear()
        return

    await state.update_data(current_question_id=question.id, hidden_current_question_id=None)
    caption = f"{question.prompt}\n\n<i>{session_obj.progress_text()}</i>"
    option_labels = question.option_labels or question.options
    if question.flag_path:
        media_question = Question(
            id=question.id,
            country_code=question.country_code,
            category=question.category,
            prompt=question.prompt,
            options=option_labels,
            option_labels=question.option_labels,
            correct_option=question.correct_option,
            answer_context=question.answer_context,
            flag_path=question.flag_path,
            is_retry=question.is_retry,
        )
        await _send_question_media(
            bot,
            callback.message.chat.id,
            media_question,
            caption,
            i18n,
            session_obj.language,
            hide_country_locked=False,
        )
        return
    await callback.message.answer(
        caption,
        reply_markup=answer_keyboard(option_labels, session_obj.language, i18n),
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
        selected_categories=[QuizCategory.FLAG.value],
        language=language.value,
    )
    await _render_quiz_setup(callback, state, language, i18n, edit_existing=False)


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
    exposed_values = {category.value for category in EXPOSED_QUIZ_CATEGORIES}
    selected = {value for value in data.get("selected_categories", []) if value in exposed_values}
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
    user = await _get_user(session, callback)
    language = SupportedLanguage(user.language)
    data = await state.get_data()
    categories = _sanitize_selected_categories(data.get("selected_categories"))
    if not categories:
        await callback.answer(i18n.text("not_enough_categories", language), show_alert=True)
        return

    hidden_country_codes = await HiddenCountriesRepository(session).get_hidden_country_codes(
        user.id
    )
    engine = QuizEngine(country_store)
    countries_count = _selected_country_count(data["selected_count"], categories)
    try:
        quiz_session = engine.create_session(
            language=language,
            countries_count=countries_count,
            categories=categories,
            excluded_country_codes=hidden_country_codes,
        )
    except ValueError:
        await callback.answer(i18n.text("quiz_not_enough_available", language), show_alert=True)
        return

    quiz_run = await QuizRunRepository(session).create_run(
        user_id=user.id,
        language=language,
        countries_count=countries_count,
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
        i18n.text("quiz_setup_cancelled", language),
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
    quiz_session: QuizSession = data["quiz_session"]
    quiz_run_id: int = data["quiz_run_id"]
    user_id: int = data["user_id"]
    question = quiz_session.current_question()
    if question is None:
        await callback.answer()
        return

    option_labels = question.option_labels or question.options
    correct_index = question.options.index(question.correct_option)
    selected_index = int(callback.data.split(":")[1])
    selected_option = question.options[selected_index]
    reveal_correct = selected_option == question.correct_option
    await callback.message.edit_reply_markup(
        reply_markup=answer_feedback_keyboard(
            option_labels,
            selected_index,
            correct_index,
            reveal_correct=reveal_correct,
            hide_country_text=i18n.text("quiz_hide_country", quiz_session.language),
            exit_text=i18n.text("quiz_exit", quiz_session.language),
        )
    )

    if reveal_correct:
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
        await callback.answer("\u2705")
        if await _finalize_run_if_complete(callback, state, session, quiz_session, i18n):
            return
        await asyncio.sleep(settings.quiz_autonext_seconds)
        await _show_question(bot, callback, state, quiz_session, i18n)
        return

    quiz_session.on_wrong()
    await state.update_data(quiz_session=quiz_session)
    await callback.answer("\u274c")
    await asyncio.sleep(settings.quiz_autonext_seconds)
    await callback.message.edit_reply_markup(
        reply_markup=answer_feedback_keyboard(
            option_labels,
            selected_index,
            correct_index,
            hide_country_text=i18n.text("quiz_hide_country", quiz_session.language),
            exit_text=i18n.text("quiz_exit", quiz_session.language),
        )
    )
    resolution = quiz_session.resolve_incorrect()
    if resolution.resolved:
        await _persist_resolution(
            session,
            user_id,
            quiz_run_id,
            quiz_session,
            resolution.question,
            None,
            QuizAnswerOutcome.INCORRECT,
        )
    await state.update_data(quiz_session=quiz_session)
    if await _finalize_run_if_complete(callback, state, session, quiz_session, i18n):
        return
    await asyncio.sleep(settings.quiz_autonext_seconds)
    await _show_question(bot, callback, state, quiz_session, i18n)


@router.callback_query(QuizStates.in_progress, F.data == "quiz:hide_country")
async def hide_country(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: I18nService,
    country_store: CountryStore,
) -> None:
    data = await state.get_data()
    user = await _get_user(session, callback)
    language = SupportedLanguage(user.language)
    quiz_session: QuizSession | None = data.get("quiz_session")
    if quiz_session is None:
        await callback.answer()
        return

    question = quiz_session.current_question()
    if question is None:
        await callback.answer()
        return

    hidden_repo = HiddenCountriesRepository(session)
    hidden = await hidden_repo.hide_country(
        user.id,
        question.country_code,
        total_country_count=len(country_store.countries),
        min_available_countries=MIN_AVAILABLE_COUNTRIES,
    )
    if not hidden:
        await callback.answer(i18n.text("quiz_hide_country_limit", language), show_alert=True)
        return

    option_labels = question.option_labels or question.options
    await callback.message.edit_reply_markup(
        reply_markup=answer_keyboard(
            option_labels,
            quiz_session.language,
            i18n,
            hide_country_locked=True,
        )
    )
    await state.update_data(hidden_current_question_id=question.id)
    await callback.answer(i18n.text("quiz_hide_country_done", language))


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
        i18n.text("quiz_abandoned", language),
        reply_markup=main_menu_keyboard(language, i18n),
    )
    await callback.answer()
