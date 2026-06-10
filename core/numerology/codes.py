"""Коды и базовые вычисления (блок «Вычисления» листа РАСЧЕТ ← лист Matr).

Источник истины: лист Excel «Matr». Этап 3. Все значения ниже зависят ТОЛЬКО от
даты рождения (и «сегодня» для возраста/дней) — сверено с тремя эталонами книги
(01.01.2000, 28.05.1994, 20.02.1990), нулевой допуск. Расчёты от ИМЕНИ (число
имени / карма имени) — отдельно, после получения ФИО-эталонов (см. OPEN_QUESTIONS).

Алгоритмы (по разбору Matr, см. docs/excel-analysis.md M.2–M.6):
- духовный уровень BD7 = Σ8 цифр даты; свод BE7 = digit_sum(BD7);
- код человека = concat(BD7, BE7); счастливые числа = «BE7 и BG7»,
  где BF7 = |BD7 − 2×(первая ненулевая цифра дня)|, BG7 = digit_sum(BF7);
- код жизни = день×месяц×год, добивка нулями справа до 6 знаков;
- финансовый код = concat(dr(Σцифр дня), dr(Σцифр месяца), dr(Σцифр года), dr(их суммы));
- доступ к деньгам = digit_sum( int(месяц‖год) × день × 100 );
- жизненные силы = digit_sum( int(день‖месяц) × год × 100 );
- жизненная задача («Жизнь») = число ненулевых цифр в пуле (дата + рабочие числа);
- полных лет; прожито дней = (сегодня − дата рождения).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from dateutil.relativedelta import relativedelta

from core.numerology._digits import date_digits, digit_pool, digit_sum, reduce_1_9
from core.numerology.person import PersonInput

# Порог в РАСЧЕТ для текстовой добавки к «доступ к деньгам» / «жизненные силы».
THRESHOLD_27 = 27


@dataclass(frozen=True)
class Codes:
    spiritual_level: int  # духовный уровень (BD7)
    human_code: str  # код человека / 1-код «до 35 лет» (concat BD7,BE7 = calc!E18&E19)
    second_code: str  # 2-код «после 35 лет» (concat BF7,BG7 = calc!E20&E21)
    lucky_numbers: str  # счастливые числа «BE7 и BG7»
    life_code: str  # код жизни (день×месяц×год, паддинг до 6)
    finance_code: str  # финансовый код удачи
    money_access: int  # доступ к деньгам (число)
    vitality: int  # жизненные силы (число)
    life_task: int  # «Жизнь» — число ненулевых цифр пула
    full_years: int  # полных лет
    lived_days: int  # прожито дней

    def as_dict(self) -> dict:
        return asdict(self)


def compute_codes(person: PersonInput, reference_date: date | None = None) -> dict:
    """Рассчитать коды по листу «Matr». reference_date по умолчанию — сегодня."""
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()

    d = person.birth_date
    dd = date_digits(d)

    spiritual = sum(dd)  # BD7
    be7 = digit_sum(spiritual)
    first_day_digit = dd[0] if dd[0] > 0 else dd[1]
    bf7 = abs(spiritual - 2 * first_day_digit)
    bg7 = digit_sum(bf7)

    life_code = str(d.day * d.month * d.year)
    if len(life_code) < 6:
        life_code = life_code + "0" * (6 - len(life_code))

    fin = (
        f"{reduce_1_9(dd[0] + dd[1])}"
        f"{reduce_1_9(dd[2] + dd[3])}"
        f"{reduce_1_9(dd[4] + dd[5] + dd[6] + dd[7])}"
    )
    fin += str(reduce_1_9(int(fin[0]) + int(fin[1]) + int(fin[2])))

    money = digit_sum(int(f"{d.month}{d.year}") * d.day * 100)
    vitality = digit_sum(int(f"{d.day}{d.month}") * d.year * 100)
    life_task = sum(1 for x in digit_pool(d) if x != 0)

    result = Codes(
        spiritual_level=spiritual,
        human_code=f"{spiritual}{be7}",
        second_code=f"{bf7}{bg7}",
        lucky_numbers=f"{be7} и {bg7}",
        life_code=life_code,
        finance_code=fin,
        money_access=money,
        vitality=vitality,
        life_task=life_task,
        full_years=relativedelta(reference_date, d).years,
        lived_days=(reference_date - d).days,
    )
    return result.as_dict()
