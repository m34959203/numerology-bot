# syntax=docker/dockerfile:1
# Многостадийная сборка: зависимости и пакет ставятся в builder, рантайм — slim + шрифты.

FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
COPY pyproject.toml ./
COPY bot ./bot
COPY core ./core
# Устанавливаем проект (с deps и data-файлами трактовок) в изолированный префикс.
RUN pip install --prefix=/install .

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RUN_MODE=polling \
    REPORT_FORMAT=pdf
# Кириллические шрифты нужны для PDF-отчётов.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local

WORKDIR /app
# Для миграций нужны alembic.ini и каталог migrations (bot/core уже установлены как пакет).
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh \
    && useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
