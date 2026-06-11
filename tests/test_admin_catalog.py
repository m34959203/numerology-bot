"""bot.handlers.admin (гейт + статистика) и catalog (имитация vs боевой Stars)."""

from __future__ import annotations

from bot.config import settings
from bot.handlers import admin, catalog
from bot.states.survey import SurveyStates
from core import repositories as repo
from tests.conftest import fake_message, fake_query, make_state


# --- admin ---------------------------------------------------------------
def test_is_admin(monkeypatch):
    monkeypatch.setattr(settings, "admin_ids", "123,456")
    assert admin._is_admin(123) and admin._is_admin(456)
    assert not admin._is_admin(999)


async def test_admin_command_ignored_for_non_admin(monkeypatch):
    monkeypatch.setattr(settings, "admin_ids", "123")
    msg = fake_message("/admin", user_id=999)
    await admin.cmd_admin(msg)
    msg.answer.assert_not_awaited()


async def test_admin_command_shows_stats(test_db, monkeypatch):
    monkeypatch.setattr(settings, "admin_ids", "1")
    msg = fake_message("/admin", user_id=1)
    await admin.cmd_admin(msg)
    msg.answer.assert_awaited_once()
    assert "Статистика" in msg.answer.await_args.args[0]


# --- catalog -------------------------------------------------------------
async def _seed_service(test_db) -> int:
    async with test_db() as s:
        await repo.seed_services(
            s,
            [{"code": "matrix_full", "title": "Полный", "description": "x", "price_tenge": 10000}],
        )
        svc = (await repo.list_active_services(s))[0]
        await s.commit()
        return svc.id


async def test_pay_imitation_starts_survey(test_db, monkeypatch):
    monkeypatch.setattr(settings, "payment_imitation", True)
    monkeypatch.setattr(settings, "crypto_pay_token", "")  # TON отключён в этом тесте
    svc_id = await _seed_service(test_db)
    q = fake_query(f"pay:{svc_id}")
    st = make_state()
    await catalog.cb_pay(q, st)
    assert await st.get_state() == SurveyStates.last_name
    # имитация шлёт PAY_SUCCESS_IMITATION + ASK_LAST_NAME, без инвойса
    assert q.message.answer.await_count == 2
    q.message.answer_invoice.assert_not_awaited()


async def test_pay_real_mode_sends_invoice(test_db, monkeypatch):
    monkeypatch.setattr(settings, "payment_imitation", False)
    monkeypatch.setattr(settings, "crypto_pay_token", "")  # TON отключён в этом тесте
    # боевой режим использует price_stars
    async with test_db() as s:
        await repo.seed_services(
            s,
            [
                {
                    "code": "matrix_full",
                    "title": "Полный",
                    "description": "x",
                    "price_tenge": 10000,
                    "price_stars": 100,
                }
            ],
        )
        svc = (await repo.list_active_services(s))[0]
        await s.commit()
        svc_id = svc.id

    q = fake_query(f"pay:{svc_id}")
    st = make_state()
    await catalog.cb_pay(q, st)
    q.message.answer_invoice.assert_awaited_once()
    assert await st.get_state() is None  # анкета стартует только после оплаты
