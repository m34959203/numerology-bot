"""FSM-маршрутизация анкеты: условные шаги по тарифу, skip, гендер-развилка,
устойчивость cb_confirm к сбоям."""

from __future__ import annotations

from unittest.mock import AsyncMock

from bot import texts
from bot.handlers import survey
from bot.states.survey import SurveyStates
from core import repositories as repo
from tests.conftest import fake_message, fake_query, make_state


async def _state_at(service_code: str) -> object:
    """FSMContext в состоянии birth_date с базовыми полями и кодом услуги."""
    st = make_state()
    await st.set_state(SurveyStates.birth_date)
    await st.update_data(
        service_code=service_code,
        last_name="Ерофеева",
        first_name="Юлия",
        middle_name="В",
        birth_date="1990-02-20",
    )
    return st


async def test_forecast_tariff_goes_straight_to_confirm():
    st = await _state_at("forecast_1y")
    await survey.step_birth_date(fake_message("20.02.1990"), st)
    assert await st.get_state() == SurveyStates.confirm


async def test_finance_tariff_asks_mother_first():
    # «Финансовый прогноз»: заказчик требует имя родителей и год рождения.
    st = await _state_at("finance_1y")
    msg = fake_message("20.02.1990")
    await survey.step_birth_date(msg, st)
    assert await st.get_state() == SurveyStates.mother_birth_date
    assert msg.answer.await_args.args[0] == texts.ASK_MOTHER_BD


async def test_mother_stored_and_advances_to_father():
    st = await _state_at("finance_1y")
    await survey.step_birth_date(fake_message("20.02.1990"), st)
    await survey.step_mother_birth_date(fake_message("06.08.1971"), st)
    assert (await st.get_data())["mother_birth_date"] == "1971-08-06"
    assert await st.get_state() == SurveyStates.father_birth_date


async def test_skip_mother_then_skip_father_reaches_gender():
    # Неизвестный код → DEFAULT_SPEC (безопасный максимум: родители + имя/пол).
    st = await _state_at("unknown_tariff")
    await survey.step_birth_date(fake_message("20.02.1990"), st)
    await survey.skip_mother(fake_query("survey:skip"), st)
    assert await st.get_state() == SurveyStates.father_birth_date
    await survey.skip_father(fake_query("survey:skip"), st)
    # DEFAULT_SPEC требует имя → спрашиваем пол
    assert await st.get_state() == SurveyStates.gender


async def test_gender_female_asks_maiden_male_confirms():
    st = await _state_at("matrix_mini")
    await st.set_state(SurveyStates.gender)
    await survey.cb_gender(fake_query("survey:gender:f"), st)
    assert await st.get_state() == SurveyStates.maiden_name
    assert (await st.get_data())["gender"] == "f"

    st2 = await _state_at("matrix_mini")
    await st2.set_state(SurveyStates.gender)
    await survey.cb_gender(fake_query("survey:gender:m"), st2)
    assert await st2.get_state() == SurveyStates.confirm


async def test_skip_maiden_confirms():
    st = await _state_at("matrix_mini")
    await st.set_state(SurveyStates.maiden_name)
    await survey.skip_maiden(fake_query("survey:skip"), st)
    assert await st.get_state() == SurveyStates.confirm


async def test_confirm_calc_failure_keeps_confirm_state(monkeypatch):
    st = await _state_at("matrix_full")
    await st.set_state(SurveyStates.confirm)
    await st.update_data(order_id=1, birth_date="1990-02-20")
    monkeypatch.setattr(
        survey, "report_for", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    q = fake_query("survey:confirm")
    await survey.cb_confirm(q, st)
    # остаёмся в confirm для повтора, показан CALC_ERROR
    assert await st.get_state() == SurveyStates.confirm
    assert any(c.args and c.args[0] == texts.CALC_ERROR for c in q.message.answer.await_args_list)


async def test_confirm_success_clears_state_and_saves(test_db, monkeypatch):
    # реальный заказ в подменённой БД
    async with test_db() as s:
        user = await repo.get_or_create_user(s, telegram_id=1, name="Тест")
        await repo.seed_services(
            s,
            [{"code": "matrix_full", "title": "Полный", "description": "x", "price_tenge": 10000}],
        )
        svc = (await repo.list_active_services(s))[0]
        order = await repo.create_order(s, user.id, svc.id)
        await s.commit()
        order_id = order.id

    st = await _state_at("matrix_full")
    await st.set_state(SurveyStates.confirm)
    await st.update_data(order_id=order_id, birth_date="1990-02-20")
    monkeypatch.setattr(survey, "report_for", lambda *a, **k: {"calculations": {}})
    monkeypatch.setattr(survey, "deliver_report", AsyncMock())

    q = fake_query("survey:confirm")
    await survey.cb_confirm(q, st)

    assert await st.get_state() is None  # state очищен при успехе
    survey.deliver_report.assert_awaited_once()
    async with test_db() as s:
        assert await repo.get_result(s, 1) is not None or await repo.get_survey(s, order_id)
