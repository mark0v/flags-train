from aiogram import Dispatcher

from app.bot.handlers.menu import router as menu_router
from app.bot.handlers.quiz import router as quiz_router


def register_handlers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(menu_router)
    dispatcher.include_router(quiz_router)
