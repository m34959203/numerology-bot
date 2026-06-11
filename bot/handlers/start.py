"""/start, главное меню, помощь."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from core.db import session_scope
from core.i18n import t
from core.repositories import get_or_create_user, get_user_locale

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with session_scope() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
        locale = await get_user_locale(session, message.from_user.id)
    await message.answer(
        t("ui.start", locale), reply_markup=keyboards.main_menu(locale), parse_mode="HTML"
    )


@router.callback_query(F.data == "menu:main")
async def cb_main(query: CallbackQuery) -> None:
    async with session_scope() as session:
        locale = await get_user_locale(session, query.from_user.id)
    await query.message.edit_text(
        t("ui.start", locale), reply_markup=keyboards.main_menu(locale), parse_mode="HTML"
    )
    await query.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(query: CallbackQuery) -> None:
    async with session_scope() as session:
        locale = await get_user_locale(session, query.from_user.id)
    await query.message.edit_text(
        t("ui.help", locale), reply_markup=keyboards.main_menu(locale), parse_mode="HTML"
    )
    await query.answer()
