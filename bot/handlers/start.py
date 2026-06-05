"""/start и главное меню (Этап 1)."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot import texts

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # TODO(Этап 1): прикрепить инлайн-меню (Услуги / Мои расчёты / Помощь).
    await message.answer(texts.START)
