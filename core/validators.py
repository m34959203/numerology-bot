"""Валидация ввода анкеты (FSM). Чистые функции, без Telegram. Ошибки локализуются."""

from __future__ import annotations

import re
from datetime import date, datetime

from core.i18n import t

# Допустимый алфавит имени: кириллица (вкл. казахские) + латиница (для en/имён
# латиницей), дефис, пробел, апостроф.
_NAME_RE = re.compile(r"^[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІіA-Za-z\- ']+$")
_MAX_NAME = 60


class ValidationError(ValueError):
    """Ошибка валидации ввода анкеты (текст — пользователю)."""


def parse_birth_date(text: str, locale: str = "ru") -> date:
    """Разобрать дату формата ДД.ММ.ГГГГ. Реальная, не из будущего, год ≥ 1900."""
    text = text.strip()
    if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", text):
        raise ValidationError(t("val.date_format", locale).format(example="14.03.1992"))
    try:
        d = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError as e:
        raise ValidationError(t("val.date_invalid", locale)) from e
    if d.year < 1900:
        raise ValidationError(t("val.birth_year_min", locale))
    if d > date.today():
        raise ValidationError(t("val.birth_future", locale))
    return d


def parse_target_date(text: str, locale: str = "ru") -> date:
    """Разобрать произвольную дату ДД.ММ.ГГГГ (для прогноза на день — допускается
    будущее, год 1900–2100). Без ограничения «не из будущего»."""
    text = text.strip()
    if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", text):
        raise ValidationError(t("val.date_format", locale).format(example="25.12.2026"))
    try:
        d = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError as e:
        raise ValidationError(t("val.date_invalid", locale)) from e
    if not (1900 <= d.year <= 2100):
        raise ValidationError(t("val.year_range", locale))
    return d


def validate_name(text: str, field: str, locale: str = "ru") -> str:
    """Проверить имя/фамилию/отчество: непустое, допустимый алфавит. `field` —
    уже локализованная подпись поля (для текста ошибки)."""
    name = " ".join(text.strip().split())
    if not name:
        raise ValidationError(t("val.name_empty", locale).format(field=field))
    if len(name) > _MAX_NAME:
        raise ValidationError(t("val.name_long", locale).format(field=field, max=_MAX_NAME))
    if not _NAME_RE.fullmatch(name):
        raise ValidationError(t("val.name_alpha", locale).format(field=field))
    return name
