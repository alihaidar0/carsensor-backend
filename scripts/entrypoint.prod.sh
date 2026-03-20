#!/usr/bin/env bash
set -euo pipefail

echo "Starting Django production server..."

# Wait for database
python << 'PYCHECK'
import os, sys, time, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()
from django.db import connection
for i in range(10):
    try:
        connection.ensure_connection()
        print("✅ Database connected")
        break
    except Exception as e:
        if i == 9:
            print(f"❌ Database failed: {e}")
            sys.exit(1)
        print(f"Retry {i+1}/10...")
        time.sleep(2)
PYCHECK

python manage.py migrate --noinput
echo "✅ Migrations complete"

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8080}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --worker-class "uvicorn.workers.UvicornWorker" \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --access-logfile - \
  --error-logfile - \
  --log-level info
