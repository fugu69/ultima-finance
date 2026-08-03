#!/bin/sh

# Выходим сразу при любой ошибке
set -e

echo "Собираем статичные файлы..."
python manage.py collectstatic --noinput

echo "Запускаем миграции базы данных..."
python manage.py migrate --noinput

echo "Запуск Gunicorn..."
exec "$@"