import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import register_handlers
from app.config import get_settings
from app.db.session import create_session_factory
from app.middleware.db import DbSessionMiddleware
from app.services.country_store import CountryStore
from app.services.i18n import I18nService


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    session_factory = create_session_factory(settings.database_url)
    i18n = I18nService()
    country_store = CountryStore.from_path(
        settings.resolve_path(settings.countries_data_path),
        settings.resolve_path(settings.flags_dir),
    )

    dispatcher.update.middleware(DbSessionMiddleware(session_factory))
    dispatcher["settings"] = settings
    dispatcher["i18n"] = i18n
    dispatcher["country_store"] = country_store

    register_handlers(dispatcher)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
