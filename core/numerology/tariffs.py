"""Дифференциация тарифов по составу отчёта — выбор ПО ПОЛЯМ.

Каждому коду услуги (см. bot.catalog_data.DEFAULT_SERVICES) сопоставлен точный
набор атомарных блоков отчёта (FIELDS) и глубина прогноза. Состав блоков задан
спецификацией заказчика (WhatsApp, 10.06.2026) — один тариф = ровно перечисленные
им пункты, не больше. Все расчёты — из единого однопользовательского движка
(core.numerology); тариф лишь выбирает, какие блоки показать на рендере.

Гранулярность — поля, а не секции: например «Финансовый прогноз» показывает
только финансовый код + помесячный прогноз, а не весь блок «Вычисления».
Технически report_for собирает нужные секции build_report и прикрепляет к отчёту
ключ "_fields" (множество атомов); рендереры (core.render, core.pdf) показывают
под-блок только если его атом включён (см. _want в рендерах).

Ручные тарифы (manual=True) — «Детские матрицы» и «Совместимость» — не считаются
автоматически: бот направляет клиента на личный аккаунт мастера для ручной
обработки (методики парного/детского разбора в Excel-источнике нет, см.
docs/OPEN_QUESTIONS.md). Не выдумывать формулы (правило проекта: Excel — истина).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.content.loader import use_locale
from core.numerology.person import PersonInput
from core.numerology.report import build_report

# --- Атомарные блоки отчёта (поля) -----------------------------------------
# Психоматрица и скаляры от неё.
PSYCHOMATRIX = "psychomatrix"  # полное описание психоматрицы (15 качеств)
LIFE_PATH = "life_path"  # ЧЖП — число жизненного пути
SOUL_NUMBER = "soul_number"  # число души (рендерится только при возрасте < 30)
CONSCIOUSNESS = "consciousness"  # уровень сознания
BEHAVIOR_CODE = "behavior_code"  # код поведения
# Коды от даты (блок «Вычисления»).
LIFE_CODE = "life_code"  # код жизни
HUMAN_CODE = "human_code"  # кодировка жизни (код человека)
LUCKY_NUMBERS = "lucky_numbers"  # счастливые числа
VITALITY = "vitality"  # жизненные силы (число)
FINANCE_CODE = "finance_code"  # финансовый код удачи
DANGER_AGE = "danger_age"  # опасный возраст
ENERGY_TREND = "energy_trend"  # энергопотенциал сейчас: на спаде / на подъёме
# Имя, дни, динамика.
NAME_KARMA = "name_karma"  # число и карма имени
BIORHYTHM_DAYS = "biorhythm_days"  # благоприятные / критические / травмоопасные дни
FORECAST = "forecast"  # прогноз по годам (силы по годам, судьбоносные события)
# Луна/Солнце и личные числа.
MOON_SUN_MONTHLY = (
    "moon_sun_monthly"  # Луна и Солнце по месяцам / энергографик / прогноз по месяцам
)
PERSONAL_NUMBERS = "personal_numbers"  # ЧПМ и ЧПД на текущий месяц/день
PERSONAL_YEAR = "personal_year"  # персональное число года (ЧПГ)

# Атом → секция build_report, в которой лежат его данные.
_SECTION_OF: dict[str, str] = {
    PSYCHOMATRIX: "psychomatrix",
    LIFE_PATH: "psychomatrix",
    SOUL_NUMBER: "psychomatrix",
    CONSCIOUSNESS: "psychomatrix",
    BEHAVIOR_CODE: "psychomatrix",
    LIFE_CODE: "calculations",
    HUMAN_CODE: "calculations",
    LUCKY_NUMBERS: "calculations",
    VITALITY: "calculations",
    FINANCE_CODE: "calculations",
    DANGER_AGE: "calculations",
    ENERGY_TREND: "calculations",
    NAME_KARMA: "name",
    BIORHYTHM_DAYS: "days",
    FORECAST: "forecast",
    MOON_SUN_MONTHLY: "moon_sun",
    PERSONAL_NUMBERS: "moon_sun",
    PERSONAL_YEAR: "moon_sun",
}

# Полный набор атомов — для тарифа «Полный разбор» и безопасного дефолта.
ALL_FIELDS: frozenset[str] = frozenset(_SECTION_OF)


def sections_for(fields: frozenset[str]) -> set[str]:
    """Какие секции build_report нужно собрать для данного набора атомов."""
    return {_SECTION_OF[f] for f in fields}


@dataclass(frozen=True)
class TariffSpec:
    """Состав отчёта одного тарифа.

    fields — атомарные блоки (см. константы выше). forecast_years ограничивает
    «Прогноз на N лет» (0 — не показывать/не урезать). manual=True — авто-расчёта
    нет, клиента направляют на контакт мастера. needs_parents/needs_name —
    какие доп. поля анкеты собирать.
    """

    fields: frozenset[str]
    forecast_years: int = 0
    manual: bool = False
    needs_parents: bool = False
    needs_name: bool = False
    contact_url: str | None = None

    @property
    def sections(self) -> set[str]:
        """Секции build_report под этот тариф (для сборки и гейтинга анкеты)."""
        return sections_for(self.fields)


# Личный аккаунт мастера для ручной обработки детских и парных разборов.
MASTER_CONTACT_URL = "https://t.me/+bZiSEb_asXZkN2M1"


# Сопоставление code услуги → состав отчёта. Цены/описания — в bot.catalog_data.
TARIFFS: dict[str, TariffSpec] = {
    # Прогноз на 1 год: ЧЖП, код жизни/поведения, Луна-Солнце по месяцам, ЧПМ/ЧПД,
    # персональный год, энергопотенциал (спад/подъём), энергографик, биоритмы.
    "forecast_1y": TariffSpec(
        fields=frozenset(
            {
                LIFE_PATH,
                LIFE_CODE,
                BEHAVIOR_CODE,
                MOON_SUN_MONTHLY,
                PERSONAL_NUMBERS,
                PERSONAL_YEAR,
                ENERGY_TREND,
                BIORHYTHM_DAYS,
            }
        ),
        forecast_years=1,
    ),
    # Прогноз на 5 лет: то же + пятилетняя динамика по годам (силы/судьбоносные).
    "forecast_5y": TariffSpec(
        fields=frozenset(
            {
                LIFE_PATH,
                LIFE_CODE,
                BEHAVIOR_CODE,
                MOON_SUN_MONTHLY,
                PERSONAL_NUMBERS,
                PERSONAL_YEAR,
                ENERGY_TREND,
                BIORHYTHM_DAYS,
                FORECAST,
            }
        ),
        forecast_years=5,
    ),
    # Мини-разбор: психоматрица, ЧЖП, персональный год, дни, код поведения, сознание.
    "matrix_mini": TariffSpec(
        fields=frozenset(
            {
                PSYCHOMATRIX,
                LIFE_PATH,
                PERSONAL_YEAR,
                BIORHYTHM_DAYS,
                BEHAVIOR_CODE,
                CONSCIOUSNESS,
            }
        ),
        forecast_years=0,
    ),
    # Полный разбор: все 13 пунктов спецификации заказчика.
    "matrix_full": TariffSpec(
        fields=frozenset(
            {
                PSYCHOMATRIX,
                HUMAN_CODE,
                LIFE_CODE,
                LIFE_PATH,
                SOUL_NUMBER,
                BEHAVIOR_CODE,
                CONSCIOUSNESS,
                PERSONAL_YEAR,
                FORECAST,
                MOON_SUN_MONTHLY,
                FINANCE_CODE,
                DANGER_AGE,
                VITALITY,
                BIORHYTHM_DAYS,
            }
        ),
        forecast_years=5,
    ),
    # Финансовый прогноз на 1 год: финкод, помесячный прогноз, энергографик,
    # персональное число года (добавлено по фидбэку заказчицы 11.06.2026).
    # Заказчик: «обязательно укажите имя родителей и год рождения».
    "finance_1y": TariffSpec(
        fields=frozenset({FINANCE_CODE, MOON_SUN_MONTHLY, PERSONAL_YEAR}),
        forecast_years=0,
        needs_parents=True,
    ),
    # Детские матрицы — ручная обработка (методики детского разбора нет в Excel).
    "children": TariffSpec(
        fields=frozenset(),
        manual=True,
        contact_url=MASTER_CONTACT_URL,
    ),
    # Совместимость — ручная обработка (парного расчёта в Excel-источнике нет).
    "compatibility": TariffSpec(
        fields=frozenset(),
        manual=True,
        contact_url=MASTER_CONTACT_URL,
    ),
}

# Тариф по умолчанию для неизвестного кода — полный разбор (безопасный максимум):
# собираем все блоки и все доп. поля анкеты, чтобы ничего не потерять.
DEFAULT_SPEC = TariffSpec(
    fields=ALL_FIELDS,
    forecast_years=5,
    needs_parents=True,
    needs_name=True,
)


def spec_for(code: str | None) -> TariffSpec:
    """Спецификация тарифа по коду услуги; неизвестный код → полный разбор."""
    return TARIFFS.get(code or "", DEFAULT_SPEC)


def report_for(
    person: PersonInput, reference_date: date | None, code: str | None, locale: str = "ru"
) -> dict:
    """Собрать отчёт под конкретный тариф (по code услуги) на заданной локали.

    Возвращает структуру build_report с дополнительным ключом "_fields" —
    множеством атомов тарифа, по которому рендереры решают, что показать.
    Трактовки (interpret) собираются на `locale` (use_locale); недостающие на
    языке ключи — fallback на русский. Для ручных тарифов (manual) расчёта нет.
    """
    spec = spec_for(code)
    with use_locale(locale):
        report = build_report(
            person,
            reference_date,
            sections=spec.sections,
            forecast_years=spec.forecast_years,
        )
    report["_fields"] = sorted(spec.fields)
    return report
