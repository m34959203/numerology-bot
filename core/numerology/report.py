"""Сборка итогового отчёта (лист РАСЧЕТ).

Собирает результаты расчётных модулей и сопоставляет с текстами-трактовками
из core.content (листы «текст», 1–36). Структура разделов — раздел 2 ТЗ.

Все разделы перенесены: «Вычисления» (коды), «Психоматрица», «Число и карма
имени», «Кармические события», «Дни» (биоритмы), «Прогноз на 5 лет», «Луна и
Солнце по месяцам» + личные числа. Расчётный слой по таблице закрыт на 100%.
"""

from __future__ import annotations

from datetime import date

from core.content.loader import interpret
from core.numerology.biorhythm import compute_biorhythm
from core.numerology.codes import compute_codes
from core.numerology.karma_events import compute_karma_events
from core.numerology.matrix import (
    compute_forecast,
    current_energy_trend,
    danger_age,
    life_code_graph_digit,
)
from core.numerology.moon_sun import compute_monthly_moon_sun, compute_personal_numbers
from core.numerology.name import compute_name_numbers
from core.numerology.person import PersonInput
from core.numerology.psychomatrix import compute_psychomatrix

# (поле психоматрицы, подпись, тема трактовки). 0 → ключ «нет» (как в РАСЧЕТ).
_PSYCHO_ROWS: list[tuple[str, str, str]] = [
    ("character", "Характер", "character"),
    ("energy", "Энергия", "energy"),
    ("interest", "Интерес", "interest"),
    ("health", "Здоровье", "health"),
    ("logic", "Логика, интуиция", "logic"),
    ("labor", "Труд, власть", "labor"),
    ("luck", "Везение", "luck"),
    ("duty", "Чувство долга", "duty"),
    ("memory", "Ум, память", "memory"),
    ("self_esteem", "Самооценка", "self_esteem"),
    ("attitude_to_labor", "Отношение к труду", "attitude_to_labor"),
    ("purposefulness", "Целеустремлённость", "purposefulness"),
    ("family_quality", "Качество семьянина", "family_quality"),
    ("stability", "Стабильность", "stability"),
    ("temperament", "Темперамент", "temperament"),
]


def _psycho_key(value: int) -> str:
    """Ключ лукапа клетки психоматрицы: 0 → «нет», иначе число (как в РАСЧЕТ)."""
    return "нет" if value == 0 else str(value)


def build_psychomatrix_section(person: PersonInput) -> dict:
    """Блок «Психоматрица» с трактовками (листы calc + 1–17, 20–23)."""
    pm = compute_psychomatrix(person)

    qualities = []
    for field, label, topic in _PSYCHO_ROWS:
        value = pm[field]
        qualities.append(
            {
                "label": label,
                "value": value,
                "text": interpret(topic, _psycho_key(value)),
            }
        )

    scalars = [
        {
            "label": "Число души",
            "value": pm["soul_number"],
            "text": interpret("soul_number", pm["soul_number"]),
        },
        {
            "label": "Уровень сознания",
            "value": pm["consciousness_level"],
            "text": interpret("consciousness_level", pm["consciousness_level"]),
        },
        {
            "label": "Число жизненного пути (ЧЖП)",
            "value": pm["life_path"],
            "text": interpret("life_path", pm["life_path"]),
        },
        {
            "label": "Код поведения",
            "value": pm["behavior_code"],
            "text": interpret("behavior_code", pm["behavior_code"]),
        },
        {"label": "Код жизни", "value": pm["life_code"], "text": None},
    ]
    return {"qualities": qualities, "scalars": scalars}


def build_biorhythm_section(person: PersonInput, reference_date: date | None = None) -> dict:
    """Блок «Дни»: благоприятные / критические / травмоопасные (лист Bio)."""
    bio = compute_biorhythm(person, reference_date)
    return {
        "reference_date": bio["reference_date"],
        "favorable": bio["favorable"],
        "critical": bio["critical"],
        "traumatic": bio["traumatic"],
    }


def build_calculations_section(person: PersonInput, reference_date: date | None = None) -> dict:
    """Блок «Вычисления» (коды от даты, лист Matr → РАСЧЕТ AN6..AN16)."""
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()
    section = compute_codes(person, reference_date)
    section["danger_age"] = danger_age(person, reference_date)
    section["energy_trend"] = current_energy_trend(person, reference_date)
    # «Код жизни» в РАСЧЕТ — это число (AN11=Matr!BI7), а ячейка ссылается на
    # описание = лист 19 «График кода жизни»: D36=VLOOKUP(F37, текст!B213:C222),
    # где F37=INDEX(код_жизни_цифры, age%6) — активная цифра графика за текущий
    # возраст. Канонический ярлык блока — «График кода жизни» (текст!B212).
    # Разворачиваем эту ссылку инлайном под числом (фидбэк заказчицы 11.06.2026).
    graph_digit = life_code_graph_digit(section["life_code"], section["full_years"])
    section["life_code_graph_digit"] = graph_digit
    section["life_code_graph_text"] = interpret("life_force_graph", graph_digit)
    # Кодировки «до/после 35» (лист 18): 1-код = human_code, 2-код = second_code;
    # оба трактуются по таблице кодировок (текст!B155:C210 = human_code.json).
    section["human_code_text"] = interpret("human_code", section["human_code"])
    section["second_code_text"] = interpret("human_code", section["second_code"])
    return section


def build_forecast_section(person: PersonInput, reference_date: date | None = None) -> list[dict]:
    """Блок «Прогноз на 5 лет» (Matr 29–33 → РАСЧЕТ).

    Каждый год обогащается трактовками по ЕГО значениям (лукап из листа «текст»,
    меняется вместе со значением): Луна/Солнце/ИТОГ года и цифра графика кода жизни.
    Солнце=0 → текст «нулевого периода». matrix.compute_forecast остаётся чистым.
    """
    years = compute_forecast(person, reference_date)
    life_code = compute_codes(person, reference_date)["life_code"]
    for y in years:
        # ИТОГ года — сверено с книгой: лист 29-33 D6 = VLOOKUP(Matr!H29..33, текст!H363:I401),
        # где Matr!H = Солнце−Луна = наш year_value (точное совпадение на эталоне).
        y["total_text"] = interpret("year_total", y["year_value"])
        # «Нулевой период» (Солнце=0) — текст-справка из таблицы Солнца (текст!F382),
        # выводим по запросу заказчика (в книге как отдельный per-год лукап не выводится).
        y["sun_text"] = interpret("sun_year", y["sun"])
        # График кода жизни: активная цифра = код_жизни[age % 6] (лист 19, сверено).
        digit = life_code_graph_digit(life_code, y["age"])
        y["life_force_digit"] = digit
        y["life_force_text"] = interpret("life_force_graph", digit)
    return years


def build_moon_sun_section(
    person: PersonInput, reference_date: date | None = None, *, span_years: int = 1
) -> dict:
    """Блоки «Луна и Солнце по месяцам» и «ЧПГ/ЧПМ/ЧПД» (Этап 5).

    span_years — на сколько лет вперёд считать помесячную Луну/Солнце (по фидбэку
    заказчицы 11.06.2026 пятилетний прогноз показывает её на все годы). Ключ
    "monthly" всегда = текущий год (обратная совместимость рендера/PDF); полный
    набор лет — в "monthly_years" = [{"year", "monthly"}].
    """
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()
    from dateutil.relativedelta import relativedelta

    span = max(1, span_years)
    monthly_years = [
        {
            "year": (ref_i := reference_date + relativedelta(years=i)).year,
            "monthly": compute_monthly_moon_sun(person, ref_i),
        }
        for i in range(span)
    ]
    return {
        "monthly": monthly_years[0]["monthly"],
        "monthly_years": monthly_years,
        "personal_numbers": compute_personal_numbers(person, reference_date),
    }


# Все секции отчёта в каноническом порядке (порядок рендера).
ALL_SECTIONS: tuple[str, ...] = (
    "calculations",
    "psychomatrix",
    "name",
    "karma_events",
    "days",
    "forecast",
    "moon_sun",
)


def build_report(
    person: PersonInput,
    reference_date: date | None = None,
    *,
    sections: set[str] | None = None,
    forecast_years: int = 5,
) -> dict:
    """Собрать отчёт. 12-летний цикл учтён в прогнозе. Кармические события
    (BG17/BG20) требуют дат родителей — без них секции пустые (как в книге).

    sections — какие блоки включить (по умолчанию все; используется для
    дифференциации тарифов, см. core.numerology.tariffs). forecast_years
    ограничивает «Прогноз на N лет» (0 не урезает; книга считает 5).
    """
    want = (lambda key: True) if sections is None else (sections.__contains__)
    report: dict = {}
    if want("calculations"):
        report["calculations"] = build_calculations_section(person, reference_date)
    if want("psychomatrix"):
        report["psychomatrix"] = build_psychomatrix_section(person)
    if want("name"):
        report["name"] = compute_name_numbers(person)
    if want("karma_events"):
        report["karma_events"] = compute_karma_events(person)
    if want("days"):
        report["days"] = build_biorhythm_section(person, reference_date)
    if want("forecast"):
        forecast = build_forecast_section(person, reference_date)
        report["forecast"] = forecast[:forecast_years] if forecast_years else forecast
    if want("moon_sun"):
        report["moon_sun"] = build_moon_sun_section(
            person, reference_date, span_years=forecast_years or 1
        )
    return report
