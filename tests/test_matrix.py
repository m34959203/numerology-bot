"""Сверка ядра матрицы с Excel (лист Matr). Этап 4."""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.matrix import compute_matrix

PERSON = PersonInput("Иванов", "Иван", "Иванович", date(1990, 5, 15))


def test_matrix_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        compute_matrix(PERSON)
