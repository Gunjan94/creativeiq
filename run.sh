#!/usr/bin/env bash
# run.sh — one-shot local bring-up for CreativeIQ (offline, zero AWS credentials).
# Generates data + assets, starts the backend (port 8000) and the Vite dev server (port 5173).
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3.12}"
command -v "$PYTHON" >/dev/null || PYTHON=python3

echo "==> 1/4  Generating synthetic data + offline hero assets"
"$PYTHON" scripts/seed_data.py
"$PYTHON" scripts/gen_assets.py

echo "==> 2/4  Backend venv + deps"
cd backend
[ -d .venv ] || "$PYTHON" -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
echo "==> 3/4  Starting backend on http://localhost:8000"
./.venv/bin/python -m uvicorn app:app --port 8000 &
BACKEND_PID=$!
cd ..

echo "==> 4/4  Frontend deps + dev server on http://localhost:5173"
cd frontend
npm install --registry=https://registry.npmjs.org/ >/dev/null 2>&1 || npm install
npm run dev &
FRONTEND_PID=$!
cd ..

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT INT TERM
echo
echo "CreativeIQ is up:  http://localhost:5173   (backend: http://localhost:8000/health)"
echo "Ctrl-C to stop."
wait
