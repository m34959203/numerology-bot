"""Ежедневный прогноз на выбранную дату.

Личные числа на конкретную дату (ЧПГ/ЧПМ/ЧПД, лист ЧПМ — те же формулы, что и в
отчёте, reference_date = выбранная дата) + трактовка дня (personal_day) и
биоритмы этого дня (лист Bio): статус (благоприятный/критический/травмоопасный/
обычный) + значения трёх циклов в процентах (уникальны почти каждый день).

Расчёт ЧПД golden-протестирован в test_moon_sun; здесь только сборка под одну дату.
"""

from __future__ import annotations

import math
from datetime import date

from core.numerology.biorhythm import DayPhase, phase_on
from core.numerology.moon_sun import compute_personal_numbers
from core.numerology.person import PersonInput

# Длины биоритмических циклов (лист Bio): физический 23, эмоциональный 28,
# интеллектуальный 33 дня. Позиция дня в цикле меняется каждый день.
_CYCLE_LEN = {"physical": 23, "emotional": 28, "intellectual": 33}


def _biorhythm_status(phase: DayPhase) -> str:
    """Ключ статуса дня по биоритму (Bio): травмо→крит→благо→обычный (локаль в render)."""
    if phase.is_traumatic:
        return "traumatic"
    if phase.is_critical:
        return "critical"
    if phase.is_favorable:
        return "favorable"
    return "ordinary"


def _biorhythm_cycles(phase: DayPhase) -> dict[str, int]:
    """Значение каждого биоритм-цикла на день в процентах (−100..+100): sin от
    позиции дня в цикле. Меняется каждый день → прогноз уникален по дате."""
    pos = {"physical": phase.phys, "emotional": phase.emo, "intellectual": phase.intel}
    return {
        cycle: round(math.sin(2 * math.pi * pos[cycle] / length) * 100)
        for cycle, length in _CYCLE_LEN.items()
    }


def daily_forecast(person: PersonInput, target_date: date) -> dict:
    """Прогноз на один день: ЧПД + трактовка, биоритмы дня (статус + циклы %),
    краткий контекст ЧПГ/ЧПМ.

    Месячный текст (personal_month_text) НЕ включаем: он одинаков весь месяц и в
    дневном прогнозе создавал ощущение «одно и то же» (он есть в полном отчёте).
    """
    pn = compute_personal_numbers(person, target_date)
    phase = phase_on(person, target_date)
    return {
        "date": target_date.isoformat(),
        "personal_year": pn["personal_year"],
        "personal_month": pn["personal_month"],
        "personal_day": pn["personal_day"],
        "personal_day_text": pn["personal_day_text"],
        "biorhythm": _biorhythm_status(phase),
        "biorhythm_cycles": _biorhythm_cycles(phase),
    }
