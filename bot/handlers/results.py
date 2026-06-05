"""«Мои расчёты»: список ранее купленных отчётов и повторная выдача."""

from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot import keyboards, texts
from core.db import session_scope
from core.render import render_report, split_message
from core.repositories import get_or_create_user, get_result, get_survey, list_results

router = Router(name="results")


@router.callback_query(F.data == "menu:results")
async def cb_results(query: CallbackQuery) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, query.from_user.id, query.from_user.full_name)
        results = await list_results(session, user.id)
    if not results:
        await query.message.edit_text(
            texts.NO_RESULTS, reply_markup=keyboards.main_menu(), parse_mode=None
        )
        await query.answer()
        return
    rows = [
        [
            InlineKeyboardButton(
                text=f"Расчёт от {r.created_at.strftime('%d.%m.%Y')}",
                callback_data=f"res:{r.id}",
            )
        ]
        for r in results
    ]
    rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data="menu:main")])
    await query.message.edit_text(
        "Ваши расчёты:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
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

    await query.answer()
    text = render_report(report, full_name, birth)
    for chunk in split_message(text):
        await query.message.answer(chunk)
