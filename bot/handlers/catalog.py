"""Каталог услуг: список, карточка, запуск оплаты Telegram Stars."""

from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice

from bot import keyboards, texts
from core.db import session_scope
from core.repositories import create_order, get_or_create_user, get_service, list_active_services

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
        f"Цена: {service.price_stars}⭐"
    )
    await query.message.edit_text(
        text,
        reply_markup=keyboards.service_card_kb(service.id, service.price_stars),
        parse_mode="HTML",
    )
    await query.answer()


@router.callback_query(F.data.startswith("pay:"))
async def cb_pay(query: CallbackQuery) -> None:
    service_id = int(query.data.split(":")[1])
    async with session_scope() as session:
        service = await get_service(session, service_id)
        if service is None or not service.is_active:
            await query.answer("Услуга недоступна", show_alert=True)
            return
        user = await get_or_create_user(session, query.from_user.id, query.from_user.full_name)
        order = await create_order(session, user.id, service.id)
        order_id, title, price = order.id, service.title, service.price_stars

    # Telegram Stars: currency XTR, provider_token пустой. payload = order_id.
    await query.message.answer_invoice(
        title=texts.PAYMENT_TITLE,
        description=title,
        payload=str(order_id),
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=price)],
    )
    await query.answer()
