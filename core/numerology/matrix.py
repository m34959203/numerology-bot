"""Прогноз на 5 лет (таблица РАСЧЕТ B49+ ← лист Matr строки 29–33).

Источник истины: лист Excel «Matr». Этап 4 (прогноз).

На каждый из 5 лет вперёд (возраст = полных лет + 0..4):
- год = год_рождения + возраст;
- персональное число года = свод(день + месяц + Σцифр года) → 1..9 + текст;
- Луна = Σ первых двух цифр (код_жизни / возраст);
- Солнце = Σ следующих двух цифр;
- «год на +/−» = Солнце − Луна → текст (−9..+9, иначе само число).

Сверено с эталоном книги (20.02.1990, сегодня 06.06.2026), нулевой допуск.

Реализовано дополнительно:
- «судьбоносные события» Z (+/−): год в списке «судьбоносных годов» (цепочка
  aₙ₊₁ = aₙ + Σцифр(aₙ) от года рождения; в список идут якоря-концы блоков и
  годы-повторы, где прибавлялся 0). Matr!D ← MATCH(год, BK9:48).
- «энергетический потенциал» J: знак(energy[A] − energy[A−2]) по энергокривой
  (кусочно-линейная, опоры = первые 5 цифр кода жизни на возрастах 0,7,14,21,28,…).
- опасный возраст: первый возраст ≥ текущего, где Солнце года = 0 (Matr!F8).

- «12-летний цикл перерождения» AF/Matr!AH: те же первые 5 цифр кода жизни, но шаг
  каждые 12 лет — AH(возраст) = digits5[(возраст//12) % 5]; текст показывается при Z="+".
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

# 12-летний цикл перерождения (Matr!AH 0..9) → текст (РАСЧЕТ AF-колонка).
REBIRTH_CYCLE_TEXT = {
    0: "0 - максимальное зло, как по времени, так и по силе",
    1: "1 - добро минимально, как по времени, так и по силе",
    2: "2 - зло минимально, как по времени, так и по силе",
    3: "3 - добро минимально по силе, но довольно продолжительно",
    4: "4 - зло минимально по силе, но средняя продолжительность",
    5: "5 - кратковременное добро с максимальной силой (шок)",
    6: "6 - кратковременное зло с максимальной силой (шок)",
    7: "7 - слабое добро но довольно продолжительное (радость)",
    8: "8 - слабое зло, но довольно продолжительное",
    9: "9 - максимальное добро как по времени так и по силе",
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


def fate_years(birth_year: int, blocks: int = 10) -> set[int]:
    """Множество «судьбоносных годов» (Matr BK9:48).

    Цепочка от года рождения: к текущему значению по очереди прибавляются цифры
    «якорного» года (год рождения, затем каждый новый якорь). Каждый 4-й шаг —
    новый якорь (год + Σего цифр). В список идут якоря и годы-повторы (где
    прибавляемая цифра = 0, значение не изменилось).
    """
    bj = birth_year
    source = birth_year
    fate: set[int] = set()
    for _ in range(blocks):
        for i, ch in enumerate(f"{source:04d}"):
            new_bj = bj + int(ch)
            if i == 3 or new_bj == bj:  # якорь блока или год-повтор
                fate.add(new_bj)
            bj = new_bj
        source = bj
    return fate


def _energy_anchors(life_code: str) -> list[int]:
    """Опоры энергокривой = первые 5 цифр кода жизни (Matr BP9:BT9 = MID(код,1..5))."""
    return [int(c) for c in life_code[:5]]


def _energy(age: int, anchors: list[int]) -> float:
    """Энергопотенциал на возраст: линейная интерполяция между опорами каждые 7 лет."""
    seg, t = divmod(age, 7)
    lo = anchors[seg % 5]
    hi = anchors[(seg + 1) % 5]
    return lo + (hi - lo) * t / 7


def energy_potential(age: int, anchors: list[int]) -> int:
    """Тренд энергии (РАСЧЕТ J): знак(energy[A] − energy[A−2]); при равенстве —
    1 если energy[A−1] > 4, иначе 0."""
    diff = round(_energy(age, anchors) - _energy(age - 2, anchors), 2)
    if diff > 0:
        return 2
    if diff < 0:
        return -1
    return 1 if _energy(age - 1, anchors) > 4 else 0


def rebirth_cycle(age: int, anchors: list[int]) -> int:
    """12-летний цикл перерождения (Matr!AH): цифра кода жизни по блоку из 12 лет."""
    return anchors[(age // 12) % 5]


def current_energy_trend(person: PersonInput, reference_date: date | None = None) -> int:
    """Энергопотенциал на текущий возраст: тренд energy_potential (РАСЧЕТ J).

    2 — рост / на подъёме, −1 — на спаде, 1/0 — стабильно. Используется для
    блока «энергетический потенциал (на спаде / на подъёме)» в тарифах-прогнозах.
    """
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()
    age = relativedelta(reference_date, person.birth_date).years
    anchors = _energy_anchors(compute_codes(person, reference_date)["life_code"])
    return energy_potential(age, anchors)


def life_code_graph_digit(life_code: str, age: int) -> int:
    """Цифра «графика кода жизни» на возраст (лист 19, сверено с формулами).

    F37 = INDEX(AR32-цифры, MAX(MATCH возраста в сетке F22:K34)). Сетка — возрасты
    0–77 по 6 в ряд (строка = age//6, колонка = age%6), AR32 = AN11 = код жизни.
    Итог: активная цифра = код_жизни[age % 6]. Описание — текст!B213:C222 (0–9).
    """
    return int(life_code[age % 6])


def danger_age(person: PersonInput, reference_date: date) -> int | None:
    """Опасный возраст: первый возраст ≥ текущего с Солнцем года = 0 (Matr!F8)."""
    life_code = int(compute_codes(person, reference_date)["life_code"])
    current_age = relativedelta(reference_date, person.birth_date).years
    for age in range(current_age, 100):
        if _moon_sun(life_code, age)[1] == 0:
            return age
    return None


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
    fate: str  # судьбоносное событие: "+" / "-"
    energy_potential: int  # тренд энергии: 2 рост / -1 спад / 1 / 0
    rebirth_cycle: int  # 12-летний цикл перерождения (0..9)
    rebirth_cycle_text: str  # текст цикла; пусто, если fate != "+"

    def as_dict(self) -> dict:
        return asdict(self)


def compute_forecast(person: PersonInput, reference_date: date | None = None) -> list[dict]:
    """Прогноз на 5 лет вперёд от текущего возраста. Список из 5 записей."""
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()

    current_age = relativedelta(reference_date, person.birth_date).years
    life_code_str = compute_codes(person, reference_date)["life_code"]
    life_code = int(life_code_str)
    fate = fate_years(person.birth_date.year)
    anchors = _energy_anchors(life_code_str)

    out: list[dict] = []
    for i in range(FORECAST_YEARS):
        age = current_age + i
        year = person.birth_date.year + age
        moon, sun = _moon_sun(life_code, age)
        value = sun - moon
        py = personal_year(person, year)
        is_fateful = year in fate
        cycle = rebirth_cycle(age, anchors)
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
                fate="+" if is_fateful else "-",
                energy_potential=energy_potential(age, anchors),
                rebirth_cycle=cycle,
                rebirth_cycle_text=REBIRTH_CYCLE_TEXT.get(cycle, "") if is_fateful else "",
            ).as_dict()
        )
    return out


def compute_matrix(person: PersonInput) -> dict:
    """Совместимость: вернуть прогноз на 5 лет (остальные блоки Matr — позже)."""
    return {"forecast": compute_forecast(person)}
