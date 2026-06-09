"""Соответствие анкеты входам Excel: даты родителей → кармические события,
девичья фамилия → её число; состав доп. шагов определяется тарифом.

Эталон — единственный заполненный пример книги (Ерофеева Ю.В., 20.02.1990,
мать 06.08.1971, отец 23.11.1970, девичья Миронова)."""

from __future__ import annotations

from datetime import date

from bot.handlers.survey import _flags
from core.numerology import PersonInput
from core.numerology.tariffs import report_for

REF = date(2026, 6, 6)
PERSON = PersonInput(
    "Ерофеева",
    "Юлия",
    "Владимировна",
    date(1990, 2, 20),
    mother_birth_date=date(1971, 8, 6),
    father_birth_date=date(1970, 11, 23),
    maiden_name="Миронова",
)


def test_flags_per_tariff():
    # (нужны родители, нужны пол+девичья)
    assert _flags({"service_code": "matrix_mini"}) == (True, True)
    assert _flags({"service_code": "matrix_full"}) == (True, True)
    assert _flags({"service_code": "forecast_1y"}) == (False, False)
    assert _flags({"service_code": "forecast_5y"}) == (False, False)
    # неизвестный код → полный разбор (безопасный максимум)
    assert _flags({}) == (True, True)


def test_parents_populate_karma_events():
    rep = report_for(PERSON, REF, "matrix_full")
    ke = rep["karma_events"]
    assert ke["first"] and ke["second"], "с датами родителей события не должны быть пустыми"
    assert "28" in ke["first"]["text"]  # эталон: возраст 28


def test_no_parents_empty_karma_events():
    bare = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))
    rep = report_for(bare, REF, "matrix_full")
    assert rep["karma_events"]["first"] is None
    assert rep["karma_events"]["second"] is None


def test_maiden_name_number():
    rep = report_for(PERSON, REF, "matrix_mini")
    assert rep["name"]["maiden_name"] == 3  # эталон ЕРОФЕЕВА…/МИРОНОВА: дев. = 3


def test_forecast_tariff_skips_name_and_karma():
    rep = report_for(PERSON, REF, "forecast_1y")
    assert "karma_events" not in rep
    assert "name" not in rep
