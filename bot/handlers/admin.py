"""Админ-команды: статистика, возврат звёзд, повторная выдача.

Доступ — только telegram_id из settings.admin_id_list.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config import settings
from core.db import session_scope
from core.models import Order, Payment, Result, User
from core.repositories import mark_refunded

logger = logging.getLogger(__name__)
router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_list


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    async with session_scope() as session:
        users = await session.scalar(select(func.count(User.id)))
        orders = await session.scalar(select(func.count(Order.id)))
        paid = await session.scalar(select(func.count(Payment.id)).where(Payment.status == "paid"))
        refunded = await session.scalar(
            select(func.count(Payment.id)).where(Payment.status == "refunded")
        )
        results = await session.scalar(select(func.count(Result.id)))
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_stars), 0)).where(Payment.status == "paid")
        )
    await message.answer(
        f"📊 Статистика\n"
        f"Пользователей: {users}\n"
        f"Заказов: {orders}\n"
        f"Оплачено: {paid} (возвращено: {refunded})\n"
        f"Выдано расчётов: {results}\n"
        f"Доход: {revenue}⭐\n\n"
        f"Возврат: /refund <charge_id>"
    )


@router.message(Command("refund"))
async def cmd_refund(message: Message, command: CommandObject, bot: Bot) -> None:
    if not _is_admin(message.from_user.id):
        return
    charge_id = (command.args or "").strip()
    if not charge_id:
        await message.answer("Использование: /refund <telegram_payment_charge_id>")
        return

    async with session_scope() as session:
        payment = await session.scalar(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )
        if payment is None:
            await message.answer("Платёж не найден.")
            return
        order = await session.get(Order, payment.order_id)
        user = await session.get(User, order.user_id) if order else None
        payer_tg = user.telegram_id if user else None

    if payer_tg is None:
        await message.answer("Не найден плательщик для возврата.")
        return
    try:
        await bot.refund_star_payment(user_id=payer_tg, telegram_payment_charge_id=charge_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("Ошибка возврата charge_id=%s", charge_id)
        await message.answer(f"Ошибка возврата: {e}")
        return
    async with session_scope() as session:
        await mark_refunded(session, charge_id)
    await message.answer(f"Возврат выполнен: {charge_id}")
    logger.info("Возврат звёзд charge_id=%s admin=%s", charge_id, message.from_user.id)
