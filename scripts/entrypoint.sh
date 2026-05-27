#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PY'
import os, time
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL", "")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

if url.startswith("postgresql://"):
    for i in range(30):
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database ready")
            break
        except Exception as exc:
            print(f"DB not ready ({i+1}/30): {exc}")
            time.sleep(2)
    else:
        raise SystemExit("Database unavailable")
PY

echo "Initializing schema..."
python - <<'PY'
import sys
sys.path.insert(0, "/app")
from backend.app.database import init_db
init_db()
print("Schema ready")
PY

PORT="${PORT:-8000}"
HOST="${API_HOST:-0.0.0.0}"
echo "Starting server on ${HOST}:${PORT}"
exec uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
