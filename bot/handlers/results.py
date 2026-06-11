"""«Мои расчёты»: список ранее купленных отчётов и повторная выдача."""

from __future__ import annotations

import json
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot import keyboards, texts
from bot.delivery import deliver_report
from core.db import session_scope
from core.repositories import (
    get_or_create_user,
    get_result,
    get_survey,
    get_user_locale,
    list_results,
)

router = Router(name="results")


@router.callback_query(F.data == "menu:results")
async def cb_results(query: CallbackQuery) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, query.from_user.id, query.from_user.full_name)
        results = await list_results(session, user.id)
    if not results:
        await query.message.edit_text(
            texts.NO_RESULTS, reply_markup=keyboards.main_menu(), parse_mode="HTML"
        )
        await query.answer()
        return
    rows = [
        [
            InlineKeyboardButton(
                text=f"📄 Отчёт от {r.created_at.strftime('%d.%m.%Y')}",
                callback_data=f"res:{r.id}",
            )
        ]
        for r in results
    ]
    rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data="menu:main")])
    await query.message.edit_text(
        texts.RESULTS_TITLE, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await query.answer()


@router.callback_query(F.data.startswith("res:"))
async def cb_open_result(query: CallbackQuery) -> None:
    result_id = int(query.data.split(":")[1])
    async with session_scope() as session:
        result = await get_result(session, result_id)
        if result is None:
            await query.answer("Расчёт не найден", show_alert=True)
            return
        survey = await get_survey(session, result.order_id)
        report = json.loads(result.payload)
        full_name = f"{survey.last_name} {survey.first_name} {survey.middle_name}" if survey else ""
        birth = survey.birth_date if survey else None
        locale = await get_user_locale(session, query.from_user.id)

    await query.answer()
    try:
        await deliver_report(query.message, report, full_name, birth, locale)
    except Exception:
        logging.getLogger(__name__).exception("Сбой повторной выдачи result_id=%s", result_id)
        await query.message.answer(texts.DELIVER_ERROR, parse_mode=None)
