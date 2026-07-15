#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r backend/requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

docker compose up -d postgres redis

echo "Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U postgres -d public_safety >/dev/null 2>&1; do
  sleep 1
done

echo "Waiting for Redis..."
until docker compose exec redis redis-cli ping | grep -q PONG; do
  sleep 1
done

PYTHONPATH="$ROOT_DIR" python scripts/setup/init_db.py

echo "Backend ready. Run (in separate terminals):"
echo "  source .venv/bin/activate"
echo "  PYTHONPATH=$ROOT_DIR uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo "  ./scripts/setup/run_worker.sh"
echo "  cd frontend && npm install && npm run dev"
