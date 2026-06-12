"""Инлайн-клавиатуры бота."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.catalog_data import format_price
from core.i18n import LOCALE_FLAGS, LOCALE_NAMES, LOCALES, t


def _svc_title(service, locale: str) -> str:
    """Локализованный заголовок услуги по коду (fallback — title из БД)."""
    key = f"svc.{service.code}.title"
    txt = t(key, locale)
    return txt if txt != key else service.title


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


def daily_today_kb(locale: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура шага «дата прогноза»: быстрый выбор «Сегодня»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("ui.btn_today", locale), callback_data="daily:today")]
        ]
    )


def services_kb(services, locale: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{_svc_title(s, locale)} · {format_price(s.price_tenge)}",
                callback_data=f"svc:{s.id}",
            )
        ]
        for s in services
    ]
    rows.append([InlineKeyboardButton(text=t("ui.btn_back", locale), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_card_kb(service_id: int, price_tenge: int, locale: str = "ru") -> InlineKeyboardMarkup:
    """Карточка услуги — кнопка оплаты. Все тарифы оплачиваются в боте (звёздами);
    ручные (детские/совместимость) после оплаты готовит мастер вручную."""
    action = InlineKeyboardButton(
        text=f"{t('ui.btn_pay', locale)} · {format_price(price_tenge)}",
        callback_data=f"pay:{service_id}",
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [action],
            [InlineKeyboardButton(text=t("ui.btn_back", locale), callback_data="menu:services")],
        ]
    )


def confirm_kb(locale: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("ui.btn_confirm", locale), callback_data="survey:confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("ui.btn_restart", locale), callback_data="survey:restart"
                )
            ],
        ]
    )


def to_menu_kb(locale: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("ui.btn_to_menu", locale), callback_data="menu:main")]
        ]
    )


def gender_kb(locale: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("lbl.gender_female", locale), callback_data="survey:gender:f"
                ),
                InlineKeyboardButton(
                    text=t("lbl.gender_male", locale), callback_data="survey:gender:m"
                ),
            ]
        ]
    )


def skip_kb(locale: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка «Пропустить» для опциональных шагов (родители, девичья фамилия)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("ui.btn_skip", locale), callback_data="survey:skip")]
        ]
    )
