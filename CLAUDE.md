# Нумерологическая матрица — Developer Guide (для Claude Code)

> Этот файл читается Claude Code при работе в репозитории. Контекст, стек, конвенции, правила.

## Project Overview

Telegram-бот, продающий персональный нумерологический разбор. Путь пользователя: меню → услуга → оплата Telegram Stars → FSM-анкета → отчёт. Вся расчётная логика — перенос Excel-программы `ПРОГРАММА_МАТРИЦА_на_русском.xlsx` (50 листов, ~6 000 формул).

**Главное правило проекта: Excel — источник истины.** Бот обязан выдавать ровно то же, что Excel. Любое расхождение на контрольных примерах = баг, а не «допустимое отклонение».

## Tech Stack

- Python 3.12+ · aiogram 3.x (polling/webhook)
- PostgreSQL · SQLAlchemy 2 (asyncpg) · Alembic
- Расчёты: чистый Python + `python-dateutil` (без pandas/numpy — только stdlib-математика)
- Конфиг: pydantic-settings из `.env`
- Тесты: pytest (+ pytest-asyncio); линт: ruff + black
- PDF (опц.): reportlab

## Running Locally

```bash
cp .env.example .env            # заполнить BOT_TOKEN, DATABASE_URL
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m bot.main
```

## Архитектура и конвенции

### Слои
- `bot/` — только Telegram (хендлеры, FSM, клавиатуры, оплата). Никакой нумерологии.
- `core/numerology/` — чистые функции расчёта. Вход: данные анкеты, выход: структурированный dict/dataclass. Без побочных эффектов, без обращений к Telegram/БД.
- `core/content/` — тексты-трактовки (выгрузка из листов `текст`, `1`–`36`). Сопоставление «число/комбинация → текст».
- `core/models.py` — ORM (SQLAlchemy).

### Соответствие модулей листам Excel
| Модуль | Лист Excel | Этап |
|--------|-----------|------|
| `psychomatrix.py` | `calc` (квадрат Пифагора) | 2 |
| `biorhythm.py` | `Bio` (репликация → одна функция) | 2 |
| `codes.py` | `РАСЧЕТ`, `Calculation`, `Lists` | 3 |
| `matrix.py` | `Matr` (ядро, 4715 формул) | 4 |
| `moon_sun.py` | `луна и солнце` (+ Calculation/Lists) + `ЧПМ` | 5 |
| `report.py` | `РАСЧЕТ` (сборка отчёта) | — |

### Перенос формул Excel → Python
Excel-функции реализуются как хелперы (см. `core/numerology/_excel.py` при появлении): IF→тернарник, IFERROR→try/except, ROUND/ROUNDDOWN, MID/LEFT/RIGHT/LEN, MATCH/INDEX/VLOOKUP→словари, INDIRECT→диспетч по имени, DATE/EDATE/YEAR/MONTH/DAY→`datetime`+`dateutil.relativedelta`, ISODD, COUNTIFS, ABS.

### Платежи
- Telegram Stars: `currency="XTR"`, `LabeledPrice`. `pre_checkout_query` → `ok=True`. `successful_payment` → запись + выдача.
- **Идемпотентность:** хранить `telegram_payment_charge_id`; один платёж = одна выдача.
- Возврат: `refund_star_payment` по команде админа.
- Провайдер абстрагирован за интерфейсом `PaymentProvider` (на будущее Kaspi/посредник).

## Testing

- TDD по расчётам: тест с эталоном из Excel → реализация. Фикстуры в `tests/fixtures/`.
- Граничные кейсы обязательны: 29 февраля, начало/конец века, сведение двузначных, пустые опциональные поля.
- Перед PR: `ruff check . && black --check . && pytest`.

## Git

- Conventional Commits, английский префикс + русское описание, инфинитив, ≤72 символа.
- Ветки: `feat/xxx`, `fix/xxx`. PR в `main`.
- **Не коммитить:** `.env`, `*.xlsx` (источник отдаётся заказчиком), любые ключи.

## Security

- Секреты только в `.env` (в репо `.env.example`).
- Персональные данные анкеты — минимально необходимый объём.
- Идемпотентность платежей + защита от двойной выдачи.
- Логировать: оплата, расчёт, ошибки, возвраты.
- FSM не должен «зависать» при исключении — ловить и предлагать «Начать заново».

## Открытые вопросы

Всё неоднозначное — в `OPEN_QUESTIONS.md`. Не угадывать формулы и обязательность полей.
