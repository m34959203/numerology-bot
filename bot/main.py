"""Точка входа: сборка Dispatcher и запуск (polling/webhook).

Этап 1: подключение роутеров и запуск polling. Webhook — позже.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import settings


def build_dispatcher() -> Dispatcher:
    """Собрать Dispatcher и подключить роутеры хендлеров."""
    dp = Dispatcher()

    # Роутеры подключаются по мере реализации этапов.
    # from bot.handlers import start, catalog, survey, payment, results, admin
    # dp.include_routers(start.router, catalog.router, survey.router,
    #                    payment.router, results.router, admin.router)

    return dp


async def run() -> None:
    logging.basicConfig(level=settings.log_level)
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
