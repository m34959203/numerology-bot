"""Дифференциация тарифов по полям: какие атомарные блоки попадают в отчёт.

Состав блоков — продуктовое решение по спецификации заказчика (не Excel-истина),
поэтому проверяем выбор атомов (_fields) и поведение рендера, а не значения
расчётов (они покрыты test_report).
"""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.report import ALL_SECTIONS, build_report
from core.numerology.tariffs import ALL_FIELDS, TARIFFS, report_for, spec_for
from core.pdf import fonts_available
from core.render import render_report

PERSON = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))
REF = date(2026, 6, 6)


def _fields(code: str | None) -> set[str]:
    return set(report_for(PERSON, REF, code)["_fields"])


def _sections(code: str | None) -> set[str]:
    return {k for k in report_for(PERSON, REF, code) if k != "_fields"}


def test_full_report_has_all_sections():
    rep = build_report(PERSON, REF)
    assert set(rep) == set(ALL_SECTIONS)


def test_mini_is_personality_and_days():
    # Заказчик: психоматрица, ЧЖП, персональный год, дни, код поведения, сознание.
    assert _fields("matrix_mini") == {
        "psychomatrix",
        "life_path",
        "personal_year",
        "biorhythm_days",
        "behavior_code",
        "consciousness",
    }
    assert _sections("matrix_mini") == {"psychomatrix", "days", "moon_sun"}
    assert "calculations" not in _sections("matrix_mini")


def test_forecast_1y_has_no_multiyear_table():
    fields = _fields("forecast_1y")
    assert "forecast" not in fields  # годовая динамика — это 5-летний тариф
    assert {"life_path", "life_code", "behavior_code", "energy_trend", "biorhythm_days"} <= fields
    assert "forecast" not in _sections("forecast_1y")
    assert "psychomatrix" not in fields  # сетки психоматрицы в прогнозе нет


def test_forecast_5y_full_horizon():
    rep = report_for(PERSON, REF, "forecast_5y")
    assert "forecast" in rep["_fields"]
    assert len(rep["forecast"]) == 5


def test_matrix_full_has_spec_fields():
    fields = _fields("matrix_full")
    for atom in ("psychomatrix", "human_code", "finance_code", "soul_number", "forecast"):
        assert atom in fields


def test_finance_1y_is_money_only():
    assert _fields("finance_1y") == {"finance_code", "moon_sun_monthly"}
    assert _sections("finance_1y") == {"calculations", "moon_sun"}
    assert spec_for("finance_1y").needs_parents is True


def test_unknown_code_falls_back_to_full_fields():
    assert _fields("no_such_tariff") == set(ALL_FIELDS)
    assert _fields(None) == set(ALL_FIELDS)


def test_manual_tariffs_route_to_master():
    for code in ("children", "compatibility"):
        spec = spec_for(code)
        assert spec.manual is True
        assert spec.contact_url and spec.contact_url.startswith("https://t.me/")
        assert spec.fields == frozenset()  # авто-расчёта нет


def test_every_catalog_code_has_a_spec():
    from bot.catalog_data import DEFAULT_SERVICES

    for svc in DEFAULT_SERVICES:
        assert svc["code"] in TARIFFS, f"нет TariffSpec для {svc['code']}"


def test_render_forecast_1y_blocks():
    text = render_report(report_for(PERSON, REF, "forecast_1y"), "Ерофеева Юлия", PERSON.birth_date)
    assert "ЛУНА И СОЛНЦЕ" in text
    assert "Энергетический потенциал" in text
    assert "ПЕРСОНАЛЬНОЕ ЧИСЛО ГОДА" in text
    assert "ПСИХОМАТРИЦА" not in text  # только скаляры, без сетки качеств
    assert "ПРОГНОЗ НА" not in text  # многолетней таблицы нет


def test_render_mini_has_psychomatrix_no_forecast():
    text = render_report(report_for(PERSON, REF, "matrix_mini"), "Ерофеева Юлия", PERSON.birth_date)
    assert "ПСИХОМАТРИЦА" in text
    assert "ПРОГНОЗ" not in text
    assert "ЛУНА И СОЛНЦЕ" not in text  # помесячного блока в мини нет
    assert "ПЕРСОНАЛЬНОЕ ЧИСЛО ГОДА" in text


def test_render_5y_title():
    text = render_report(report_for(PERSON, REF, "forecast_5y"), "Ерофеева Юлия", PERSON.birth_date)
    assert "ПРОГНОЗ НА 5 ЛЕТ" in text


def test_render_finance_is_focused():
    text = render_report(report_for(PERSON, REF, "finance_1y"), "Ерофеева Юлия", PERSON.birth_date)
    assert "Финансовый код удачи" in text
    assert "ЛУНА И СОЛНЦЕ" in text
    assert "ПСИХОМАТРИЦА" not in text
    assert "Опасный возраст" not in text


def test_full_report_labels_life_path_aspects():
    # ЧЖП выводится по полям заказчика (предназначение/профессии/талисман/цвет),
    # описание привязано к значению (лукап из life_path.json). Молодой — чтобы
    # показался и блок «Число души».
    young = PersonInput("Иван", "Пётр", "Сергеевич", date(2005, 3, 14))
    text = render_report(report_for(young, REF, "matrix_full"), "Иван Пётр", young.birth_date)
    for cap in ("Предназначение", "Недостатки", "Профессии", "Цвет удачи", "Талисман"):
        assert f"• {cap}:" in text, f"нет аспекта ЧЖП «{cap}»"
    for cap in ("Счастливые камни", "Болезни", "Рекомендации"):
        assert f"• {cap}:" in text, f"нет аспекта числа души «{cap}»"


def test_full_report_shows_two_codes_by_age():
    # Кодировка «до/после 35» (лист 18): 1-код = human_code (calc!E18&E19),
    # 2-код = second_code (calc!E20&E21); оба с описанием из таблицы кодировок.
    rep = report_for(PERSON, REF, "matrix_full")
    c = rep["calculations"]
    assert c["human_code"] == "235" and c["second_code"] == "1910"  # эталон Ерофеева
    text = render_report(rep, "Ерофеева Юлия", PERSON.birth_date)
    assert "До 35 лет — код 235" in text
    assert "После 35 лет — код 1910" in text


def test_pdf_partial_report_builds():
    pytest.importorskip("reportlab")
    if not fonts_available():
        pytest.skip("нет кириллического TTF-шрифта (бандл PT или fonts-dejavu-core)")
    from core.pdf import build_report_pdf

    rep = report_for(PERSON, REF, "matrix_mini")
    data = build_report_pdf(rep, "Ерофеева Юлия Владимировна", PERSON.birth_date)
    assert data[:5] == b"%PDF-"
