"""Графики отчёта: серии данных сверены с книгой, отрисовка не падает."""

from __future__ import annotations

from core.charts import life_code_energy, life_force_curve, monthly_energy
from core.numerology.matrix import energy_curve, life_code_digits, monthly_energy_year


def test_life_code_digits():
    # Лист 19 F21:K21 для кода жизни 796000 (эталон Ерофеева Ю.В.).
    assert life_code_digits("796000") == [7, 9, 6, 0, 0, 0]
    # Короткий код добивается нулями слева до 6 знаков.
    assert life_code_digits("12") == [0, 0, 0, 0, 1, 2]


def test_energy_curve_matches_book_anchors():
    # Энергокривая Matr!BE59:BE158: опоры = первые 5 цифр кода жизни [7,9,6,0,0],
    # линейная интерполяция каждые 7 лет. Первые точки сверены с книгой.
    curve = energy_curve("796000", max_age=14)
    assert curve[0] == 7  # возраст 0 = первая опора
    assert curve[7] == 9  # возраст 7 = вторая опора
    assert curve[14] == 6  # возраст 14 = третья опора
    assert round(curve[1], 4) == round(7 + (9 - 7) / 7, 4)  # интерполяция 7→9
    assert len(curve) == 15


def test_monthly_energy_matches_book():
    # «Энергетический график на текущий год» (Matr!CC28:CO28), эталон Ерофеева Ю.В.
    # Реверс сверен с книгой 36/36; для 2026 (годобаза 1) anchors [7,9,6,0,0]:
    # Янв(поз11→anchor1=9)+1=10→1, Фев(0→7)+1=8, Мар(1→9)+1→1, Апр(2→6)+1=7 ...
    assert monthly_energy_year("796000", 1990, 2026) == [1, 8, 1, 7, 1, 1, 8, 1, 7, 1, 1, 8]
    # Годобаза для 2025 = ((2025-1990)%9)+1 = 9 → Фев: 7+9=16→7.
    assert monthly_energy_year("796000", 1990, 2025)[1] == 7


def test_charts_build_without_error():
    # Drawing-объекты строятся (reportlab.graphics) без исключений.
    d1 = life_force_curve(energy_curve("796000"), "Helvetica")
    d2 = life_code_energy(life_code_digits("796000"), "Helvetica")
    d3 = monthly_energy(monthly_energy_year("796000", 1990, 2026), "Helvetica")
    assert d1.width > 0 and d1.height > 0
    assert d2.width > 0 and d2.height > 0
    assert d3.width > 0 and d3.height > 0
