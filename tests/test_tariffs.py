"""Дифференциация тарифов по контенту: какие секции попадают в отчёт.

Состав секций — не источник истины Excel (это продуктовое решение), поэтому
проверяем именно выбор блоков, а не значения расчётов (они покрыты test_report).
"""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.report import ALL_SECTIONS, build_report
from core.numerology.tariffs import TARIFFS, report_for
from core.pdf import fonts_available
from core.render import render_report

PERSON = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))
REF = date(2026, 6, 6)


def test_full_report_has_all_sections():
    rep = build_report(PERSON, REF)
    assert set(rep) == set(ALL_SECTIONS)


def test_mini_is_personality_only():
    rep = report_for(PERSON, REF, "matrix_mini")
    assert set(rep) == {"calculations", "psychomatrix", "name", "karma_events"}
    # без временных блоков
    assert "forecast" not in rep and "days" not in rep and "moon_sun" not in rep


def test_forecast_1y_single_year():
    rep = report_for(PERSON, REF, "forecast_1y")
    assert set(rep) == {"calculations", "days", "moon_sun", "forecast"}
    assert len(rep["forecast"]) == 1
    # без психоматрицы (это премиум полного разбора)
    assert "psychomatrix" not in rep


def test_forecast_5y_full_horizon():
    rep = report_for(PERSON, REF, "forecast_5y")
    assert set(rep) == {"calculations", "days", "moon_sun", "forecast"}
    assert len(rep["forecast"]) == 5
    assert "psychomatrix" not in rep


def test_matrix_full_is_everything():
    assert set(report_for(PERSON, REF, "matrix_full")) == set(ALL_SECTIONS)


def test_unknown_code_falls_back_to_full():
    assert set(report_for(PERSON, REF, "no_such_tariff")) == set(ALL_SECTIONS)
    assert set(report_for(PERSON, REF, None)) == set(ALL_SECTIONS)


def test_compatibility_fallback_full_until_methodology():
    # До методики заказчика совместимость = полный однопользовательский разбор.
    assert set(report_for(PERSON, REF, "compatibility")) == set(ALL_SECTIONS)


def test_every_catalog_code_has_a_spec():
    # Все коды из каталога должны быть описаны (иначе тихий fallback на full).
    from bot.catalog_data import DEFAULT_SERVICES

    for svc in DEFAULT_SERVICES:
        assert svc["code"] in TARIFFS, f"нет TariffSpec для {svc['code']}"


def test_render_partial_report_omits_absent_sections():
    rep = report_for(PERSON, REF, "forecast_1y")
    text = render_report(rep, "Ерофеева Юлия Владимировна", PERSON.birth_date)
    assert "ПРОГНОЗ НА ГОД" in text
    assert "ЛУНА И СОЛНЦЕ" in text
    # психоматрицы в прогнозном тарифе нет — заголовок не должен появиться
    assert "ПСИХОМАТРИЦА" not in text


def test_render_mini_has_psychomatrix_no_forecast():
    rep = report_for(PERSON, REF, "matrix_mini")
    text = render_report(rep, "Ерофеева Юлия Владимировна", PERSON.birth_date)
    assert "ПСИХОМАТРИЦА" in text
    assert "ПРОГНОЗ" not in text
    assert "ЛУНА И СОЛНЦЕ" not in text


def test_render_5y_title():
    rep = report_for(PERSON, REF, "forecast_5y")
    text = render_report(rep, "Ерофеева Юлия Владимировна", PERSON.birth_date)
    assert "ПРОГНОЗ НА 5 ЛЕТ" in text


def test_pdf_partial_report_builds():
    pytest.importorskip("reportlab")
    if not fonts_available():
        pytest.skip("нет кириллического TTF-шрифта (бандл PT или fonts-dejavu-core)")
    from core.pdf import build_report_pdf

    rep = report_for(PERSON, REF, "matrix_mini")
    data = build_report_pdf(rep, "Ерофеева Юлия Владимировна", PERSON.birth_date)
    assert data[:5] == b"%PDF-"
