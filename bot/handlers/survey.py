"""FSM-анкета: ФИО + дата рождения → подтверждение → расчёт и выдача.

Запускается после успешной оплаты (см. payment.py).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import keyboards, texts
from bot.states.survey import SurveyStates
from core.db import session_scope
from core.numerology import PersonInput
from core.numerology.report import build_report
from core.render import render_report, split_message
from core.repositories import save_result, save_survey
from core.validators import ValidationError, parse_birth_date, validate_name

logger = logging.getLogger(__name__)
router = Router(name="survey")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        return
    await state.clear()
    await message.answer(texts.SURVEY_CANCELLED, parse_mode=None)


@router.message(SurveyStates.last_name, F.text)
async def step_last_name(message: Message, state: FSMContext) -> None:
    try:
        value = validate_name(message.text, "Фамилия")
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(last_name=value)
    await state.set_state(SurveyStates.first_name)
    await message.answer(texts.ASK_FIRST_NAME)


@router.message(SurveyStates.first_name, F.text)
async def step_first_name(message: Message, state: FSMContext) -> None:
    try:
        value = validate_name(message.text, "Имя")
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(first_name=value)
    await state.set_state(SurveyStates.middle_name)
    await message.answer(texts.ASK_MIDDLE_NAME)


@router.message(SurveyStates.middle_name, F.text)
async def step_middle_name(message: Message, state: FSMContext) -> None:
    try:
        value = validate_name(message.text, "Отчество")
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(middle_name=value)
    await state.set_state(SurveyStates.birth_date)
    await message.answer(texts.ASK_BIRTH_DATE)


@router.message(SurveyStates.birth_date, F.text)
async def step_birth_date(message: Message, state: FSMContext) -> None:
    try:
        bd = parse_birth_date(message.text)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(birth_date=bd.isoformat())
    await state.set_state(SurveyStates.confirm)
    data = await state.get_data()
    summary = (
        "Проверьте данные:\n\n"
        f"Фамилия: {data['last_name']}\n"
        f"Имя: {data['first_name']}\n"
        f"Отчество: {data['middle_name']}\n"
        f"Дата рождения: {bd.strftime('%d.%m.%Y')}"
    )
    await message.answer(summary, reply_markup=keyboards.confirm_kb(), parse_mode=None)


@router.callback_query(SurveyStates.confirm, F.data == "survey:restart")
async def cb_restart(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    keep = {k: data[k] for k in ("order_id", "charge_id", "service_title") if k in data}
    await state.set_state(SurveyStates.last_name)
    await state.set_data(keep)
    await query.message.answer(texts.ASK_LAST_NAME)
    await query.answer()


@router.callback_query(SurveyStates.confirm, F.data == "survey:confirm")
async def cb_confirm(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await query.answer()
    await query.message.answer(texts.CALCULATING, parse_mode=None)

    person = PersonInput(
        last_name=data["last_name"],
        first_name=data["first_name"],
        middle_name=data["middle_name"],
        birth_date=date.fromisoformat(data["birth_date"]),
    )
    reference = datetime.now(UTC).date()
    report = build_report(person, reference)
    full_name = f"{person.last_name} {person.first_name} {person.middle_name}"
    text = render_report(report, full_name, person.birth_date)

    async with session_scope() as session:
        order_id = data["order_id"]
        await save_survey(
            session,
            order_id,
            last_name=person.last_name,
            first_name=person.first_name,
            middle_name=person.middle_name,
            birth_date=person.birth_date,
        )
        await save_result(session, order_id, json.dumps(report, ensure_ascii=False))

    for chunk in split_message(text):
        await query.message.answer(chunk)
    await state.clear()
    await query.message.answer(
        "Готово! Ваши расчёты — в меню «Мои расчёты».",
        reply_markup=keyboards.main_menu(),
        parse_mode=None,
    )
    logger.info("Выдан расчёт order_id=%s", order_id)
