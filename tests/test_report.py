"""Сверка сборки итогового отчёта с Excel (лист РАСЧЕТ)."""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.report import build_report

PERSON = PersonInput("Иванов", "Иван", "Иванович", date(1990, 5, 15))


def test_report_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        build_report(PERSON)
