"""Маршрутизация карточки услуги: ручные тарифы (детские/совместимость) ведут
на контакт мастера, авто-тарифы — на оплату."""

from __future__ import annotations

from bot import keyboards
from core.numerology.tariffs import MASTER_CONTACT_URL, spec_for


def _buttons(kb):
    return [btn for row in kb.inline_keyboard for btn in row]


def test_manual_card_shows_contact_button():
    spec = spec_for("children")
    kb = keyboards.service_card_kb(1, 5000, spec.contact_url if spec.manual else None)
    action = _buttons(kb)[0]
    assert action.url == MASTER_CONTACT_URL
    assert action.callback_data is None  # не платёжная кнопка


def test_auto_card_shows_pay_button():
    spec = spec_for("matrix_full")
    kb = keyboards.service_card_kb(7, 10000, spec.contact_url if spec.manual else None)
    action = _buttons(kb)[0]
    assert action.callback_data == "pay:7"
    assert action.url is None
