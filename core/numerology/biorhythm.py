"""Биоритмы: благоприятные / критические / травмоопасные дни.

Источник истины: лист Excel «Bio». Этап 2.

Модель (восстановлена по формулам Bio для входа B2 = дата рождения):
каждая строка = один день от рождения. Для каждого дня ведутся три фазовых
аккумулятора с суточными инкрементами и переносом по длине цикла:

    физика   : I += 1.0131383374031213, перенос при I > 23 (−24)   (Bio!AF$3)
    эмоция   : J += 1.0201714790837135, перенос при J > 28 (−29)   (Bio!AC$15)
    интеллект: K += 1.0252235280781246, перенос при K > 33 (−34)   (Bio!AC$20)

Целые позиции фаз F/G/H = ROUND(I/J/K) (округление Excel — half-away-from-zero),
со сбросом в 0 на следующий день после достижения максимума цикла и значением
максимума при отрицательном аккумуляторе.

Зоны (Bio!R,S,T):
    R(физ) = 1 если 4≤F≤9,  2 если 17≤F≤21
    S(эмо) = 1 если 4≤G≤10, 2 если 19≤G≤24
    T(инт) = 1 если 5≤H≤11, 2 если 23≤H≤28

Классификация дня (Bio!U/V/W):
    благоприятный (Good)     : R=S=T=1  (сумма зон = 3)
    критический   (Critical) : R=S=T=2  (сумма зон = 6)
    травмоопасный (Dang)     : 11.5 < I < 12  (физ-аккумулятор у пика)

Отчёт (РАСЧЕТ) выводит ближайшие такие дни вперёд от «сегодня». Точные лимиты
вывода/горизонт согласуются с заказчиком (см. OPEN_QUESTIONS); дефолты ниже
воспроизводят пример книги (7 благоприятных, 5 критических, 5 травмоопасных).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

from core.numerology.person import PersonInput

# Суточные инкременты фаз (Bio!AF$3, AC$15, AC$20) — точные double из книги.
_INC_PHYS = 1.0131383374031213
_INC_EMO = 1.0201714790837135
_INC_INTEL = 1.0252235280781246

_CYCLE_PHYS = 23
_CYCLE_EMO = 28
_CYCLE_INTEL = 33

# Правила вывода особых дней (display-слоты РАСЧЕТ BD6/BD9/BD12 = 7/7/5).
# Выверено по ДВУМ эталонам книги (01.01.2000 и 28.05.1994):
#   благоприятные — первые 7 вперёд (count);
#   травмоопасные — первые 5 вперёд (count);
#   критические   — все в окне 365 дней, не более 7 (window, у Excel — годовой
#                   диапазон строк-кандидатов 436..801). count даёт 5 и 2 соответственно.
# Формат: count = максимум дат; window_days = только в пределах N дней (None = без окна).
DEFAULT_SPEC: dict[str, dict[str, int | None]] = {
    "favorable": {"count": 7, "window_days": None},
    "critical": {"count": 7, "window_days": 365},
    "traumatic": {"count": 5, "window_days": None},
}
# Верхняя граница итерации (благоприятные/травмоопасные без окна — ищем вперёд).
MAX_SCAN_DAYS = 2000


def _xround(x: float) -> int:
    """Округление как Excel ROUND(x, 0): половина — от нуля."""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


@dataclass(frozen=True)
class DayPhase:
    """Фазы дня: целые позиции циклов и физ-аккумулятор."""

    phys: int  # F (0..23)
    emo: int  # G (0..28)
    intel: int  # H (0..33)
    phys_acc: float  # I (для травмоопасности)

    @property
    def is_favorable(self) -> bool:
        return 4 <= self.phys <= 9 and 4 <= self.emo <= 10 and 5 <= self.intel <= 11

    @property
    def is_critical(self) -> bool:
        return 17 <= self.phys <= 21 and 19 <= self.emo <= 24 and 23 <= self.intel <= 28

    @property
    def is_traumatic(self) -> bool:
        return 11.5 < self.phys_acc < 12


def iter_phases(birth: date, upto: date):
    """Итератор (date, DayPhase) от дня рождения до upto включительно."""
    i = j = k = 0.0
    f = g = h = 0
    d = birth
    yield d, DayPhase(f, g, h, i)
    for _ in range((upto - birth).days):
        i2 = i + _INC_PHYS
        i = i2 - (_CYCLE_PHYS + 1) if i2 > _CYCLE_PHYS else i2
        j2 = j + _INC_EMO
        j = j2 - (_CYCLE_EMO + 1) if j2 > _CYCLE_EMO else j2
        k2 = k + _INC_INTEL
        k = k2 - (_CYCLE_INTEL + 1) if k2 > _CYCLE_INTEL else k2
        f = 0 if f == _CYCLE_PHYS else (_CYCLE_PHYS if i < 0 else _xround(i))
        g = 0 if g == _CYCLE_EMO else (_CYCLE_EMO if j < 0 else _xround(j))
        h = 0 if h == _CYCLE_INTEL else (_CYCLE_INTEL if k < 0 else _xround(k))
        d = d + timedelta(days=1)
        yield d, DayPhase(f, g, h, i)


def phase_on(person: PersonInput, day: date) -> DayPhase:
    """Фазы биоритмов на конкретную дату."""
    if day < person.birth_date:
        raise ValueError("Дата раньше даты рождения")
    last = None
    for _d, ph in iter_phases(person.birth_date, day):
        last = ph
    assert last is not None
    return last


def special_days(
    person: PersonInput,
    reference_date: date,
    spec: dict[str, dict[str, int | None]] | None = None,
) -> dict[str, list[date]]:
    """Ближайшие особые дни вперёд от reference_date.

    Каждая категория ограничена своим count и опциональным окном (window_days).
    Возвращает {'favorable': [...], 'critical': [...], 'traumatic': [...]}.
    """
    spec = spec or DEFAULT_SPEC
    horizon = reference_date + timedelta(days=MAX_SCAN_DAYS)
    out: dict[str, list[date]] = {"favorable": [], "critical": [], "traumatic": []}
    checks = {
        "favorable": lambda p: p.is_favorable,
        "critical": lambda p: p.is_critical,
        "traumatic": lambda p: p.is_traumatic,
    }
    for d, ph in iter_phases(person.birth_date, horizon):
        if d < reference_date:
            continue
        for kind, rule in spec.items():
            lst = out[kind]
            if len(lst) >= rule["count"]:
                continue
            window = rule["window_days"]
            if window is not None and (d - reference_date).days > window:
                continue
            if checks[kind](ph):
                lst.append(d)
    return out


def compute_biorhythm(person: PersonInput, reference_date: date | None = None) -> dict:
    """Рассчитать особые дни биоритмов. reference_date по умолчанию — сегодня.

    Возвращает dict с ISO-датами и фазами на reference_date.
    """
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()
    days = special_days(person, reference_date)
    ref_phase = phase_on(person, reference_date)
    return {
        "reference_date": reference_date.isoformat(),
        "favorable": [d.isoformat() for d in days["favorable"]],
        "critical": [d.isoformat() for d in days["critical"]],
        "traumatic": [d.isoformat() for d in days["traumatic"]],
        "phase": {"phys": ref_phase.phys, "emo": ref_phase.emo, "intel": ref_phase.intel},
    }
