"""Коды и базовые вычисления.

Источник истины: листы Excel «РАСЧЕТ», «Calculation», «Lists». Этап 3.
Сюда входят: полных лет, прожито дней, код жизни/человека/души, ЧЖП,
финансовый код, счастливые числа и пр.

Перед реализацией: разобрать формулы листа, выписать алгоритм псевдокодом,
написать тест на контрольных примерах, затем реализацию.
"""

from __future__ import annotations

from core.numerology.person import PersonInput


def compute_codes(person: PersonInput) -> dict:
    """Вернуть коды и базовые вычисления в виде структурированного dict."""
    raise NotImplementedError("Этап 3: перенос листов «РАСЧЕТ», «Calculation», «Lists»")
