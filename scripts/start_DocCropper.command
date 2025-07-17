#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
cd "$APP_DIR"

PORT=$(python3 - <<'PY'
import json
try:
    with open('settings.json') as f:
        d=json.load(f)
    print(d.get('port',8000))
except Exception:
    print(8000)
PY
)

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

echo "Starting DocCropper on port $PORT..."
python3 main.py --host 0.0.0.0 --port "$PORT"
