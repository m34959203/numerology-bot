"""Точка входа: сборка Dispatcher, сид каталога и запуск polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.catalog_data import DEFAULT_SERVICES
from bot.config import settings
from bot.handlers import admin, catalog, payment, results, start, survey
from core.db import create_all, session_scope
from core.repositories import seed_services

logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    """Собрать Dispatcher и подключить роутеры хендлеров."""
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        catalog.router,
        payment.router,
        survey.router,
        results.router,
        admin.router,
    )
    return dp


async def on_startup() -> None:
    await create_all()
    async with session_scope() as session:
        added = await seed_services(session, DEFAULT_SERVICES)
    if added:
        logger.info("Засеяно услуг: %s", added)


async def run() -> None:
    logging.basicConfig(level=settings.log_level)
    await on_startup()
    bot = Bot(token=settings.bot_token)
    dp = build_dispatcher()
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
