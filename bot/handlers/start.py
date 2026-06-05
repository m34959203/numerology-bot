"""/start, главное меню, помощь."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot import keyboards, texts
from core.db import session_scope
from core.repositories import get_or_create_user

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with session_scope() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
    await message.answer(texts.START, reply_markup=keyboards.main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "menu:main")
async def cb_main(query: CallbackQuery) -> None:
    await query.message.edit_text(
        texts.START, reply_markup=keyboards.main_menu(), parse_mode="HTML"
    )
    await query.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(query: CallbackQuery) -> None:
    await query.message.edit_text(texts.HELP, reply_markup=keyboards.main_menu(), parse_mode="HTML")
    await query.answer()
