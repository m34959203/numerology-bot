"""Сверка психоматрицы с Excel (лист calc). Этап 2.

Контрольные примеры (вход -> эталон) добавляются в tests/fixtures от заказчика.
Пока модуль не реализован — фиксируем контракт.
"""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.psychomatrix import compute_psychomatrix

PERSON = PersonInput("Иванов", "Иван", "Иванович", date(1990, 5, 15))


def test_psychomatrix_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        compute_psychomatrix(PERSON)


@pytest.mark.skip(reason="Этап 2: нужны контрольные примеры из Excel")
def test_psychomatrix_matches_excel(): ...
