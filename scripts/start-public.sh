#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -r requirements.txt -q
[ -f .env ] || cp .env.example .env

export API_HOST=0.0.0.0
export PORT=8080
export CORS_ORIGINS="*"

echo "Starting on http://0.0.0.0:8080"
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
