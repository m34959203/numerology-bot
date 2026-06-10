"""Прогноз на выбранную дату: дата рождения → дата прогноза → выдача.

Бесплатная интерактивная функция (нужна только дата рождения — ЧПД от неё).
Расчёт — core.numerology.daily; рендер — core.render.render_daily.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import keyboards, texts
from bot.states.daily import DailyStates
from core.numerology import PersonInput
from core.numerology.daily import daily_forecast
from core.render import render_daily, split_message
from core.validators import ValidationError, parse_birth_date, parse_target_date

logger = logging.getLogger(__name__)
router = Router(name="daily")


async def _start_daily(message: Message, state: FSMContext) -> None:
    await state.set_state(DailyStates.birth_date)
    await message.answer(texts.ASK_DAILY_BIRTH, parse_mode=None)


@router.callback_query(F.data == "menu:daily")
async def cb_daily(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await _start_daily(query.message, state)


@router.message(Command("day"))
async def cmd_day(message: Message, state: FSMContext) -> None:
    await _start_daily(message, state)


@router.message(DailyStates.birth_date, F.text)
async def step_birth_date(message: Message, state: FSMContext) -> None:
    try:
        bd = parse_birth_date(message.text)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(birth_date=bd.isoformat())
    await state.set_state(DailyStates.target_date)
    await message.answer(
        texts.ASK_DAILY_TARGET, reply_markup=keyboards.daily_today_kb(), parse_mode=None
    )


async def _deliver(message: Message, state: FSMContext, target: date) -> None:
    data = await state.get_data()
    person = PersonInput("—", "—", "—", date.fromisoformat(data["birth_date"]))
    forecast = daily_forecast(person, target)
    await state.clear()
    text = render_daily(forecast)
    for chunk in split_message(text):
        await message.answer(chunk, parse_mode=None)
    await message.answer(texts.DELIVERED, reply_markup=keyboards.to_menu_kb(), parse_mode=None)


@router.callback_query(DailyStates.target_date, F.data == "daily:today")
async def cb_today(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await _deliver(query.message, state, datetime.now(UTC).date())


@router.message(DailyStates.target_date, F.text)
async def step_target_date(message: Message, state: FSMContext) -> None:
    try:
        target = parse_target_date(message.text)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await _deliver(message, state, target)
