"""Смоук-тест каркаса: модули импортируются, вход собирается.

Реальные тесты сверки с Excel добавляются по этапам (см. test_*.py ниже).
"""

from datetime import date

from core.numerology import PersonInput


def test_person_input_builds():
    p = PersonInput(
        last_name="Иванов",
        first_name="Иван",
        middle_name="Иванович",
        birth_date=date(1990, 5, 15),
    )
    assert p.first_name == "Иван"
    assert p.maiden_name is None


def test_dispatcher_builds():
    from bot.main import build_dispatcher

    assert build_dispatcher() is not None
