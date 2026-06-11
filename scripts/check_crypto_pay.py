"""Диагностика платёжного токена: что это и в какой сети.

Читает токен из переменной окружения (по умолчанию CRYPTO_PAY_TOKEN) и пробует
Crypto Pay `getMe` на mainnet и testnet. Печатает, валиден ли токен, имя
приложения и сеть — чтобы определить «что за токен», не зная его заранее.

Запуск:  CRYPTO_PAY_TOKEN=<токен> python scripts/check_crypto_pay.py
(или положите токен в .env как CRYPTO_PAY_TOKEN и запустите через окружение).
Значение токена в вывод НЕ попадает.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def _load_dotenv() -> None:
    """Подхватить переменные из .env проекта (без внешних зависимостей)."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip("'\""))


ENDPOINTS = {
    "mainnet": "https://pay.crypt.bot/api/getMe",
    "testnet": "https://testnet-pay.crypt.bot/api/getMe",
}


def _probe(url: str, token: str) -> tuple[bool, dict | str]:
    # Браузероподобный UA обязателен: Cloudflare режет дефолтный Python-UA (1010).
    headers = {
        "Crypto-Pay-API-Token": token,
        "User-Agent": "Mozilla/5.0 (compatible; NumerologyBot/1.0)",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
        return bool(body.get("ok")), body.get("result", body)
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"http_status": e.code}
        return False, body
    except Exception as e:  # сеть/таймаут
        return False, f"{type(e).__name__}: {e}"


def main() -> None:
    _load_dotenv()
    var = os.environ.get("CRYPTO_PAY_TOKEN_VAR", "CRYPTO_PAY_TOKEN")
    token = os.environ.get(var, "").strip()
    if not token:
        print(f"❌ Переменная {var} пуста. Положите токен в .env как {var}=... и запустите снова.")
        print("   (значение токена не печатается)")
        return

    # Лёгкий «отпечаток» токена без раскрытия: формат и длина.
    looks_like_pay = ":" in token and token.split(":", 1)[0].isdigit()
    print(f"Токен из {var}: длина {len(token)}, формат «id:hash» = {looks_like_pay}")
    print("Проверяю Crypto Pay (@CryptoBot)…\n")

    found = False
    for net, url in ENDPOINTS.items():
        ok, result = _probe(url, token)
        if ok:
            found = True
            name = result.get("name") or result.get("app_id") or "?"
            bot_name = result.get("payment_processing_bot_username")
            print(f"✅ {net.upper()}: это токен Crypto Pay. Приложение: {name}")
            print(f"   app_id={result.get('app_id')} payment_processing_bot={bot_name}")
        else:
            print(f"—  {net}: не Crypto Pay / неверный токен. Ответ: {result}")

    print()
    if found:
        print("ИТОГ: токен Crypto Pay — путь подтверждён. Сеть, где он валиден, — выше.")
    else:
        print("ИТОГ: это НЕ токен Crypto Pay (или он недействителен).")
        print("Возможные варианты: xRocket Pay, Wallet Pay (@wallet), TON Connect/кошелёк.")
        print("Скажите, в каком боте/сайте заказчик создавал токен — подберу путь.")


if __name__ == "__main__":
    main()
