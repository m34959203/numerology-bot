#!/usr/bin/env bash
# Бэкап Postgres из docker-compose: pg_dump → gzip в ./backups, ретеншен 14 копий.
# Использует переменные окружения контейнера db (POSTGRES_USER/DB) — .env на хосте не нужен.
#
# Разовый запуск:   ./scripts/backup_db.sh
# По расписанию (crontab -e), ежедневно в 03:30:
#   30 3 * * * cd /path/to/numerology_bot && ./scripts/backup_db.sh >> backups/backup.log 2>&1
#
# Восстановление:
#   gunzip -c backups/numerology_YYYYmmdd_HHMMSS.sql.gz | \
#     docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p backups

ts=$(date +%Y%m%d_%H%M%S)
out="backups/numerology_${ts}.sql.gz"

docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip >"$out"

# Ретеншен: оставить 14 свежих дампов, остальные удалить.
ls -1t backups/numerology_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm --

echo "[backup] $(date '+%F %T') → $out ($(du -h "$out" | cut -f1))"
