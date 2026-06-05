"""Сверка помесячной Луны/Солнца и ЧПГ/ЧПМ/ЧПД с эталоном книги."""

import json
from datetime import date
from pathlib import Path

from core.numerology import PersonInput
from core.numerology.moon_sun import compute_monthly_moon_sun, compute_personal_numbers

FIXTURES = Path(__file__).parent / "fixtures"


def _data():
    return json.loads((FIXTURES / "moon_sun_1990_02_20.json").read_text(encoding="utf-8"))


def _person():
    d = _data()
    return PersonInput("", "", None, date.fromisoformat(d["input"]["birth_date"]))


def test_monthly_moon_sun_matches_excel():
    d = _data()
    ref = date.fromisoformat(d["input"]["reference_date"])
    months = compute_monthly_moon_sun(_person(), ref)
    assert [m["value"] for m in months] == d["monthly_values"]
    # тексты определены (лукап по коду месяца)
    assert all(m["text"] for m in months)


def test_personal_numbers_match_excel():
    d = _data()
    ref = date.fromisoformat(d["input"]["reference_date"])
    p = compute_personal_numbers(_person(), ref)
    for key, exp in d["personal"].items():
        assert p[key] == exp, f"{key}: получили {p[key]!r}, эталон {exp!r}"
    assert p["combo_title"] and p["combo_text"]
    assert p["personal_month_text"] and p["personal_day_text"]
