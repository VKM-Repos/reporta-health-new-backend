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

exec "$@"