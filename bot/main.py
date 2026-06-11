"""Точка входа: сборка Dispatcher, сид каталога и запуск polling."""

from __future__ import annotations

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher

from bot.catalog_data import DEFAULT_SERVICES
from bot.config import settings
from bot.handlers import admin, catalog, daily, language, payment, results, start, survey
from core.db import create_all, session_scope
from core.repositories import seed_services

logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    """Собрать Dispatcher и подключить роутеры хендлеров."""
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        language.router,
        catalog.router,
        daily.router,
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


def _setup_logging() -> None:
    """stdout + (опц.) ротируемый файл в settings.log_dir."""
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if settings.log_dir:
        Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                Path(settings.log_dir) / "bot.log",
                maxBytes=5_000_000,
                backupCount=5,
                encoding="utf-8",
            )
        )
    logging.basicConfig(level=settings.log_level, format=fmt, handlers=handlers)


async def run() -> None:
    _setup_logging()
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
