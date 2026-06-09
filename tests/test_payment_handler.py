"""bot.handlers.payment: pre_checkout-проверка заказа и идемпотентность выдачи."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import payment
from bot.states.survey import SurveyStates
from core import repositories as repo
from tests.conftest import fake_message, make_state


async def _make_order(test_db) -> int:
    async with test_db() as s:
        user = await repo.get_or_create_user(s, telegram_id=1, name="Тест")
        await repo.seed_services(
            s,
            [{"code": "matrix_full", "title": "Полный", "description": "x", "price_tenge": 10000}],
        )
        svc = (await repo.list_active_services(s))[0]
        order = await repo.create_order(s, user.id, svc.id)
        await s.commit()
        return order.id


def _precheckout(payload: str):
    q = MagicMock(name="PreCheckoutQuery")
    q.invoice_payload = payload
    q.answer = AsyncMock()
    return q


async def test_pre_checkout_ok_for_existing_order(test_db):
    order_id = await _make_order(test_db)
    q = _precheckout(str(order_id))
    await payment.on_pre_checkout(q)
    assert q.answer.await_args.kwargs["ok"] is True


async def test_pre_checkout_rejects_unknown_order(test_db):
    await _make_order(test_db)
    q = _precheckout("999999")
    await payment.on_pre_checkout(q)
    assert q.answer.await_args.kwargs["ok"] is False


async def test_pre_checkout_rejects_bad_payload(test_db):
    q = _precheckout("not-an-int")
    await payment.on_pre_checkout(q)
    assert q.answer.await_args.kwargs["ok"] is False


async def test_successful_payment_starts_survey_then_idempotent(test_db):
    order_id = await _make_order(test_db)
    sp = SimpleNamespace(
        invoice_payload=str(order_id),
        telegram_payment_charge_id="charge-1",
        total_amount=100,
    )
    msg = fake_message(successful_payment=sp)
    st = make_state()

    await payment.on_successful_payment(msg, st)
    assert await st.get_state() == SurveyStates.last_name
    assert msg.answer.await_count == 2  # PAY_SUCCESS + ASK_LAST_NAME

    # повтор того же charge_id → ранний выход, состояние не выставляется заново
    msg2 = fake_message(successful_payment=sp)
    st2 = make_state()
    await payment.on_successful_payment(msg2, st2)
    assert await st2.get_state() is None
    msg2.answer.assert_not_awaited()
