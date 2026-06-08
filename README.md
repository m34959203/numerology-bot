# Нумерологическая матрица — Telegram-бот

[![CI](https://img.shields.io/github/actions/workflow/status/m34959203/numerology-bot/ci.yml?branch=main)](https://github.com/m34959203/numerology-bot/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Stack](https://img.shields.io/badge/stack-Python%203.12%20·%20aiogram%203%20·%20PostgreSQL-black)]()

> Telegram-бот: расчёт персональной нумерологической матрицы и прогноза с оплатой через Telegram Stars. Логика повторяет Excel-программу «МАТРИЦА».

## Проблема

Нумерологический разбор сегодня живёт в гигантском Excel-файле (50 листов, ~6 000 формул). Им нельзя пользоваться массово, продавать и автоматизировать: нет оплаты, анкеты, выдачи отчётов, истории клиентов.

## Решение

Перенос логики Excel в продакшн-бота: пользователь выбирает услугу → платит Telegram Stars → заполняет анкету → получает персональный расчёт. **Источник истины расчётов — `ПРОГРАММА_МАТРИЦА_на_русском.xlsx`**; бот обязан выдавать ровно то же, что Excel (нулевая толерантность к расхождениям на контрольных примерах).

## Why Python + aiogram

- **aiogram 3.x** — нативная поддержка Telegram Stars (`currency="XTR"`), pre-checkout, refund, FSM-анкеты из коробки.
- **Чистый Python** для расчётов — формулы Excel (IF/INDEX/MATCH/EDATE/ROUND…) 1:1 ложатся на стандартную библиотеку + `python-dateutil`, легко покрываются `pytest`.
- **PostgreSQL + SQLAlchemy 2 + Alembic** — идемпотентность платежей и история «Мои расчёты» без самописного хранилища.

## Demo

- **Live:** _TBD_
- **Видео:** _TBD_

## Архитектура

```
Telegram ──► bot/ (aiogram: меню, каталог, FSM-анкета, оплата Stars)
                   │
                   ▼
            core/numerology/ (расчёт = перенос листов Excel)
                   │  ◄── core/content/ (тексты-трактовки из листов «текст», 1–36)
                   ▼
            core/report.py (сборка отчёта) ──► PostgreSQL (orders/payments/results)
```

Подробнее: [docs/architecture.md](docs/architecture.md).

## Quick Start

```bash
git clone https://github.com/m34959203/numerology-bot.git
cd numerology-bot
cp .env.example .env          # заполнить BOT_TOKEN и DATABASE_URL
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m bot.main
```

Подробная инструкция и troubleshooting: [docs/setup.md](docs/setup.md).

## Стек

- **Бот:** Python 3.12+ · aiogram 3.x
- **БД:** PostgreSQL · SQLAlchemy 2 (asyncpg) · Alembic
- **Расчёты:** чистый Python + `python-dateutil`
- **PDF (опц.):** reportlab / weasyprint
- **Конфиг:** pydantic-settings (`.env`)
- **Тесты/линт:** pytest · ruff · black
- **Хостинг:** VPS (для Telegram Stars статический IP/VPN не нужен)

## Статус

**Готово: расчётный слой перенесён на 100%, все 5 пунктов ТЗ закрыты.**
Сверка по ТЗ — [docs/TZ_CHECKLIST.md](docs/TZ_CHECKLIST.md).

## Этапы (roadmap)

- [x] **Этап 1** — каркас + оплата Stars + FSM-анкета + БД + заглушка выдачи
- [x] **Этап 2** — психоматрица (`calc`) + биоритмы (`Bio`) + тесты сверки
- [x] **Этап 3** — коды и базовые вычисления (`РАСЧЕТ`, `Calculation`, `Lists`)
- [x] **Этап 4** — ядро матрицы (`Matr`) + число/карма имени + кармические события
- [x] **Этап 5** — Луна и Солнце + ЧПМ
- [x] **Этап 6** — PDF, админка, деплой, приёмка

Подробно: [docs/roadmap.md](docs/roadmap.md). Открытые вопросы к заказчику: [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Лицензия

[MIT](LICENSE)
