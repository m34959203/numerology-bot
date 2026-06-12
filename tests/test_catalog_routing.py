"""Маршрутизация карточки услуги: все тарифы (включая ручные детские/совместимость)
оплачиваются в боте — карточка ведёт на оплату, а не на контакт мастера."""

from __future__ import annotations

from bot import keyboards
from core.numerology.tariffs import spec_for


def _buttons(kb):
    return [btn for row in kb.inline_keyboard for btn in row]


def test_manual_card_shows_pay_button():
    # Ручной тариф (children) теперь тоже оплачивается в боте звёздами.
    assert spec_for("children").manual is True
    kb = keyboards.service_card_kb(1, 5000)
    action = _buttons(kb)[0]
    assert action.callback_data == "pay:1"
    assert action.url is None


def test_auto_card_shows_pay_button():
    kb = keyboards.service_card_kb(7, 10000)
    action = _buttons(kb)[0]
    assert action.callback_data == "pay:7"
    assert action.url is None
