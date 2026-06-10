"""Валидация ввода анкеты (FSM). Чистые функции, без Telegram."""

from __future__ import annotations

import re
from datetime import date, datetime

# Допустимый алфавит имени: кириллица (вкл. казахские), дефис, пробел, апостроф.
_NAME_RE = re.compile(r"^[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі\- ']+$")
_MAX_NAME = 60


class ValidationError(ValueError):
    """Ошибка валидации ввода анкеты (текст — пользователю)."""


def parse_birth_date(text: str) -> date:
    """Разобрать дату формата ДД.ММ.ГГГГ. Реальная, не из будущего, год ≥ 1900."""
    text = text.strip()
    if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", text):
        raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ, например 14.03.1992")
    try:
        d = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError as e:
        raise ValidationError("Такой даты не существует. Проверьте день и месяц.") from e
    if d.year < 1900:
        raise ValidationError("Год рождения должен быть не раньше 1900.")
    if d > date.today():
        raise ValidationError("Дата рождения не может быть в будущем.")
    return d


def parse_target_date(text: str) -> date:
    """Разобрать произвольную дату ДД.ММ.ГГГГ (для прогноза на день — допускается
    будущее, год 1900–2100). Без ограничения «не из будущего»."""
    text = text.strip()
    if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", text):
        raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ, например 25.12.2026")
    try:
        d = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError as e:
        raise ValidationError("Такой даты не существует. Проверьте день и месяц.") from e
    if not (1900 <= d.year <= 2100):
        raise ValidationError("Год должен быть в диапазоне 1900–2100.")
    return d


def validate_name(text: str, field: str) -> str:
    """Проверить имя/фамилию/отчество: непустое, допустимый алфавит."""
    name = " ".join(text.strip().split())
    if not name:
        raise ValidationError(f"{field} не может быть пустым.")
    if len(name) > _MAX_NAME:
        raise ValidationError(f"{field} слишком длинное (максимум {_MAX_NAME} символов).")
    if not _NAME_RE.fullmatch(name):
        raise ValidationError(f"{field}: допустимы только буквы (кириллица), дефис и пробел.")
    return name
