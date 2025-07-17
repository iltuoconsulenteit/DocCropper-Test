#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
cd "$APP_DIR"
python3 main.py --stop
