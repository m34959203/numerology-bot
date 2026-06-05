"""Сверка биоритмов с Excel (лист Bio). Этап 2.

Golden-эталон извлечён из кэша книги: вход 01.01.2000, сегодня 27.07.2025.
Списки благоприятных/критических/травмоопасных дней совпадают 1:1 с РАСЧЕТ.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from core.numerology import PersonInput
from core.numerology.biorhythm import compute_biorhythm, phase_on

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture", ["biorhythm_2000_01_01.json", "biorhythm_1994_05_28.json"])
def test_biorhythm_matches_excel(fixture):
    data = _load(fixture)
    person = PersonInput("", "", None, date.fromisoformat(data["input"]["birth_date"]))
    ref = date.fromisoformat(data["input"]["reference_date"])
    result = compute_biorhythm(person, ref)
    for kind in ("favorable", "critical", "traumatic"):
        assert (
            result[kind] == data["expected"][kind]
        ), f"{kind}: получили {result[kind]}, эталон {data['expected'][kind]}"


def test_phase_at_birth_is_zero():
    person = PersonInput("", "", None, date(2000, 1, 1))
    p = phase_on(person, date(2000, 1, 1))
    assert (p.phys, p.emo, p.intel) == (0, 0, 0)


def test_reference_before_birth_raises():
    person = PersonInput("", "", None, date(2000, 1, 1))
    with pytest.raises(ValueError):
        phase_on(person, date(1999, 12, 31))
