"""Загрузка трактовок из выгруженных данных (core/content/data).

Тексты выгружаются из Excel скриптом scripts/extract_texts.py в JSON,
здесь — только чтение и сопоставление «ключ расчёта -> текст».
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


@cache
def load_section(name: str) -> dict:
    """Прочитать JSON-файл трактовок раздела (например, "psychomatrix")."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Нет данных трактовок: {path}. Сначала запустите scripts/extract_texts.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))
