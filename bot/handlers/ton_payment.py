"""Приём оплаты в TON через Crypto Pay.

Поток: создать счёт (fiat=KZT → автоконвертация в TON) → отправить пользователю
кнопку-ссылку «Оплатить в TON» + «Проверить оплату» → по нажатию опросить статус
счёта; если paid — записать платёж (идемпотентно) и запустить анкету.

Вебхук не нужен: подтверждение через poll get_invoice по кнопке. send_ton_invoice
вызывается из catalog.cb_pay, когда задан CRYPTO_PAY_TOKEN.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.handlers.survey import begin_survey
from core.db import session_scope
from core.i18n import t
from core.models import Order
from core.payments import crypto_pay
from core.repositories import get_service, get_user_locale, record_payment

logger = logging.getLogger(__name__)
router = Router(name="ton_payment")


async def send_ton_invoice(
    query: CallbackQuery, order_id: int, code: str, title: str, price_tenge: int, locale: str
) -> None:
    """Создать счёт Crypto Pay и отправить пользователю кнопки оплаты/проверки."""
    try:
        inv = await crypto_pay.create_invoice(
            amount=str(price_tenge),
            payload=str(order_id),
            description=title,
            currency_type="fiat",
            fiat=settings.crypto_pay_fiat,
            accepted_assets=settings.crypto_pay_asset,
        )
    except Exception:
        logger.exception("Crypto Pay createInvoice сбой order_id=%s", order_id)
        await query.message.answer(t("ui.ton_invoice_error", locale))
        await query.answer()
        return

    invoice_id = inv["invoice_id"]
    pay_url = crypto_pay.invoice_pay_url(inv)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("ui.btn_pay_open", locale), url=pay_url)],
            [
                InlineKeyboardButton(
                    text=t("ui.btn_check_payment", locale),
                    callback_data=f"ton:check:{invoice_id}",
                )
            ],
        ]
    )
    await query.message.answer(
        t("ui.ton_invoice", locale).format(amount=price_tenge, fiat=settings.crypto_pay_fiat),
        reply_markup=kb,
    )
    await query.answer()


@router.callback_query(F.data.startswith("ton:check:"))
async def cb_check(query: CallbackQuery, state: FSMContext) -> None:
    invoice_id = query.data.split(":")[2]
    async with session_scope() as session:
        locale = await get_user_locale(session, query.from_user.id)

    try:
        inv = await crypto_pay.get_invoice(invoice_id)
    except Exception:
        logger.exception("Crypto Pay getInvoice сбой invoice_id=%s", invoice_id)
        await query.answer(t("ui.ton_not_paid", locale), show_alert=True)
        return

    if inv is None:
        await query.answer(t("ui.ton_expired", locale), show_alert=True)
        return
    if inv.get("status") != "paid":
        await query.answer(t("ui.ton_not_paid", locale), show_alert=True)
        return

    # Оплачено — записываем платёж (идемпотентно) и запускаем анкету.
    order_id = int(inv["payload"])
    charge_id = f"cryptopay-{invoice_id}"
    amount = int(float(inv.get("amount", 0)))
    async with session_scope() as session:
        payment = await record_payment(session, order_id, charge_id, amount)
        if payment is None:
            # уже обработано (анкета запущена ранее) — не дублируем
            await query.answer(t("ui.order_already_paid", locale), show_alert=True)
            return
        order = await session.get(Order, order_id)
        if order is not None:
            order.status = "paid"
        service = await get_service(session, order.service_id) if order else None
        code = service.code if service else ""
        title = service.title if service else ""

    logger.info("TON оплата принята order_id=%s invoice_id=%s", order_id, invoice_id)
    await query.answer()
    await query.message.answer(t("ui.pay_success", locale))
    await begin_survey(
        query.message,
        state,
        order_id=order_id,
        charge_id=charge_id,
        service_code=code,
        service_title=title,
        locale=locale,
    )
