"""Приём оплаты в TON (Crypto Pay): роутинг из cb_pay + проверка статуса."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from bot.config import settings
from bot.handlers import catalog, ton_payment
from bot.states.survey import SurveyStates
from core import repositories as repo
from tests.conftest import fake_query, make_state


async def _seed(test_db) -> int:
    async with test_db() as s:
        await repo.seed_services(
            s,
            [
                {
                    "code": "forecast_1y",
                    "title": "Прогноз на 1 год",
                    "description": "x",
                    "price_tenge": 3000,
                    "price_stars": 30,
                }
            ],
        )
        svc_id = (await repo.list_active_services(s))[0].id
        await s.commit()
        return svc_id


async def _seed_order(test_db, svc_id: int) -> int:
    async with test_db() as s:
        user = await repo.get_or_create_user(s, 1, "T")
        order = await repo.create_order(s, user.id, svc_id)
        oid = order.id
        await s.commit()
        return oid


async def test_cb_pay_routes_to_ton_when_enabled(test_db, monkeypatch):
    monkeypatch.setattr(settings, "crypto_pay_token", "12345:TESTTOKEN")
    svc_id = await _seed(test_db)
    q = fake_query(f"pay:{svc_id}")
    invoice = {"invoice_id": 999, "bot_invoice_url": "https://t.me/CryptoTestnetBot?start=x"}
    with patch("core.payments.crypto_pay.create_invoice", AsyncMock(return_value=invoice)) as ci:
        await catalog.cb_pay(q, make_state())
    ci.assert_awaited_once()
    # отправлено сообщение со счётом, инвойс Stars не слался
    q.message.answer.assert_awaited()
    q.message.answer_invoice.assert_not_awaited()


async def test_cb_check_not_paid(test_db, monkeypatch):
    monkeypatch.setattr(settings, "crypto_pay_token", "12345:TESTTOKEN")
    q = fake_query("ton:check:999")
    with patch(
        "core.payments.crypto_pay.get_invoice", AsyncMock(return_value={"status": "active"})
    ):
        await ton_payment.cb_check(q, make_state())
    # не оплачено → alert, анкета не стартует
    q.answer.assert_awaited()
    q.message.answer.assert_not_awaited()


async def test_cb_check_paid_starts_survey(test_db, monkeypatch):
    monkeypatch.setattr(settings, "crypto_pay_token", "12345:TESTTOKEN")
    svc_id = await _seed(test_db)
    order_id = await _seed_order(test_db, svc_id)
    q = fake_query("ton:check:777")
    paid = {"status": "paid", "payload": str(order_id), "amount": "3000"}
    st = make_state()
    with patch("core.payments.crypto_pay.get_invoice", AsyncMock(return_value=paid)):
        await ton_payment.cb_check(q, st)
    # платёж записан, анкета запущена
    assert await st.get_state() == SurveyStates.last_name
    async with test_db() as s:
        assert await repo.payment_exists(s, "cryptopay-777")


async def test_cb_check_idempotent(test_db, monkeypatch):
    monkeypatch.setattr(settings, "crypto_pay_token", "12345:TESTTOKEN")
    svc_id = await _seed(test_db)
    order_id = await _seed_order(test_db, svc_id)
    paid = {"status": "paid", "payload": str(order_id), "amount": "3000"}
    with patch("core.payments.crypto_pay.get_invoice", AsyncMock(return_value=paid)):
        # повторная проверка того же счёта не должна падать (идемпотентно)
        await ton_payment.cb_check(fake_query("ton:check:555"), make_state())
        await ton_payment.cb_check(fake_query("ton:check:555"), make_state())
    async with test_db() as s:
        assert await repo.payment_exists(s, "cryptopay-555")
