"""Сверка кармических событий (BG17/BG20) с эталоном книги.

Эталон — единственный заполненный пример книги: субъект 20.02.1990,
мать 06.08.1971, отец 23.11.1970 → BG17/BG20 из кэша РАСЧЕТ."""

from datetime import date

from core.numerology import PersonInput
from core.numerology.karma_events import compute_karma_events


def _person(**kw):
    base = dict(
        last_name="ЕРОФЕЕВА",
        first_name="ЮЛИЯ",
        middle_name="ВЛАДИМИРОВНА",
        birth_date=date(1990, 2, 20),
        maiden_name="МИРОНОВА",
    )
    base.update(kw)
    return PersonInput(**base)


def test_karma_events_match_excel():
    person = _person(
        mother_birth_date=date(1971, 8, 6),
        father_birth_date=date(1970, 11, 23),
    )
    events = compute_karma_events(person)
    assert events["first"] == {
        "sign": "-",
        "age": 28,
        "text": "событие негативного характера в возрасте 28",
    }
    assert events["second"] == {
        "sign": "+",
        "age": 28,
        "text": "подъём в возрасте 28",
    }


def test_missing_parent_dates_skip_events():
    """Без дат родителей события не формируются (как #VALUE! в книге)."""
    events = compute_karma_events(_person())
    assert events == {"first": None, "second": None}

    only_mother = compute_karma_events(_person(mother_birth_date=date(1971, 8, 6)))
    assert only_mother["first"] is not None
    assert only_mother["second"] is None
