"""Психоматрица / квадрат Пифагора.

Источник истины: лист Excel «calc». Этап 2.

Алгоритм (восстановлен по формулам листа calc для входа C12 = дата рождения):

1. Цифры даты (calc!D16:K16): первая/вторая цифра дня, первая/вторая цифра
   месяца (вторая = 0, если число однозначное), затем 4 цифры года.
2. Рабочие числа:
   - E18 = сумма всех 8 цифр даты (первое рабочее число);
   - E19 = сумма цифр E18 (сведение в одну цифру);
   - E20 = E18 − 2×(первая цифра дня, либо вторая, если первая = 0); по модулю
           через спец-ветку формулы при отрицательном результате;
   - E21 = сумма цифр E20.
3. Строка рабочих чисел U16 = concat(E18, E19, E20, E21); её цифры (calc!L16:S16)
   добавляются в общий пул.
4. Пул цифр = цифры даты + цифры рабочих чисел. Считаем вхождения 1..9
   (нули не учитываются) — это клетки квадрата Пифагора (calc!U19:W21).
5. Качества (лист РАСЧЕТ): повтор-цифры клеток (count×digit) и суммы рядов/столбцов.

Скаляры: число души (calc!F1=DAY), уровень сознания (calc!C1), ЧЖП (свод E19),
код жизни (calc!C14), код поведения (VLOOKUP по дате, таблица behavior_codes.json).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from functools import cache
from pathlib import Path

from core.numerology.person import PersonInput

_DATA = Path(__file__).resolve().parent.parent / "content" / "data" / "behavior_codes.json"


@cache
def _behavior_codes() -> dict[str, str]:
    return json.loads(_DATA.read_text(encoding="utf-8"))


def _digit_sum(n: int) -> int:
    """Сумма цифр числа (одно сведение, как MID(..,1)+MID(..,2) в Excel)."""
    return sum(int(c) for c in str(abs(n)))


def _reduce_1_9(n: int) -> int:
    """Свод к 1..9 как VLOOKUP по таблице calc!AI:AJ (= ((n-1) mod 9)+1)."""
    return (n - 1) % 9 + 1 if n > 0 else 0


def _repdigit(count: int, digit: int) -> int:
    """Повтор-цифра клетки: count раз цифра digit (calc!U24 и т.п.). 0 если пусто."""
    return int(str(digit) * count) if count > 0 else 0


def _date_digits(d: date) -> list[int]:
    """8 цифр даты (calc!D16:K16): день(2), месяц(2, добивка 0), год(4)."""
    day = str(d.day)
    month = str(d.month)
    year = f"{d.year:04d}"
    return [
        int(day[0]),
        int(day[1]) if len(day) == 2 else 0,
        int(month[0]),
        int(month[1]) if len(month) == 2 else 0,
        *(int(c) for c in year),
    ]


@dataclass(frozen=True)
class Psychomatrix:
    """Результат психоматрицы. 0 в качестве трактуется как «нет»."""

    # Квадрат Пифагора: повтор-цифры клеток 1..9
    character: int  # 1 — характер
    energy: int  # 2 — энергия
    interest: int  # 3 — интерес (познание)
    health: int  # 4 — здоровье
    logic: int  # 5 — логика, интуиция
    labor: int  # 6 — труд, власть
    luck: int  # 7 — везение
    duty: int  # 8 — чувство долга
    memory: int  # 9 — ум, память
    # Суммы рядов/столбцов
    self_esteem: int  # самооценка = c1+c2+c3
    purposefulness: int  # целеустремлённость = c1+c4+c7
    family_quality: int  # качество семьянина = c2+c5+c8
    attitude_to_labor: int  # отношение к труду = c4+c5+c6
    stability: int  # стабильность = c3+c6+c9
    talents: int  # таланты = c7+c8+c9
    temperament: int  # темперамент = c3+c5+c7
    # Скаляры
    soul_number: int  # число души = день рождения (calc!F1)
    consciousness_level: int  # уровень сознания (calc!C1)
    life_path: int  # ЧЖП — число жизненного пути (calc!J19)
    life_code: str  # код жизни (calc!C14)
    behavior_code: str  # код поведения (calc!D13)

    def as_dict(self) -> dict:
        return asdict(self)


def compute_psychomatrix(person: PersonInput) -> dict:
    """Рассчитать психоматрицу по листу «calc». Возвращает Psychomatrix.as_dict()."""
    d = person.birth_date

    # --- цифры даты и рабочие числа ---
    dd = _date_digits(d)
    e18 = sum(dd)
    e19 = _digit_sum(e18)
    first_day_digit = dd[0] if dd[0] > 0 else dd[1]
    subtract = first_day_digit * 2
    e20 = e18 - subtract if (e18 - subtract) >= 0 else (dd[0] - subtract) * -1
    e21 = _digit_sum(e20)
    working = [int(c) for c in f"{e18}{e19}{e20}{e21}"]

    # --- пул цифр и клетки квадрата ---
    pool = dd + working
    c = {n: pool.count(n) for n in range(1, 10)}

    # --- скаляры ---
    consciousness = d.day + d.month + sum(int(x) for x in f"{d.year:04d}")
    life_code = str(d.day * d.month * d.year)
    if len(life_code) < 6:
        life_code = life_code + "0" * (6 - len(life_code))
    behavior_code = _behavior_codes().get(f"{d.month:02d}-{d.day:02d}", "")

    result = Psychomatrix(
        character=_repdigit(c[1], 1),
        energy=_repdigit(c[2], 2),
        interest=_repdigit(c[3], 3),
        health=_repdigit(c[4], 4),
        logic=_repdigit(c[5], 5),
        labor=_repdigit(c[6], 6),
        luck=_repdigit(c[7], 7),
        duty=_repdigit(c[8], 8),
        memory=_repdigit(c[9], 9),
        self_esteem=c[1] + c[2] + c[3],
        purposefulness=c[1] + c[4] + c[7],
        family_quality=c[2] + c[5] + c[8],
        attitude_to_labor=c[4] + c[5] + c[6],
        stability=c[3] + c[6] + c[9],
        talents=c[7] + c[8] + c[9],
        temperament=c[3] + c[5] + c[7],
        soul_number=d.day,
        consciousness_level=consciousness,
        life_path=_reduce_1_9(e19),
        life_code=life_code,
        behavior_code=behavior_code,
    )
    return result.as_dict()
