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
from core.numerology.matrix import compute_forecast, danger_age
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
    return section


def build_forecast_section(person: PersonInput, reference_date: date | None = None) -> list[dict]:
    """Блок «Прогноз на 5 лет» (Matr 29–33 → РАСЧЕТ)."""
    return compute_forecast(person, reference_date)


def build_moon_sun_section(person: PersonInput, reference_date: date | None = None) -> dict:
    """Блоки «Луна и Солнце по месяцам» и «ЧПГ/ЧПМ/ЧПД» (Этап 5)."""
    if reference_date is None:
        from datetime import UTC, datetime

        reference_date = datetime.now(UTC).date()
    return {
        "monthly": compute_monthly_moon_sun(person, reference_date),
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
        report["moon_sun"] = build_moon_sun_section(person, reference_date)
    return report
