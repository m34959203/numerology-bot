"""Инлайн-клавиатуры бота."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts
from bot.catalog_data import format_price
from core.i18n import LOCALE_FLAGS, LOCALE_NAMES, LOCALES, t


def main_menu(locale: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("ui.btn_services", locale), callback_data="menu:services"
                )
            ],
            [InlineKeyboardButton(text=t("ui.btn_daily", locale), callback_data="menu:daily")],
            [
                InlineKeyboardButton(
                    text=t("ui.btn_my_results", locale), callback_data="menu:results"
                ),
                InlineKeyboardButton(text=t("ui.btn_help", locale), callback_data="menu:help"),
            ],
            [InlineKeyboardButton(text=t("ui.btn_lang", locale), callback_data="menu:lang")],
        ]
    )


def lang_menu() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка (ru/kk/en)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{LOCALE_FLAGS[loc]} {LOCALE_NAMES[loc]}", callback_data=f"lang:{loc}"
                )
            ]
            for loc in LOCALES
        ]
    )


def daily_today_kb() -> InlineKeyboardMarkup:
    """Клавиатура шага «дата прогноза»: быстрый выбор «Сегодня»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=texts.BTN_TODAY, callback_data="daily:today")]]
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


def service_card_kb(
    service_id: int, price_tenge: int, contact_url: str | None = None
) -> InlineKeyboardMarkup:
    """Карточка услуги. Для ручных тарифов (contact_url) — кнопка контакта мастера
    вместо оплаты (детские/совместимость считаются вручную)."""
    if contact_url:
        action = InlineKeyboardButton(text=texts.BTN_CONTACT_MASTER, url=contact_url)
    else:
        action = InlineKeyboardButton(
            text=f"{texts.BTN_PAY} · {format_price(price_tenge)}",
            callback_data=f"pay:{service_id}",
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [action],
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


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Женский", callback_data="survey:gender:f"),
                InlineKeyboardButton(text="Мужской", callback_data="survey:gender:m"),
            ]
        ]
    )


def skip_kb() -> InlineKeyboardMarkup:
    """Кнопка «Пропустить» для опциональных шагов (родители, девичья фамилия)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data="survey:skip")]]
    )
