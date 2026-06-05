"""Сверка прогноза на 5 лет (Matr строки 29–33 → РАСЧЕТ) с эталоном книги."""

import json
from datetime import date
from pathlib import Path

from core.numerology import PersonInput
from core.numerology.matrix import compute_forecast

FIXTURES = Path(__file__).parent / "fixtures"


def test_forecast_matches_excel():
    data = json.loads((FIXTURES / "forecast_1990_02_20.json").read_text(encoding="utf-8"))
    person = PersonInput("", "", None, date.fromisoformat(data["input"]["birth_date"]))
    ref = date.fromisoformat(data["input"]["reference_date"])
    got = compute_forecast(person, ref)
    assert len(got) == len(data["expected"])
    for g, e in zip(got, data["expected"], strict=True):
        for key, exp in e.items():
            assert g[key] == exp, f"год {e['year']} {key}: получили {g[key]!r}, эталон {exp!r}"


def test_danger_age():
    from core.numerology.matrix import danger_age

    # ex1: солнце=0 на возрасте 25; жен. пример: нет опасного возраста
    assert danger_age(PersonInput("", "", None, date(2000, 1, 1)), date(2025, 7, 27)) == 25
    assert danger_age(PersonInput("", "", None, date(1990, 2, 20)), date(2026, 6, 6)) is None


def test_fate_years_contains_anchor():
    from core.numerology.matrix import fate_years

    # цепочка от 1990: первый якорь 1990+Σцифр=2009
    assert 2009 in fate_years(1990)
