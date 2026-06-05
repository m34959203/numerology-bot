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
