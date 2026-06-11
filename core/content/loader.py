"""Загрузка трактовок из core/content/data/texts/*.json.

Тексты выгружаются из листа «текст» скриптом scripts/extract_texts.py.
Здесь — только чтение и сопоставление «значение расчёта → текст(ы)».

Лукап повторяет VLOOKUP(...,FALSE) числовых листов книги: точное совпадение
ключа. Для психоматрицы значение 0 в книге отображается как «нет» (РАСЧЕТ
оборачивает клетку в IF(...>0,...,"нет")) — это учитывается в report.py.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_TEXTS_DIR = _DATA_DIR / "texts"  # русский — база (исторический путь)

# Базовый язык трактовок — русский (источник = Excel). Переводы лежат в
# data/texts_<locale>/ (kk, en). Текущая локаль — через ContextVar, чтобы не
# протаскивать её через все compute-функции; report_for выставляет её на сборку.
BASE_LOCALE = "ru"
_locale: ContextVar[str] = ContextVar("content_locale", default=BASE_LOCALE)


def set_locale(locale: str) -> None:
    """Выставить текущую локаль контента (для interpret в этом контексте)."""
    _locale.set(locale or BASE_LOCALE)


def current_locale() -> str:
    """Текущая локаль контента (ContextVar). Используется и i18n.t для хрома."""
    return _locale.get()


@contextmanager
def use_locale(locale: str):
    """Контекст-менеджер: на время блока interpret() читает трактовки на `locale`."""
    token = _locale.set(locale or BASE_LOCALE)
    try:
        yield
    finally:
        _locale.reset(token)


def _topic_dir(locale: str) -> Path:
    return _TEXTS_DIR if locale == BASE_LOCALE else _DATA_DIR / f"texts_{locale}"


@cache
def _load_topic(topic: str, locale: str) -> dict:
    path = _topic_dir(locale) / f"{topic}.json"
    if not path.exists():
        if locale == BASE_LOCALE:
            raise FileNotFoundError(
                f"Нет трактовок темы {topic!r}: {path}. Запустите scripts/extract_texts.py"
            )
        return {}  # перевода ещё нет → fallback на базовый язык (per-key ниже)
    return json.loads(path.read_text(encoding="utf-8"))


def interpret(topic: str, key: str) -> str | list[str] | None:
    """Вернуть трактовку темы по ключу (точное совпадение, как VLOOKUP FALSE).

    Локаль — из ContextVar (по умолчанию ru). Если на текущем языке ключа нет
    (тема не переведена / частичный перевод) — fallback на русский. Для
    мультиаспектных тем (ЧЖП, число души) возвращается список абзацев.
    """
    k = str(key).strip()
    loc = _locale.get()
    val = _load_topic(topic, loc).get(k)
    if val is None and loc != BASE_LOCALE:
        val = _load_topic(topic, BASE_LOCALE).get(k)
    return val


def interpret_prefixed(topic: str, number: int | str) -> str | list[str] | None:
    """Лукап по ведущему числу ключа: темы вида «N - заголовок» (напр. personal_year,
    где ключ = «2 - год взаимоотношения», а на входе только число 2). None — если нет.

    Ключи (RU-структура) едины для всех языков; значение берётся на текущей локали."""
    want = str(number).strip()
    loc = _locale.get()
    base = _load_topic(topic, BASE_LOCALE)
    localized = _load_topic(topic, loc) if loc != BASE_LOCALE else base
    for key in base:
        if key.split(" ", 1)[0] == want:
            return localized.get(key, base[key])
    return None
