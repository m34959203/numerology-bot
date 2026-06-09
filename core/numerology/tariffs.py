"""Дифференциация тарифов по контенту отчёта.

Каждому коду услуги (см. bot.catalog_data.DEFAULT_SERVICES) сопоставлен набор
секций отчёта и глубина прогноза. Все расчёты — из единого однопользовательского
движка (core.numerology), тариф лишь выбирает, какие блоки показать.

ВАЖНО: «Совместимость» (compatibility) в Excel-источнике ОТСУТСТВУЕТ — все 50
листов считают одного человека, методики парного расчёта нет. До получения
методики от заказчика тариф отдаёт полный однопользовательский разбор (fallback),
см. docs/OPEN_QUESTIONS.md. Не выдумывать формулу совместимости (правило проекта:
Excel — источник истины).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.numerology.person import PersonInput
from core.numerology.report import ALL_SECTIONS, build_report


@dataclass(frozen=True)
class TariffSpec:
    """Набор секций отчёта и глубина прогноза для одного тарифа."""

    sections: frozenset[str]
    forecast_years: int = 5  # 0 — не урезать прогноз


# Сопоставление code услуги → состав отчёта. Описания тарифов — в catalog_data.
TARIFFS: dict[str, TariffSpec] = {
    # Краткий разбор личности: психоматрица + коды от даты + число/карма имени.
    "matrix_mini": TariffSpec(
        sections=frozenset({"calculations", "psychomatrix", "name", "karma_events"}),
        forecast_years=0,
    ),
    # Прогноз на год: личные числа, Луна/Солнце по месяцам, дни, текущий год.
    "forecast_1y": TariffSpec(
        sections=frozenset({"calculations", "days", "moon_sun", "forecast"}),
        forecast_years=1,
    ),
    # Прогноз на 5 лет: то же, но полная пятилетняя динамика.
    "forecast_5y": TariffSpec(
        sections=frozenset({"calculations", "days", "moon_sun", "forecast"}),
        forecast_years=5,
    ),
    # Полный разбор: все секции.
    "matrix_full": TariffSpec(sections=frozenset(ALL_SECTIONS), forecast_years=5),
    # Совместимость: до методики заказчика — полный разбор (fallback, см. модульный docstring).
    "compatibility": TariffSpec(sections=frozenset(ALL_SECTIONS), forecast_years=5),
}

# Тариф по умолчанию для неизвестного кода — полный разбор (безопасный максимум).
DEFAULT_SPEC = TARIFFS["matrix_full"]


def spec_for(code: str | None) -> TariffSpec:
    """Спецификация тарифа по коду услуги; неизвестный код → полный разбор."""
    return TARIFFS.get(code or "", DEFAULT_SPEC)


def report_for(person: PersonInput, reference_date: date | None, code: str | None) -> dict:
    """Собрать отчёт под конкретный тариф (по code услуги)."""
    spec = spec_for(code)
    return build_report(
        person,
        reference_date,
        sections=set(spec.sections),
        forecast_years=spec.forecast_years,
    )
