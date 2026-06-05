"""Прогноз на 5 лет (таблица РАСЧЕТ B49+ ← лист Matr строки 29–33).

Источник истины: лист Excel «Matr». Этап 4 (прогноз).

На каждый из 5 лет вперёд (возраст = полных лет + 0..4):
- год = год_рождения + возраст;
- персональное число года = свод(день + месяц + Σцифр года) → 1..9 + текст;
- Луна = Σ первых двух цифр (код_жизни / возраст);
- Солнце = Σ следующих двух цифр;
- «год на +/−» = Солнце − Луна → текст (−9..+9, иначе само число).

Сверено с эталоном книги (20.02.1990, сегодня 06.06.2026), нулевой допуск.

НЕ реализованы (требуют доп. реверса глубоких цепочек Matr, см. docs/excel-analysis):
- «судьбоносные события» Z (+/−): Matr!D = есть ли год в списке «судьбоносных годов»
  BK9:48 (цепочка BJ9:48 — повторяющиеся подряд значения);
- «12-летний цикл перерождения» AF: Matr!AH ← BG/CH-ряды;
- «энергетический потенциал» J: сравнение по энергокривой Matr!BE59:158
  (кусочно-линейная, опоры из ротаций цифр кода жизни; CH73←CJ72…).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from dateutil.relativedelta import relativedelta

from core.numerology._digits import digit_sum, reduce_1_9
from core.numerology.codes import compute_codes
from core.numerology.person import PersonInput

FORECAST_YEARS = 5

# Персональное число года → текст (РАСЧЕТ P-колонка).
PERSONAL_YEAR_TEXT = {
    1: "год планирования",
    2: "год взаимоотношения",
    3: "год творчества и креативности",
    4: "год стабильности и надежности",
    5: "год изменений",
    6: "год семьи",
    7: "год духовных поисков",
    8: "год проверки на честность",
    9: "завершающий год",
}

# «Год на + или −» (Солнце−Луна) → текст (РАСЧЕТ BO-колонка). Вне диапазона — само число.
YEAR_VALUE_TEXT = {
    -1: "незначительный спад",
    -2: "потеря отношений с близкими людьми",
    -3: "год ошибочных решений",
    -4: "опасность для здоровья",
    -5: "потеря имущества",
    -6: "потеря работы",
    -7: "духовный кризис, депрессия",
    -8: "потеря денег",
    -9: "спуск, но определенных событий не несет",
    1: "незначительное везение, хороший год",
    2: "полезные связи, новые друзья",
    3: "удачный год, лотерея",
    4: "подъем, определенных событий не несет",
    5: "успех в работе",
    6: "высокий каръерный рост",
    7: "разрешение конфликтов в семье",
    8: "улучшение финансовых дел",
    9: "подъём, определенных событий не несет",
}


def _moon_sun(life_code: int, age: int) -> tuple[int, int]:
    """Луна/Солнце года: суммы пар цифр строки (код_жизни / возраст)."""
    digits = [c for c in str(life_code / age) if c.isdigit()][:4]
    digits += ["0"] * (4 - len(digits))
    moon = int(digits[0]) + int(digits[1])
    sun = int(digits[2]) + int(digits[3])
    return moon, sun


def personal_year(person: PersonInput, year: int) -> int:
    """Персональное число года = свод(день + месяц + Σцифр года)."""
    return reduce_1_9(person.birth_date.day + person.birth_date.month + digit_sum(year))


@dataclass(frozen=True)
class ForecastYear:
    year: int
    age: int
    personal_year: int
    personal_year_text: str
    moon: int
    sun: int
    year_value: int  # Солнце − Луна
    year_value_text: str

    def as_dict(self) -> dict:
        return asdict(self)


def compute_forecast(person: PersonInput, reference_date: date | None = None) -> list[dict]:
    """Прогноз на 5 лет вперёд от текущего возраста. Список из 5 записей."""
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()

    current_age = relativedelta(reference_date, person.birth_date).years
    life_code = int(compute_codes(person, reference_date)["life_code"])

    out: list[dict] = []
    for i in range(FORECAST_YEARS):
        age = current_age + i
        year = person.birth_date.year + age
        moon, sun = _moon_sun(life_code, age)
        value = sun - moon
        py = personal_year(person, year)
        out.append(
            ForecastYear(
                year=year,
                age=age,
                personal_year=py,
                personal_year_text=PERSONAL_YEAR_TEXT.get(py, ""),
                moon=moon,
                sun=sun,
                year_value=value,
                year_value_text=YEAR_VALUE_TEXT.get(value, str(value)),
            ).as_dict()
        )
    return out


def compute_matrix(person: PersonInput) -> dict:
    """Совместимость: вернуть прогноз на 5 лет (остальные блоки Matr — позже)."""
    return {"forecast": compute_forecast(person)}
