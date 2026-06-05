"""Единый вход для всех расчётных модулей — данные анкеты."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PersonInput:
    """Нормализованные данные анкеты (вход листа РАСЧЕТ)."""

    last_name: str
    first_name: str
    middle_name: str | None
    birth_date: date
    mother_birth_date: date | None = None
    father_birth_date: date | None = None
    maiden_name: str | None = None
