#!/bin/sh
# Применяем миграции БД, затем запускаем бота. Падаем при ошибке миграции.
set -e

echo "[entrypoint] alembic upgrade head ..."
alembic upgrade head

echo "[entrypoint] запуск бота (RUN_MODE=${RUN_MODE:-polling}) ..."
exec python -m bot.main
