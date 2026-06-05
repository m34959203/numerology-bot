"""Сверка психоматрицы с Excel (лист calc). Этап 2.

Golden-эталон извлечён из кэшированных значений книги (вход 01.01.2000).
Дополнительные контрольные примеры от заказчика кладём в tests/fixtures.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from core.numerology import PersonInput
from core.numerology.psychomatrix import compute_psychomatrix

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture",
    [
        "psychomatrix_2000_01_01.json",
        "psychomatrix_1994_05_28.json",
        "psychomatrix_1990_02_20.json",
    ],
)
def test_psychomatrix_matches_excel(fixture):
    data = _load(fixture)
    bd = date.fromisoformat(data["input"]["birth_date"])
    person = PersonInput("", "", None, bd)
    result = compute_psychomatrix(person)
    for key, expected in data["expected"].items():
        assert result[key] == expected, f"{key}: получили {result[key]!r}, эталон {expected!r}"


def test_two_digit_day_month():
    """Граничный случай: двузначные день и месяц (15.12.1990)."""
    r = compute_psychomatrix(PersonInput("", "", None, date(1990, 12, 15)))
    # 15.12.1990 цифры: 1,5,1,2,1,9,9,0 -> сумма 28 -> E18=28, E19=10
    assert r["consciousness_level"] == 15 + 12 + (1 + 9 + 9 + 0)
    assert r["soul_number"] == 15
    assert r["behavior_code"]  # код поведения определён для любой даты
