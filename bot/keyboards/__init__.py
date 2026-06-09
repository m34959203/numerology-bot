"""Инлайн-клавиатуры бота."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts
from bot.catalog_data import format_price


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BTN_SERVICES, callback_data="menu:services")],
            [
                InlineKeyboardButton(text=texts.BTN_MY_RESULTS, callback_data="menu:results"),
                InlineKeyboardButton(text=texts.BTN_HELP, callback_data="menu:help"),
            ],
        ]
    )


def services_kb(services) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{s.title} · {format_price(s.price_tenge)}", callback_data=f"svc:{s.id}"
            )
        ]
        for s in services
    ]
    rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_card_kb(service_id: int, price_tenge: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{texts.BTN_PAY} · {format_price(price_tenge)}",
                    callback_data=f"pay:{service_id}",
                )
            ],
            [InlineKeyboardButton(text=texts.BTN_BACK, callback_data="menu:services")],
        ]
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BTN_CONFIRM, callback_data="survey:confirm")],
            [InlineKeyboardButton(text=texts.BTN_RESTART, callback_data="survey:restart")],
        ]
    )


def to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=texts.BTN_TO_MENU, callback_data="menu:main")]]
    )
