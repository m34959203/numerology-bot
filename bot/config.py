"""Настройки из окружения (.env) через pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфиг приложения. Значения берутся из .env / переменных окружения."""

    bot_token: str = "123456:CHANGE_ME"
    admin_ids: str = ""
    # Чат(ы) мастера для заявок на ручные тарифы (детские/совместимость).
    # Запятая-разделитель. Пусто → заявки уходят в ADMIN_IDS. Мастер должен
    # один раз нажать Start у бота, иначе Telegram не даст боту ему написать.
    master_chat_id: str = ""
    database_url: str = "postgresql+asyncpg://numerology:CHANGE_ME@localhost:5432/numerology"

    excel_source_path: str = "./ПРОГРАММА_МАТРИЦА_на_русском.xlsx"
    report_format: str = "pdf"  # text | pdf | both
    # Путь к TTF-шрифту с кириллицей для PDF. Пусто → поиск по системным путям.
    pdf_font_path: str = ""

    # Имитация оплаты для тестирования функционала: оплата через Telegram Stars
    # отключена, бот сразу выдаёт услугу как будто платёж прошёл. Вернуть к боевой
    # оплате — выставить PAYMENT_IMITATION=false в .env.
    payment_imitation: bool = True

    # Приём оплаты в TON через Crypto Pay (@CryptoBot / @CryptoTestnetBot).
    # Токен приложения — в .env (CRYPTO_PAY_TOKEN); пусто → TON-оплата скрыта.
    # CRYPTO_PAY_TESTNET=true — тестовая сеть (testnet-pay.crypt.bot).
    crypto_pay_token: str = ""
    crypto_pay_testnet: bool = True
    crypto_pay_asset: str = "TON"  # криптовалюта приёма (TON по умолчанию)
    crypto_pay_fiat: str = "KZT"  # валюта цены для автоконвертации (тенге)

    run_mode: str = "polling"  # polling | webhook
    webhook_base_url: str = ""
    webhook_path: str = "/webhook"

    log_level: str = "INFO"
    # Каталог для персистентных логов с ротацией (RotatingFileHandler).
    # Пусто → только stdout. В docker задаётся LOG_DIR=/app/logs (volume botlogs).
    log_dir: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def master_chat_id_list(self) -> list[int]:
        """Куда слать заявки на ручные разборы. Пустой MASTER_CHAT_ID → fallback на админов."""
        ids = [int(x) for x in self.master_chat_id.split(",") if x.strip()]
        return ids or self.admin_id_list

    @property
    def crypto_pay_enabled(self) -> bool:
        """TON-оплата доступна, если задан токен Crypto Pay."""
        return bool(self.crypto_pay_token.strip())


settings = Settings()
