#!/bin/sh
set -e

# ─── Wait for PostgreSQL to be available ─────────────────────────────────────
echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until python -c "
import socket, sys
try:
    s = socket.create_connection(('${DB_HOST}', int('${DB_PORT}')), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  → PostgreSQL not ready yet, retrying in 2s..."
  sleep 2
done
echo "PostgreSQL is available!"

# ─── Apply database migrations ───────────────────────────────────────────────
echo "Running migrations..."
python manage.py migrate --noinput

# ─── Collect static files (production) ───────────────────────────────────────
if [ "$DJANGO_ENV" = "production" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# ─── Start Uvicorn ───────────────────────────────────────────────────────────
echo "Starting Uvicorn..."
exec uvicorn core.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers ${UVICORN_WORKERS:-2} \
  --log-level ${UVICORN_LOG_LEVEL:-info}
