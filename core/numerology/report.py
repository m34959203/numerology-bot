"""Сборка итогового отчёта (лист РАСЧЕТ).

Собирает результаты расчётных модулей и сопоставляет с текстами-трактовками
из core.content (листы «текст», 1–36). Структура разделов — раздел 2 ТЗ.

Реализованы (Этап 2): блок «Психоматрица» (+ скаляры: число души, уровень
сознания, ЧЖП, код поведения) и блок «Дни» (биоритмы). Блоки «Вычисления»
и «Прогноз на 5 лет» зависят от листа Matr (этапы 3–4) и подключаются позже.
"""

from __future__ import annotations

from datetime import date

from core.content.loader import interpret
from core.numerology.biorhythm import compute_biorhythm
from core.numerology.codes import compute_codes
from core.numerology.matrix import compute_forecast, danger_age
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


def build_report(person: PersonInput, reference_date: date | None = None) -> dict:
    """Собрать доступную часть отчёта. Остаток Matr (опасный возраст,
    судьбоносные события, 12-цикл, энергопотенциал) — позже."""
    return {
        "calculations": build_calculations_section(person, reference_date),
        "psychomatrix": build_psychomatrix_section(person),
        "days": build_biorhythm_section(person, reference_date),
        "forecast": build_forecast_section(person, reference_date),
    }
