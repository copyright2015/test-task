#!/usr/bin/env bash
set -euo pipefail

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || { echo "Python 3.10 or newer is required."; exit 1; }
node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 18 ? 0 : 1)' || { echo "Node.js 18 or newer is required."; exit 1; }

if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm install)
mkdir -p database
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head

.venv/bin/uvicorn app.main:app --app-dir backend --reload &
API_PID=$!
(cd frontend && npm run dev) &
UI_PID=$!
trap 'kill "$API_PID" "$UI_PID" 2>/dev/null || true' INT TERM EXIT
wait
