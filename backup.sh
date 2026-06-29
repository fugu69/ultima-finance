#!/bin/bash

# Автоматически определяем папку, где лежит этот скрипт (корень проекта)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Жестко создаем папку для бэкапов, если её ещё нет
mkdir -p backups

# Проверяем, запущен ли контейнер базы данных прямо сейчас
CONTAINER_ID=$(docker ps -q -f "name=ultima_db")

if [ -z "$CONTAINER_ID" ]; then
    echo "=== [БЭКАП ОТМЕНЕН] Контейнер ultima_db не запущен. ==="
    exit 1
fi

# Если контейнер работает — подтягиваем .env и делаем дамп
export $(grep -v '^#' .env | xargs)
FILENAME="ultima_finance_$(date +%Y%m%d_%H%M%S).dump"

/usr/bin/docker compose exec -T ultima_db pg_dump -U $POSTGRES_USER -F c -b -f /app/backups/$FILENAME $POSTGRES_DB
