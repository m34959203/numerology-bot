"""Загрузка трактовок из core/content/data/texts/*.json.

Тексты выгружаются из листа «текст» скриптом scripts/extract_texts.py.
Здесь — только чтение и сопоставление «значение расчёта → текст(ы)».

Лукап повторяет VLOOKUP(...,FALSE) числовых листов книги: точное совпадение
ключа. Для психоматрицы значение 0 в книге отображается как «нет» (РАСЧЕТ
оборачивает клетку в IF(...>0,...,"нет")) — это учитывается в report.py.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

_TEXTS_DIR = Path(__file__).parent / "data" / "texts"


@cache
def _load_topic(topic: str) -> dict:
    path = _TEXTS_DIR / f"{topic}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Нет трактовок темы {topic!r}: {path}. Запустите scripts/extract_texts.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def interpret(topic: str, key: str) -> str | list[str] | None:
    """Вернуть трактовку темы по ключу (точное совпадение, как VLOOKUP FALSE).

    Для мультиаспектных тем (ЧЖП, число души) возвращается список абзацев.
    None — если ключа нет в таблице.
    """
    return _load_topic(topic).get(str(key).strip())
