"""Число имени и карма имени (блок ФИО листа Matr, ячейки D3–D7).

Источник истины: лист Excel «Matr». Зависит ТОЛЬКО от ФИО (не от даты).
Транслитерация сверена с книгой по таблице Matr!BJ1:CP2 (33 буквы, цикл 1–9):
буква → ((позиция_в_алфавите − 1) mod 9) + 1, где алфавит — полные 33 буквы
с Ё (поз. 7), Й (11), Ъ (28), Ы (29), Ь (30). Ё/Й/Ъ/Ь — ОТДЕЛЬНЫЕ буквы,
не сливаются с Е/И и не выкидываются.

Алгоритмы (см. docs/excel-analysis.md M.7):
- число части ФИО (D3 фамилия, D4 имя, D5 отчество, D6 девичья) =
  цифровой корень суммы цифр букв части (свод к 1..9); пусто → 0;
- карма имени D7 = D3 + D4 + D5 (фамилия+имя+отчество; девичья НЕ входит),
  БЕЗ дальнейшего свода → может быть 13/14/16/19;
- флаг кармы: D7 ∈ {13, 14, 16, 19}. В книге формула E7/AN17 = «…=OR(13,14,16,19)»
  содержит баг (всегда «нет») — здесь канонический пересчёт.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from core.numerology._digits import reduce_1_9
from core.numerology.person import PersonInput

# Полный русский алфавит (33 буквы), порядок = лист Matr BJ1:CP1.
_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
# буква → цифра 1..9 по позиции (циклично), как Matr!BJ2:CP2.
_LETTER_DIGIT = {ch: i % 9 + 1 for i, ch in enumerate(_ALPHABET)}

# Кармические числа имени (D7), при которых карма «есть».
KARMA_NUMBERS = frozenset({13, 14, 16, 19})


def _part_number(part: str | None) -> int:
    """Число части ФИО (D3–D6): свод суммы цифр букв к 1..9. Пусто → 0.

    Не-буквы (пробелы, дефисы) дают 0 и не влияют на сумму. Регистр игнорируется,
    но Ё/Е и Й/И НЕ нормализуются — книга считает их разными буквами.
    """
    if not part:
        return 0
    total = sum(_LETTER_DIGIT.get(ch, 0) for ch in part.upper())
    return reduce_1_9(total)


@dataclass(frozen=True)
class NameNumbers:
    last_name: int  # D3 число фамилии
    first_name: int  # D4 число имени
    middle_name: int  # D5 число отчества
    maiden_name: int  # D6 число девичьей фамилии
    karma: int  # D7 карма имени (D3+D4+D5)
    has_karma: bool  # канонический флаг (D7 ∈ {13,14,16,19})

    def as_dict(self) -> dict:
        return asdict(self)


def compute_name_numbers(person: PersonInput) -> dict:
    """Числа ФИО по листу «Matr» (D3–D7). Зависит только от ФИО."""
    d3 = _part_number(person.last_name)
    d4 = _part_number(person.first_name)
    d5 = _part_number(person.middle_name)
    d6 = _part_number(person.maiden_name)
    karma = d3 + d4 + d5
    return NameNumbers(
        last_name=d3,
        first_name=d4,
        middle_name=d5,
        maiden_name=d6,
        karma=karma,
        has_karma=karma in KARMA_NUMBERS,
    ).as_dict()
