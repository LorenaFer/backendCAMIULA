#!/bin/bash
# Railway startup script — runs migrations then starts uvicorn.
# Migrations run first so the schema is ready before any request hits.
# If alembic fails, the deploy fails fast (which is what we want).

set -e

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 2 \
    --log-level info
