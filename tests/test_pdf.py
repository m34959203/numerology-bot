"""Генерация PDF-отчёта (пропускается, если нет кириллического шрифта)."""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.report import build_report


def test_build_report_pdf():
    pytest.importorskip("reportlab")
    from core.pdf import _FONT_CANDIDATES, _find_font, build_report_pdf

    if _find_font(_FONT_CANDIDATES) is None:
        pytest.skip("нет кириллического TTF-шрифта (fonts-dejavu-core)")

    p = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))
    report = build_report(p, date(2026, 6, 6))
    data = build_report_pdf(report, "Ерофеева Юлия Владимировна", p.birth_date)
    assert data[:5] == b"%PDF-"
    assert len(data) > 3000  # непустой содержательный документ
