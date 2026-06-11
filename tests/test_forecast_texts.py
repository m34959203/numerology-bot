"""Прогноз по годам: каждый год несёт трактовки по СВОИМ значениям (лукап из
листа «текст»), включая «нулевой период» при Солнце=0. Тексты — продуктовый
слой (core.numerology.report обогащает compute_forecast), значения покрыты
test_matrix."""

from __future__ import annotations

from datetime import date

from core.content.loader import interpret
from core.numerology import PersonInput
from core.numerology.report import build_forecast_section
from core.numerology.tariffs import report_for

REF = date(2026, 6, 6)
PERSON = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))


def test_new_blocks_extracted():
    # 4 новых блока извлечены из Excel с ожидаемыми ключами.
    assert set(interpret_keys("life_force_graph")) == {str(n) for n in range(10)}
    assert "0" in interpret_keys("sun_year")  # нулевой период
    assert "нулевой период" in (interpret("sun_year", 0) or "").lower()


def interpret_keys(topic: str) -> list[str]:
    from core.content.loader import _load_topic

    return list(_load_topic(topic, "ru"))


def test_forecast_year_carries_per_value_texts():
    years = build_forecast_section(PERSON, REF)
    assert years, "прогноз не пустой"
    for y in years:
        # ИТОГ года — сверено с книгой (Matr!H = Солнце−Луна = year_value), лукап по значению
        assert y["total_text"] == interpret("year_total", y["year_value"])
        assert y["sun_text"] == interpret("sun_year", y["sun"])


def test_zero_period_text_when_sun_zero():
    # Искусственный год с Солнцем=0 → текст нулевого периода (через лукап sun_year[0]).
    zero_text = interpret("sun_year", 0)
    assert zero_text and "рок" in zero_text.lower()


def test_forecast_text_changes_with_value():
    # Разные значения ИТОГ → разные описания (описание меняется со значением).
    pos = interpret("year_total", 6)
    neg = interpret("year_total", -6)
    assert pos and neg and pos != neg


def test_life_code_graph_digit_matches_book():
    # Лист 19: код жизни 796000, возраст 36 → активная цифра 7 (книга F37=7).
    from core.numerology.matrix import life_code_graph_digit

    assert life_code_graph_digit("796000", 36) == 7
    assert life_code_graph_digit("796000", 37) == 9  # позиция age%6=1 → «9»
    assert life_code_graph_digit("796000", 42) == 7  # цикл по 6: 42%6=0 снова «7»


def test_forecast_year_carries_life_force_text():
    years = build_forecast_section(PERSON, REF)
    for y in years:
        assert y["life_force_text"] == interpret("life_force_graph", y["life_force_digit"])


def test_render_forecast_shows_full_year_text():
    from core.render import render_report

    text = render_report(report_for(PERSON, REF, "forecast_5y"), "Ерофеева Юлия", PERSON.birth_date)
    assert "Итог года:" in text
