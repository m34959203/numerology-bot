# Деплой в прод

Бот работает в режиме **polling** — входящие порты и публичный домен не нужны
(для Telegram Stars тоже). Нужны только исходящий доступ в интернет и PostgreSQL.

## Вариант A. Docker Compose (рекомендуется)

Поднимает PostgreSQL и бота, прогоняет миграции и стартует polling.

### 1. Подготовка сервера
- Установлен Docker + Docker Compose v2.
- Открыт исходящий HTTPS (api.telegram.org).

### 2. Конфигурация
```bash
git clone https://github.com/m34959203/numerology-bot.git
cd numerology-bot
cp .env.example .env
```
Заполнить в `.env` как минимум:
- `BOT_TOKEN` — токен от @BotFather;
- `ADMIN_IDS` — ваш Telegram ID (через запятую) для `/admin` и `/refund`;
- `POSTGRES_PASSWORD` — пароль БД (тот же попадёт в `DATABASE_URL` контейнера);
- `REPORT_FORMAT` — `pdf` / `text` / `both` (по умолчанию `pdf`).

`DATABASE_URL` для контейнера бота собирается автоматически из `POSTGRES_*`
(host = `db`). Локальный `DATABASE_URL` из `.env` для compose не используется.

### 3. Запуск
```bash
docker compose up -d --build
docker compose logs -f bot
```
При старте контейнер бота выполняет `alembic upgrade head` (создаёт схему) и
засевает каталог услуг, затем запускает polling.

### 4. Обновление
```bash
git pull
docker compose up -d --build
```
Новые миграции применятся автоматически при старте.

### 5. Эксплуатация
```bash
docker compose ps                    # статус
docker compose logs -f bot           # логи бота
docker compose exec db pg_dump -U numerology numerology > backup.sql   # бэкап
docker compose down                  # остановить (данные в volume сохраняются)
```

## Вариант B. Только образ бота + внешний PostgreSQL

```bash
docker build -t numerology-bot .
docker run -d --name numerology-bot --restart unless-stopped \
  -e BOT_TOKEN=... \
  -e ADMIN_IDS=123456789 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db-host:5432/numerology" \
  -e REPORT_FORMAT=pdf \
  numerology-bot
```
Контейнер сам прогонит `alembic upgrade head` перед запуском.

## Миграции БД (Alembic)
- Схема версионируется в `migrations/versions/`. Прод применяет их через entrypoint.
- Создать новую миграцию после изменения моделей (`core/models.py`):
  ```bash
  alembic revision --autogenerate -m "описание"
  alembic upgrade head
  ```
- Alembic ходит в БД синхронно через `psycopg` (asyncpg-URL конвертируется в `+psycopg`
  в `migrations/env.py`); рантайм бота — через `asyncpg`.

## Шрифты для PDF
Образ ставит `fonts-dejavu-core` (кириллица в PDF). Если используете свой базовый
образ без шрифтов — установите пакет или смонтируйте TTF и задайте `PDF_FONT_PATH`.

## Возвраты и админка
- `/admin` — статистика (пользователи, заказы, доход, возвраты).
- `/refund <telegram_payment_charge_id>` — возврат звёзд (доступно только `ADMIN_IDS`).

## Чек-лист перед продом
- [ ] `.env` заполнен, секреты НЕ в git (`.env` в `.gitignore`).
- [ ] `BOT_TOKEN` рабочий, бот отвечает на `/start`.
- [ ] Прошёл тестовый платёж Stars → пришёл расчёт (PDF).
- [ ] Возврат `/refund` отрабатывает.
- [ ] Услуги/цены в каталоге согласованы с заказчиком (по умолчанию 1 услуга, 100⭐).
- [ ] Настроен бэкап PostgreSQL (cron `pg_dump`).
