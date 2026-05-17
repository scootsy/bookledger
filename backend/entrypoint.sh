#!/bin/sh
set -e
cd /app/backend
alembic upgrade head
exec uvicorn bookledger.main:app --host 0.0.0.0 --port 8787
