"""Настройки из окружения (.env) через pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфиг приложения. Значения берутся из .env / переменных окружения."""

    bot_token: str = "123456:CHANGE_ME"
    admin_ids: str = ""
    database_url: str = "postgresql+asyncpg://numerology:CHANGE_ME@localhost:5432/numerology"

    excel_source_path: str = "./ПРОГРАММА_МАТРИЦА_на_русском.xlsx"
    report_format: str = "pdf"  # text | pdf | both
    # Путь к TTF-шрифту с кириллицей для PDF. Пусто → поиск по системным путям.
    pdf_font_path: str = ""

    run_mode: str = "polling"  # polling | webhook
    webhook_base_url: str = ""
    webhook_path: str = "/webhook"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x) for x in self.admin_ids.split(",") if x.strip()]


settings = Settings()
