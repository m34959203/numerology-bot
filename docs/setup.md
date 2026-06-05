# Установка и запуск

## Требования

- Python 3.12+
- PostgreSQL 14+
- Бот-токен от [@BotFather](https://t.me/BotFather)

## Локально

```bash
git clone https://github.com/m34959203/numerology-bot.git
cd numerology-bot

cp .env.example .env
# заполнить как минимум BOT_TOKEN и DATABASE_URL

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"          # +".[pdf]" если нужен PDF, +".[excel]" для выгрузки текстов

# БД
createdb numerology               # или вручную в psql
alembic upgrade head

# Запуск (polling)
python -m bot.main
```

## Переменные окружения

См. `.env.example`. Ключевые:

| Переменная | Назначение |
|-----------|-----------|
| `BOT_TOKEN` | токен бота |
| `ADMIN_IDS` | id админов через запятую (возвраты, услуги) |
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `REPORT_FORMAT` | `text` / `pdf` / `both` |
| `RUN_MODE` | `polling` / `webhook` |

## Выгрузка текстов-трактовок из Excel

```bash
pip install -e ".[excel]"
python scripts/extract_texts.py --src "$EXCEL_SOURCE_PATH" --out core/content/data
```

## Деплой (VPS)

Для Telegram Stars статический IP/VPN не нужен. Минимально — systemd-юнит на `python -m bot.main` в режиме polling. Подробности — после Этапа 6.

## Troubleshooting

| Симптом | Действие |
|---------|----------|
| Бот не отвечает | проверить `BOT_TOKEN`, что процесс жив, нет второго polling |
| Ошибка БД при старте | проверить `DATABASE_URL`, что `alembic upgrade head` прошёл |
| Платёж прошёл, отчёта нет | проверить лог `successful_payment` и уникальность `telegram_payment_charge_id` |
| Расхождение с Excel | это баг — добавить контрольный пример в `tests/fixtures`, не «подгонять» |
