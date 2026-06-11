"""Клиент Crypto Pay API (@CryptoBot / @CryptoTestnetBot) — приём оплаты в TON.

Docs: https://help.crypt.bot/crypto-pay-api
Токен приложения — из settings.crypto_pay_token (.env). Сеть выбирается флагом
settings.crypto_pay_testnet (testnet-pay.crypt.bot vs pay.crypt.bot).

Поток в боте: create_invoice (fiat=KZT, asset=TON, автоконвертация по курсу
Crypto Pay) → пользователю кнопка-ссылка на оплату → опрос get_invoices до
статуса "paid" → выдача (как при Stars). Вебхук не нужен — работаем поллингом.
"""

from __future__ import annotations

from typing import Any

import aiohttp

from bot.config import settings


class CryptoPayError(RuntimeError):
    """Ошибка Crypto Pay API (ok=false или сетевой сбой)."""


def _base_url() -> str:
    return (
        "https://testnet-pay.crypt.bot" if settings.crypto_pay_testnet else "https://pay.crypt.bot"
    )


# Crypto Pay за Cloudflare блокирует дефолтные UA Python/urllib/aiohttp (error
# 1010 → HTTP 403). Обязателен браузероподобный User-Agent.
_UA = "Mozilla/5.0 (compatible; NumerologyBot/1.0)"


async def _call(method: str, params: dict[str, Any] | None = None) -> Any:
    """Вызвать метод Crypto Pay API. Возвращает result или бросает CryptoPayError."""
    token = settings.crypto_pay_token.strip()
    if not token:
        raise CryptoPayError("CRYPTO_PAY_TOKEN не задан")
    url = f"{_base_url()}/api/{method}"
    headers = {"Crypto-Pay-API-Token": token, "User-Agent": _UA}
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=params or {}, headers=headers) as resp:
            data = await resp.json()
    if not data.get("ok"):
        raise CryptoPayError(f"{method}: {data.get('error', data)}")
    return data.get("result")


async def get_me() -> dict:
    """Информация о приложении (для диагностики токена)."""
    return await _call("getMe")


async def create_invoice(
    amount: str,
    payload: str,
    description: str,
    *,
    currency_type: str = "fiat",
    fiat: str | None = None,
    asset: str | None = None,
    accepted_assets: str | None = None,
    expires_in: int = 1800,
) -> dict:
    """Создать счёт. По умолчанию fiat-счёт (цена в KZT) с приёмом в TON —
    Crypto Pay сам конвертирует по курсу на момент оплаты.

    Возвращает invoice (invoice_id, status, bot_invoice_url/pay_url, amount, …).
    """
    params: dict[str, Any] = {
        "currency_type": currency_type,
        "amount": str(amount),
        "payload": payload,
        "description": description,
        "expires_in": expires_in,
        "allow_comments": False,
    }
    if currency_type == "fiat":
        params["fiat"] = fiat or settings.crypto_pay_fiat
        params["accepted_assets"] = accepted_assets or settings.crypto_pay_asset
    else:
        params["asset"] = asset or settings.crypto_pay_asset
    return await _call("createInvoice", params)


async def get_invoice(invoice_id: int | str) -> dict | None:
    """Один счёт по id (статус оплаты). None — если не найден."""
    result = await _call("getInvoices", {"invoice_ids": str(invoice_id)})
    items = result.get("items", []) if isinstance(result, dict) else result
    return items[0] if items else None


def invoice_pay_url(invoice: dict) -> str:
    """Ссылка на оплату из ответа createInvoice (учёт разных версий API)."""
    return (
        invoice.get("bot_invoice_url")
        or invoice.get("mini_app_invoice_url")
        or invoice.get("web_app_invoice_url")
        or invoice.get("pay_url")
        or ""
    )
