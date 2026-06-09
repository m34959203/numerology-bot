"""Генерация PDF-отчёта (пропускается, если нет кириллического шрифта)."""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.report import build_report


def test_build_report_pdf():
    pytest.importorskip("reportlab")
    from core.pdf import build_report_pdf, fonts_available

    if not fonts_available():
        pytest.skip("нет кириллического TTF-шрифта (бандл PT или fonts-dejavu-core)")

    p = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))
    report = build_report(p, date(2026, 6, 6))
    data = build_report_pdf(report, "Ерофеева Юлия Владимировна", p.birth_date)
    assert data[:5] == b"%PDF-"
    assert len(data) > 3000  # непустой содержательный документ
