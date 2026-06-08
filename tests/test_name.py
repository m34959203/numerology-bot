"""Сверка числа/кармы имени (лист Matr, D3–D7) с эталоном книги и контролями."""

import json
from datetime import date
from pathlib import Path

from core.numerology import PersonInput
from core.numerology.name import compute_name_numbers

FIXTURES = Path(__file__).parent / "fixtures"


def test_name_numbers_match_excel():
    data = json.loads((FIXTURES / "name_examples.json").read_text(encoding="utf-8"))
    for case in data["cases"]:
        person = PersonInput(
            last_name=case["last_name"],
            first_name=case["first_name"],
            middle_name=case["middle_name"],
            birth_date=date(2000, 1, 1),  # имя не зависит от даты
            maiden_name=case["maiden_name"],
        )
        got = compute_name_numbers(person)
        for key, exp in case["expected"].items():
            assert got[key] == exp, f"{case['label']} {key}: получили {got[key]!r}, эталон {exp!r}"


def test_empty_name_is_zero():
    """Пустое ФИО → все числа 0, кармы нет (как пустой пример книги)."""
    person = PersonInput("", "", None, date(2000, 1, 1))
    got = compute_name_numbers(person)
    assert got == {
        "last_name": 0,
        "first_name": 0,
        "middle_name": 0,
        "maiden_name": 0,
        "karma": 0,
        "has_karma": False,
    }
