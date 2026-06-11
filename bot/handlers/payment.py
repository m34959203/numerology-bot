"""Оплата через Telegram Stars (Этап 1).

Поток: send_invoice(XTR) -> pre_checkout_query(ok) -> successful_payment.
Идемпотентность: telegram_payment_charge_id уникален, один платёж = одна выдача.
После оплаты запускается FSM-анкета (порядок «оплата → анкета»).
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PreCheckoutQuery

from bot.states.survey import SurveyStates
from core.db import session_scope
from core.i18n import t
from core.models import Order
from core.repositories import get_service, get_user_locale, record_payment

logger = logging.getLogger(__name__)
router = Router(name="payment")


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    # Проверяем, что заказ существует, прежде чем подтверждать списание.
    async with session_scope() as session:
        locale = await get_user_locale(session, query.from_user.id)
    try:
        order_id = int(query.invoice_payload)
    except (TypeError, ValueError):
        await query.answer(ok=False, error_message=t("ui.invalid_order", locale))
        return
    async with session_scope() as session:
        order = await session.get(Order, order_id)
        ok = order is not None
    await query.answer(ok=ok, error_message=None if ok else t("ui.order_not_found", locale))


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, state: FSMContext) -> None:
    sp = message.successful_payment
    order_id = int(sp.invoice_payload)
    charge_id = sp.telegram_payment_charge_id

    async with session_scope() as session:
        payment = await record_payment(session, order_id, charge_id, sp.total_amount)
        if payment is None:
            logger.info("Дубликат платежа charge_id=%s, выдача пропущена", charge_id)
            return  # идемпотентность: повторная выдача не нужна
        order = await session.get(Order, order_id)
        if order is not None:
            order.status = "paid"
        service = await get_service(session, order.service_id) if order else None
        locale = await get_user_locale(session, message.from_user.id)

    logger.info("Платёж принят order_id=%s charge_id=%s", order_id, charge_id)
    await state.set_state(SurveyStates.last_name)
    await state.update_data(
        order_id=order_id,
        charge_id=charge_id,
        service_code=service.code if service else "",
        service_title=service.title if service else "",
        locale=locale,
    )
    await message.answer(t("ui.pay_success", locale))
    await message.answer(t("ui.ask_last_name", locale))
