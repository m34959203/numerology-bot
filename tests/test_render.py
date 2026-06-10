"""Рендер отчёта в текст + разбивка по лимиту Telegram."""

from datetime import date

from core.numerology import PersonInput
from core.numerology.report import build_report
from core.render import render_report, split_message


def test_render_contains_sections():
    p = PersonInput("Ерофеева", "Юлия", "Владимировна", date(1990, 2, 20))
    report = build_report(p, date(2026, 6, 6))
    text = render_report(report, "Ерофеева Юлия Владимировна", p.birth_date)
    for marker in [
        "МАТРИЦА",
        "КОДЫ И ПОКАЗАТЕЛИ",
        "ПСИХОМАТРИЦА",
        "ПРОГНОЗ НА 5 ЛЕТ",
        "ЛИЧНЫЕ ЧИСЛА",
    ]:
        assert marker in text
    assert "Код жизни: 796000" in text


def test_split_message_respects_limit():
    text = "\n".join(f"строка номер {i} " * 5 for i in range(2000))
    parts = split_message(text, limit=4096)
    assert all(len(p) <= 4096 for p in parts)
    assert len(parts) > 1
    # склейка восстанавливает контент (без потерь строк)
    assert sum(p.count("строка") for p in parts) == text.count("строка")


def test_split_short_text_single():
    assert split_message("привет") == ["привет"]
