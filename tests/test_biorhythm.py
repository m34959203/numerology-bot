"""Сверка биоритмов с Excel (лист Bio). Этап 2."""

from datetime import date

import pytest

from core.numerology import PersonInput
from core.numerology.biorhythm import compute_biorhythm

PERSON = PersonInput("Иванов", "Иван", "Иванович", date(1990, 5, 15))


def test_biorhythm_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        compute_biorhythm(PERSON)


@pytest.mark.skip(reason="Этап 2: нужны контрольные примеры + горизонт дней")
def test_biorhythm_matches_excel(): ...
