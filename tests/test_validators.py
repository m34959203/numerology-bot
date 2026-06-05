"""Валидация анкеты."""

from datetime import date, timedelta

import pytest

from core.validators import ValidationError, parse_birth_date, validate_name


def test_parse_birth_date_ok():
    assert parse_birth_date("14.03.1992") == date(1992, 3, 14)
    assert parse_birth_date("1.1.2000") == date(2000, 1, 1)


def test_parse_birth_date_bad_format():
    for bad in ["2000-01-01", "32.13.1990", "abc", "14/03/1992", "14.03.90"]:
        with pytest.raises(ValidationError):
            parse_birth_date(bad)


def test_parse_birth_date_future_and_old():
    future = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
    with pytest.raises(ValidationError):
        parse_birth_date(future)
    with pytest.raises(ValidationError):
        parse_birth_date("01.01.1800")


def test_validate_name():
    assert validate_name("  Иванов  ", "Фамилия") == "Иванов"
    assert validate_name("Әбілқайыр", "Имя")  # казахские буквы допустимы
    for bad in ["", "John123", "Ivan!", "123"]:
        with pytest.raises(ValidationError):
            validate_name(bad, "Имя")
