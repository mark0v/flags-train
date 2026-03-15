from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    setup = State()
    in_progress = State()
    exit_confirm = State()
