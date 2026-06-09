"""Каталог услуг: список, карточка, запуск оплаты.

Оплата через Telegram Stars временно отключена (settings.payment_imitation):
для проверки функционала бот имитирует успешный платёж и сразу запускает анкету.
Боевой режим Stars сохранён ниже и включается PAYMENT_IMITATION=false.
"""

from __future__ import annotations

import logging
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice

from bot import keyboards, texts
from bot.catalog_data import format_price
from bot.config import settings
from bot.states.survey import SurveyStates
from core.db import session_scope
from core.models import Order
from core.repositories import (
    create_order,
    get_or_create_user,
    get_service,
    list_active_services,
    record_payment,
)

logger = logging.getLogger(__name__)
router = Router(name="catalog")


@router.callback_query(F.data == "menu:services")
async def cb_services(query: CallbackQuery) -> None:
    async with session_scope() as session:
        services = await list_active_services(session)
    if not services:
        await query.answer("Каталог пока пуст", show_alert=True)
        return
    await query.message.edit_text(
        texts.SERVICES_TITLE, reply_markup=keyboards.services_kb(services)
    )
    await query.answer()


@router.callback_query(F.data.startswith("svc:"))
async def cb_service_card(query: CallbackQuery) -> None:
    service_id = int(query.data.split(":")[1])
    async with session_scope() as session:
        service = await get_service(session, service_id)
    if service is None or not service.is_active:
        await query.answer("Услуга недоступна", show_alert=True)
        return
    text = (
        f"<b>{escape(service.title)}</b>\n\n"
        f"{escape(service.description)}\n\n"
        f"Цена: {format_price(service.price_tenge)}"
    )
    await query.message.edit_text(
        text,
        reply_markup=keyboards.service_card_kb(service.id, service.price_tenge),
        parse_mode="HTML",
    )
    await query.answer()


@router.callback_query(F.data.startswith("pay:"))
async def cb_pay(query: CallbackQuery, state: FSMContext) -> None:
    service_id = int(query.data.split(":")[1])
    async with session_scope() as session:
        service = await get_service(session, service_id)
        if service is None or not service.is_active:
            await query.answer("Услуга недоступна", show_alert=True)
            return
        user = await get_or_create_user(session, query.from_user.id, query.from_user.full_name)
        order = await create_order(session, user.id, service.id)
        order_id, code, title, price_tenge = (
            order.id,
            service.code,
            service.title,
            service.price_tenge,
        )

    if settings.payment_imitation:
        await _imitate_payment(query, state, order_id, code, title, price_tenge)
        return

    # Боевой режим: Telegram Stars (currency XTR, provider_token пустой). payload = order_id.
    await query.message.answer_invoice(
        title=texts.PAYMENT_TITLE,
        description=title,
        payload=str(order_id),
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=service.price_stars)],
    )
    await query.answer()


async def _imitate_payment(
    query: CallbackQuery,
    state: FSMContext,
    order_id: int,
    code: str,
    title: str,
    price_tenge: int,
) -> None:
    """Имитация успешной оплаты: помечаем заказ оплаченным и запускаем анкету.

    Повторяет логику payment.on_successful_payment, но без реального платежа.
    charge_id синтетический (imitation-<order_id>) — идемпотентность сохраняется.
    """
    charge_id = f"imitation-{order_id}"
    async with session_scope() as session:
        payment = await record_payment(session, order_id, charge_id, price_tenge)
        if payment is None:
            await query.answer("Заказ уже оплачен", show_alert=True)
            return
        order = await session.get(Order, order_id)
        if order is not None:
            order.status = "paid"

    logger.info("ИМИТАЦИЯ оплаты order_id=%s charge_id=%s", order_id, charge_id)
    await state.set_state(SurveyStates.last_name)
    await state.update_data(
        order_id=order_id, charge_id=charge_id, service_code=code, service_title=title
    )
    await query.message.answer(texts.PAY_SUCCESS_IMITATION)
    await query.message.answer(texts.ASK_LAST_NAME)
    await query.answer()
