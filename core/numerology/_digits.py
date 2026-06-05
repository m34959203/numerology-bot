"""Общие цифровые операции для расчётов (листы calc и Matr используют их идентично).

Дата раскладывается на 8 цифр: день(2), месяц(2, добивка 0 при однозначном), год(4).
Рабочие числа и пул цифр — основа и психоматрицы (calc), и кодов (Matr).
"""

from __future__ import annotations

from datetime import date


def digit_sum(n: int) -> int:
    """Сумма цифр числа (один проход), как MID(..,1)+MID(..,2)+… в Excel."""
    return sum(int(c) for c in str(abs(n)))


def reduce_1_9(n: int) -> int:
    """Свод к 1..9 как VLOOKUP по таблице (= ((n-1) mod 9)+1). Мастер-числа не хранятся."""
    return (n - 1) % 9 + 1 if n > 0 else 0


def date_digits(d: date) -> list[int]:
    """8 цифр даты: день(2), месяц(2, 0 при однозначном), год(4)."""
    day = str(d.day)
    month = str(d.month)
    year = f"{d.year:04d}"
    return [
        int(day[0]),
        int(day[1]) if len(day) == 2 else 0,
        int(month[0]),
        int(month[1]) if len(month) == 2 else 0,
        *(int(c) for c in year),
    ]


def working_numbers(dd: list[int]) -> tuple[int, int, int, int]:
    """Четыре рабочих числа E18..E21 по 8 цифрам даты (лист calc / Matr).

    E18 = Σ8 цифр; E19 = свод E18; E20 = E18 − 2×(первая ненулевая цифра дня)
    (спец-ветка при <0); E21 = свод E20.
    """
    e18 = sum(dd)
    e19 = digit_sum(e18)
    first_day_digit = dd[0] if dd[0] > 0 else dd[1]
    subtract = first_day_digit * 2
    e20 = e18 - subtract if (e18 - subtract) >= 0 else (dd[0] - subtract) * -1
    e21 = digit_sum(e20)
    return e18, e19, e20, e21


def digit_pool(d: date) -> list[int]:
    """Полный пул цифр: 8 цифр даты + цифры строки рабочих чисел (concat E18..E21)."""
    dd = date_digits(d)
    e18, e19, e20, e21 = working_numbers(dd)
    working = [int(c) for c in f"{e18}{e19}{e20}{e21}"]
    return dd + working
