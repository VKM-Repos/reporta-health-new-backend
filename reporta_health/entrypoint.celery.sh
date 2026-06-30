#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import os, time, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.db import connections
from django.db.utils import OperationalError
for i in range(60):
    try:
        connections['default'].ensure_connection()
        print('Database is ready')
        break
    except OperationalError:
        print(f'Attempt {i+1}/60 — waiting...')
        time.sleep(1)
else:
    print('Database unavailable after 60s — exiting')
    exit(1)
"

echo "Starting Celery..."
exec "$@"