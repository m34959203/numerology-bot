"""Прогноз на выбранную дату: ЧПД + трактовка + статус биоритма; парсинг даты."""

from __future__ import annotations

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.daily import daily_forecast
from core.numerology.moon_sun import compute_personal_numbers
from core.render import render_daily
from core.validators import ValidationError, parse_target_date

PERSON = PersonInput("—", "—", "—", date(1990, 2, 20))


def test_daily_matches_personal_numbers():
    # ЧПД дня = compute_personal_numbers на ту же дату (единый движок).
    target = date(2026, 6, 10)
    fc = daily_forecast(PERSON, target)
    pn = compute_personal_numbers(PERSON, target)
    assert fc["personal_day"] == pn["personal_day"]
    assert fc["personal_day_text"] == pn["personal_day_text"]
    assert fc["biorhythm"] in {"traumatic", "critical", "favorable", "ordinary"}
    # биоритм-циклы дня (в процентах) присутствуют
    assert set(fc["biorhythm_cycles"]) == {"physical", "emotional", "intellectual"}


def test_daily_changes_by_date():
    a = daily_forecast(PERSON, date(2026, 6, 10))
    b = daily_forecast(PERSON, date(2026, 6, 11))
    assert a["personal_day"] != b["personal_day"] or a["date"] != b["date"]


def test_daily_differs_for_dates_9_apart():
    # Дни через 9 дают одинаковый ЧПД (mod-9), но прогноз НЕ должен быть идентичным:
    # биоритм-циклы дня различают их (регресс на жалобу «пишет одно и то же»).
    repro = PersonInput("—", "—", "—", date(1994, 5, 28))
    a = render_daily(daily_forecast(repro, date(2026, 6, 11)))
    b = render_daily(daily_forecast(repro, date(2026, 6, 2)))
    assert a != b


def test_render_daily_has_key_blocks():
    text = render_daily(daily_forecast(PERSON, date(2026, 6, 10)), "Юлия")
    assert "ПРОГНОЗ НА ДЕНЬ" in text
    assert "ЧПД" in text
    assert "Биоритм дня" in text


def test_parse_target_date_allows_future():
    # для прогноза будущая дата допустима (в отличие от даты рождения)
    assert parse_target_date("25.12.2030") == date(2030, 12, 25)


def test_parse_target_date_rejects_garbage():
    with pytest.raises(ValidationError):
        parse_target_date("не дата")
    with pytest.raises(ValidationError):
        parse_target_date("31.02.2026")
