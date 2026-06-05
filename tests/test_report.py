"""Сборка отчёта (Этап 2: психоматрица + биоритмы) с трактовками."""

from datetime import date

from core.numerology import PersonInput
from core.numerology.report import build_report

PERSON = PersonInput("", "", None, date(2000, 1, 1))


def test_report_psychomatrix_texts_match_excel():
    rep = build_report(PERSON, date(2025, 7, 27))
    q = {row["label"]: row for row in rep["psychomatrix"]["qualities"]}

    # Характер 11 -> текст про «две единицы» (VLOOKUP текст!B3:C10)
    assert q["Характер"]["value"] == 11
    assert "две единиц" in q["Характер"]["text"]
    # Здоровье 44 -> текст про «две или более четверки»
    assert q["Здоровье"]["value"] == 44
    assert "четвер" in q["Здоровье"]["text"]
    # Везение «нет» -> текст про пустой сектор
    assert q["Везение"]["value"] == 0
    assert "устой сектор везение" in q["Везение"]["text"]


def test_report_scalars():
    rep = build_report(PERSON, date(2025, 7, 27))
    s = {row["label"]: row for row in rep["psychomatrix"]["scalars"]}
    assert s["Код поведения"]["value"] == "22.12-20.01 код Карьеры"
    assert "карьерный рост" in s["Код поведения"]["text"]
    # ЧЖП и число души — мультиаспектные (список абзацев)
    assert isinstance(s["Число жизненного пути (ЧЖП)"]["text"], list)
    assert isinstance(s["Число души"]["text"], list)


def test_report_days_present():
    rep = build_report(PERSON, date(2025, 7, 27))
    assert rep["days"]["favorable"][0] == "2025-08-18"
    assert len(rep["days"]["critical"]) == 5


def test_report_calculations_and_forecast():
    rep = build_report(PERSON, date(2025, 7, 27))
    assert rep["calculations"]["human_code"] == "44"
    assert rep["calculations"]["life_code"] == "200000"
    assert len(rep["forecast"]) == 5
    assert rep["forecast"][0]["age"] == 25
    assert rep["forecast"][0]["personal_year"] == 2
