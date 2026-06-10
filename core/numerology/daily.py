"""Ежедневный прогноз на выбранную дату.

Личные числа на конкретную дату (ЧПГ/ЧПМ/ЧПД, лист ЧПМ — те же формулы, что и в
отчёте, reference_date = выбранная дата) + трактовка дня (personal_day) и статус
биоритма этого дня (лист Bio: благоприятный/критический/травмоопасный/обычный).

Расчёт ЧПД golden-протестирован в test_moon_sun; здесь только сборка под одну дату.
"""

from __future__ import annotations

from datetime import date

from core.numerology.biorhythm import phase_on
from core.numerology.moon_sun import compute_personal_numbers
from core.numerology.person import PersonInput


def _biorhythm_status(person: PersonInput, target_date: date) -> str:
    """Статус дня по биоритму (Bio): по приоритету травмо→крит→благо→обычный."""
    ph = phase_on(person, target_date)
    if ph.is_traumatic:
        return "травмоопасный"
    if ph.is_critical:
        return "критический"
    if ph.is_favorable:
        return "благоприятный"
    return "обычный"


def daily_forecast(person: PersonInput, target_date: date) -> dict:
    """Прогноз на один день: ЧПД + трактовка, ЧПГ/ЧПМ контекст, статус биоритма."""
    pn = compute_personal_numbers(person, target_date)
    return {
        "date": target_date.isoformat(),
        "personal_year": pn["personal_year"],
        "personal_month": pn["personal_month"],
        "personal_day": pn["personal_day"],
        "personal_day_text": pn["personal_day_text"],
        "personal_month_text": pn["personal_month_text"],
        "combo_title": pn["combo_title"],
        "combo_text": pn["combo_text"],
        "biorhythm": _biorhythm_status(person, target_date),
    }
