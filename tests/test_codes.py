"""Сверка кодов (блок «Вычисления» РАСЧЕТ ← Matr) с тремя эталонами книги."""

import json
from datetime import date
from pathlib import Path

from core.numerology import PersonInput
from core.numerology.codes import compute_codes

FIXTURES = Path(__file__).parent / "fixtures"


def test_codes_match_excel():
    data = json.loads((FIXTURES / "codes_examples.json").read_text(encoding="utf-8"))
    for case in data["cases"]:
        person = PersonInput("", "", None, date.fromisoformat(case["birth_date"]))
        ref = date.fromisoformat(case["reference_date"])
        got = compute_codes(person, ref)
        for key, exp in case["expected"].items():
            assert (
                got[key] == exp
            ), f"{case['birth_date']} {key}: получили {got[key]!r}, эталон {exp!r}"
