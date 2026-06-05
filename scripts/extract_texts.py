"""Выгрузка текстов-трактовок из Excel в core/content/data/*.json.

Использование:
    pip install -e ".[excel]"
    python scripts/extract_texts.py --src ПРОГРАММА_МАТРИЦА_на_русском.xlsx --out core/content/data

Логика заполняется на Этапе 2: какие листы («текст», 1–36) и по какому
ключу сопоставляются с результатами расчёта. Сейчас — каркас CLI.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def extract(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    raise NotImplementedError(
        "Этап 2: распарсить листы трактовок ('текст', 1–36) и записать JSON в out"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Выгрузка трактовок из Excel в JSON")
    parser.add_argument("--src", required=True, type=Path, help="путь к .xlsx")
    parser.add_argument(
        "--out", default=Path("core/content/data"), type=Path, help="каталог для JSON"
    )
    args = parser.parse_args()
    extract(args.src, args.out)


if __name__ == "__main__":
    main()
