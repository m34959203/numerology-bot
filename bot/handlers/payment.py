"""Оплата через Telegram Stars (Этап 1).

Поток: send_invoice(XTR) -> pre_checkout_query(ok) -> successful_payment.
Идемпотентность: telegram_payment_charge_id уникален, один платёж = одна выдача.
"""

from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery

router = Router(name="payment")


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    # TODO(Этап 1): проверить, что услуга/заказ валидны, прежде чем подтверждать.
    await query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def on_successful_payment(message: Message) -> None:
    # TODO(Этап 1): записать платёж (telegram_payment_charge_id) в БД,
    # привязать к услуге/пользователю, запустить анкету. Защита от двойной выдачи.
    raise NotImplementedError("Этап 1: запись платежа и запуск анкеты")
