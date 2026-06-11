"""Выбор языка интерфейса: /lang, кнопка меню «🌐 Язык», переключение ru/kk/en."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from core.db import session_scope
from core.i18n import LOCALES, t
from core.repositories import set_user_locale

router = Router(name="language")


async def _show_picker(target: Message | CallbackQuery) -> None:
    msg = target.message if isinstance(target, CallbackQuery) else target
    # Заголовок мультиязычный (пользователь ещё не выбрал язык).
    await msg.answer(t("ui.lang_title", "ru"), reply_markup=keyboards.lang_menu())


@router.message(Command("lang"))
async def cmd_lang(message: Message) -> None:
    await _show_picker(message)


@router.callback_query(F.data == "menu:lang")
async def cb_lang_menu(query: CallbackQuery) -> None:
    await query.message.answer(t("ui.lang_title", "ru"), reply_markup=keyboards.lang_menu())
    await query.answer()


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_lang(query: CallbackQuery) -> None:
    locale = query.data.split(":", 1)[1]
    if locale not in LOCALES:
        await query.answer()
        return
    async with session_scope() as session:
        await set_user_locale(session, query.from_user.id, locale)
    # Подтверждение + главное меню уже на выбранном языке.
    await query.message.answer(t("ui.lang_set", locale))
    await query.message.answer(
        t("ui.start", locale), reply_markup=keyboards.main_menu(locale), parse_mode="HTML"
    )
    await query.answer()
