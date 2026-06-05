"""Инлайн-клавиатуры бота."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BTN_SERVICES, callback_data="menu:services")],
            [InlineKeyboardButton(text=texts.BTN_MY_RESULTS, callback_data="menu:results")],
            [InlineKeyboardButton(text=texts.BTN_HELP, callback_data="menu:help")],
        ]
    )


def services_kb(services) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{s.title} — {s.price_stars}⭐", callback_data=f"svc:{s.id}")]
        for s in services
    ]
    rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_card_kb(service_id: int, price_stars: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{texts.BTN_PAY} ({price_stars}⭐)", callback_data=f"pay:{service_id}"
                )
            ],
            [InlineKeyboardButton(text=texts.BTN_BACK, callback_data="menu:services")],
        ]
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно, рассчитать", callback_data="survey:confirm")],
            [InlineKeyboardButton(text=texts.BTN_RESTART, callback_data="survey:restart")],
        ]
    )
