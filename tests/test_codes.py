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


def test_thousand_code_and_consciousness():
    """C19 (код тысячника = Matr!I3) и C21 (текст уровня сознания). Эталон
    Ерофеева Ю.В. 20.02.1990: I3=19 (сверено с книгой), уровень сознания —
    «земная карма» (духовный уровень 23 ≥ 20, жизненная задача 11 < 30)."""
    from core.render import consciousness_meaning, thousand_code_text

    c = compute_codes(PersonInput("", "", None, date(1990, 2, 20)), date(2026, 6, 6))
    assert c["thousand_code"] == 19
    assert thousand_code_text(19).startswith("Код тысячника - известность через творчество")
    assert thousand_code_text(0) is None  # не тысячник
    assert thousand_code_text(46).startswith("Код тысячника - человек учитель, должен оставить")
    assert consciousness_meaning(23, 11).startswith("Необходимо отработать свою земную карму")
    assert consciousness_meaning(15, 11).startswith("Необходимо основное внимание уделять")
