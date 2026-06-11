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

from bot import keyboards
from bot.catalog_data import format_price
from bot.config import settings
from bot.states.survey import SurveyStates
from core.db import session_scope
from core.i18n import t
from core.models import Order
from core.numerology.tariffs import spec_for
from core.repositories import (
    create_order,
    get_or_create_user,
    get_service,
    get_user_locale,
    list_active_services,
    record_payment,
)

logger = logging.getLogger(__name__)
router = Router(name="catalog")


def _svc_text(code: str, fallback: str, suffix: str, locale: str) -> str:
    """Локализованный заголовок/описание услуги по коду (fallback — из БД)."""
    key = f"svc.{code}.{suffix}"
    val = t(key, locale)
    return val if val != key else fallback


@router.callback_query(F.data == "menu:services")
async def cb_services(query: CallbackQuery) -> None:
    async with session_scope() as session:
        services = await list_active_services(session)
        locale = await get_user_locale(session, query.from_user.id)
    if not services:
        await query.answer(t("ui.catalog_empty", locale), show_alert=True)
        return
    await query.message.edit_text(
        t("ui.services_title", locale), reply_markup=keyboards.services_kb(services, locale)
    )
    await query.answer()


@router.callback_query(F.data.startswith("svc:"))
async def cb_service_card(query: CallbackQuery) -> None:
    service_id = int(query.data.split(":")[1])
    async with session_scope() as session:
        service = await get_service(session, service_id)
        locale = await get_user_locale(session, query.from_user.id)
    if service is None or not service.is_active:
        await query.answer(t("ui.service_unavailable", locale), show_alert=True)
        return
    spec = spec_for(service.code)
    contact_url = spec.contact_url if spec.manual else None
    title = _svc_text(service.code, service.title, "title", locale)
    desc = _svc_text(service.code, service.description, "desc", locale)
    text = (
        f"<b>{escape(title)}</b>\n\n"
        f"{escape(desc)}\n\n"
        f"{escape(t('ui.price', locale))}: {format_price(service.price_tenge)}"
    )
    await query.message.edit_text(
        text,
        reply_markup=keyboards.service_card_kb(
            service.id, service.price_tenge, contact_url, locale
        ),
        parse_mode="HTML",
    )
    await query.answer()


@router.callback_query(F.data.startswith("pay:"))
async def cb_pay(query: CallbackQuery, state: FSMContext) -> None:
    service_id = int(query.data.split(":")[1])
    async with session_scope() as session:
        service = await get_service(session, service_id)
        locale = await get_user_locale(session, query.from_user.id)
        if service is None or not service.is_active:
            await query.answer(t("ui.service_unavailable", locale), show_alert=True)
            return
        if spec_for(service.code).manual:
            # Ручные тарифы оплачиваются не в боте — клиента ведут к мастеру.
            await query.answer(t("ui.manual_at_master", locale), show_alert=True)
            return
        user = await get_or_create_user(session, query.from_user.id, query.from_user.full_name)
        order = await create_order(session, user.id, service.id)
        order_id, code, title, price_tenge, price_stars = (
            order.id,
            service.code,
            service.title,
            service.price_tenge,
            service.price_stars,
        )

    # Приём в TON (Crypto Pay) — приоритетно, если задан токен.
    if settings.crypto_pay_enabled:
        from bot.handlers.ton_payment import send_ton_invoice

        await send_ton_invoice(query, order_id, code, title, price_tenge, locale)
        return

    if settings.payment_imitation:
        await _imitate_payment(query, state, order_id, code, title, price_tenge, locale)
        return

    # Боевой режим: Telegram Stars (currency XTR, provider_token пустой). payload = order_id.
    await query.message.answer_invoice(
        title=t("ui.payment_title", locale),
        description=_svc_text(code, title, "title", locale),
        payload=str(order_id),
        currency="XTR",
        prices=[LabeledPrice(label=t("ui.payment_title", locale), amount=price_stars)],
    )
    await query.answer()


async def _imitate_payment(
    query: CallbackQuery,
    state: FSMContext,
    order_id: int,
    code: str,
    title: str,
    price_tenge: int,
    locale: str,
) -> None:
    """Имитация успешной оплаты: помечаем заказ оплаченным и запускаем анкету.

    Повторяет логику payment.on_successful_payment, но без реального платежа.
    charge_id синтетический (imitation-<order_id>) — идемпотентность сохраняется.
    """
    charge_id = f"imitation-{order_id}"
    async with session_scope() as session:
        payment = await record_payment(session, order_id, charge_id, price_tenge)
        if payment is None:
            await query.answer(t("ui.order_already_paid", locale), show_alert=True)
            return
        order = await session.get(Order, order_id)
        if order is not None:
            order.status = "paid"

    logger.info("ИМИТАЦИЯ оплаты order_id=%s charge_id=%s", order_id, charge_id)
    await state.set_state(SurveyStates.last_name)
    await state.update_data(
        order_id=order_id,
        charge_id=charge_id,
        service_code=code,
        service_title=title,
        locale=locale,
    )
    await query.message.answer(t("ui.pay_success_imitation", locale))
    await query.message.answer(t("ui.ask_last_name", locale))
    await query.answer()
