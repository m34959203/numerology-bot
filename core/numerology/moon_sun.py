"""Помесячная Луна/Солнце + ЧПГ/ЧПМ/ЧПД (личные числа года/месяца/дня).

Источник истины: листы Excel «Calculation луна и солнце», «Lists луна и солнце», «ЧПМ».
Этап 5. Зависят ТОЛЬКО от даты рождения и даты отчёта (имя не участвует).
Сверено с эталоном книги (20.02.1990, отчёт 06.06.2026), нулевой допуск.

Помесячная Луна/Солнце (лист Calculation луна и солнце → render-лист 35):
1. код жизни (день×месяц×год, добивка до 6 знаков) и число года = свод Σцифр года отчёта;
2. «изменённый код» — каждая из 6 цифр кода + число года, со сводом;
3. возраст = (отчёт − рождение)/365; Луна/Солнце = пары цифр (код_жизни/возраст);
   знак прогноза Result = Солнце − Луна;
4. «дважды изменённый код» B26 — изменённый код + Result по позициям (по модулю);
5. для каждого месяца: B26 / делитель[месяц] → первые 4 цифры → Луна_м/Солнце_м;
   код месяца J = Солнце_м − Луна_м (или −|..| если Result=0) → текст по таблице.

ЧПГ/ЧПМ/ЧПД (лист ЧПМ → render-лист 36):
- ЧПГ = свод( Σцифр(год отчёта) + свод(день + месяц рождения) );
- ЧПМ = свод( ЧПГ + месяц отчёта );
- ЧПД = свод( ЧПМ + день отчёта );
- ключ комбинации = "{ЧПМ} − {ЧПГ}" (разделитель U+2212).
"""

from __future__ import annotations

from datetime import date

from core.content.loader import interpret
from core.numerology._digits import digit_sum, reduce_1_9
from core.numerology.codes import compute_codes
from core.numerology.person import PersonInput

# Делители по месяцам (Lists луна и солнце!K2:K13).
_MONTH_DIVISORS = [7, 9, 28, 10, 8, 16, 11, 14, 17, 25, 2, 19]
_MONTH_NAMES = [
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
]
_MINUS = "−"  # знак минус в ключе комбинации ЧПМ−ЧПГ


def _svod(n: int) -> int:
    """Свод значения: <10 — как есть; иначе сумма цифр; результат по модулю ≥0."""
    n = abs(n)
    return n if n < 10 else digit_sum(n)


def _first4_digits(x: float) -> list[int]:
    """Первые 4 цифры строкового представления числа (без точки/знака)."""
    ds = [c for c in str(x) if c.isdigit()][:4]
    ds += ["0"] * (4 - len(ds))
    return [int(c) for c in ds]


def _double_changed_code(life_code: str, year_number: int, result: int, moon: int, sun: int) -> str:
    """«Дважды изменённый код» B26 (6 цифр)."""
    changed = [_svod(int(d) + year_number) for d in life_code[:6]]
    change = result if result != 0 else 1
    out = []
    for i, c in enumerate(changed):
        val = abs(_svod(c + change))
        if i == 0 and moon == sun:
            val = 1
        out.append(str(val))
    return "".join(out)


def _age_years(birth: date, reference: date) -> int:
    """Возраст как INT((отчёт − рождение)/365) — как в книге."""
    return (reference - birth).days // 365


def compute_monthly_moon_sun(person: PersonInput, reference_date: date) -> list[dict]:
    """12 записей помесячной Луны/Солнца: {month, month_name, value, text}."""
    life_code = compute_codes(person, reference_date)["life_code"]
    year_number = reduce_1_9(digit_sum(reference_date.year))
    age = _age_years(person.birth_date, reference_date)

    ms = _first4_digits(int(life_code) / age)
    moon, sun = ms[0] + ms[1], ms[2] + ms[3]
    result = sun - moon

    b26 = _double_changed_code(life_code, year_number, result, moon, sun)
    b26_val = int(b26)

    out: list[dict] = []
    for m in range(12):
        D, E, F, G = _first4_digits(b26_val / _MONTH_DIVISORS[m])
        moon_m, sun_m = D + E, F + G
        value = (sun_m - moon_m) if result != 0 else -abs(sun_m - moon_m)
        out.append(
            {
                "month": m + 1,
                "month_name": _MONTH_NAMES[m],
                "value": value,
                "text": interpret("moon_sun_monthly", value),
            }
        )
    return out


def compute_personal_numbers(person: PersonInput, reference_date: date) -> dict:
    """ЧПГ/ЧПМ/ЧПД + тексты (лист ЧПМ)."""
    b = person.birth_date
    chpg = reduce_1_9(digit_sum(reference_date.year) + reduce_1_9(b.day + b.month))
    chpm = reduce_1_9(chpg + reference_date.month)
    chpd = reduce_1_9(chpm + reference_date.day)
    combo = f"{chpm} {_MINUS} {chpg}"
    return {
        "personal_year": chpg,
        "personal_month": chpm,
        "personal_day": chpd,
        "combo_key": combo,
        "personal_year_text": None,  # ЧПГ отдельного текста в книге нет
        "personal_month_text": interpret("personal_month", chpm),
        "personal_day_text": interpret("personal_day", chpd),
        "combo_title": interpret("personal_combo_title", combo),
        "combo_text": interpret("personal_combo_text", combo),
    }
