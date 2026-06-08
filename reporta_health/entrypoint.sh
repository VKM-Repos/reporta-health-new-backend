#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
for i in $(seq 1 60); do
    if nc -z "$DB_HOST" "$DB_PORT"; then
        echo "PostgreSQL is up"
        break
    fi
    echo "Attempt $i/60 — waiting..."
    sleep 1
done
nc -z "$DB_HOST" "$DB_PORT" || { echo "PostgreSQL unavailable after 60s — exiting"; exit 1; }

echo "Running Django checks..."
python manage.py check --deploy

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -