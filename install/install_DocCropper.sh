#!/bin/bash
set -e

REPO_URL="https://github.com/iltuoconsulenteit/DocCropper"
BRANCH="main"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
# If the script sits inside the repo's install/ folder we update the parent
# otherwise we clone into a DocCropper subfolder next to the script
if [ -d "$SCRIPT_DIR/.git" ]; then
  TARGET_DIR="$SCRIPT_DIR"
elif [ -d "$PARENT_DIR/.git" ]; then
  TARGET_DIR="$PARENT_DIR"
else
  TARGET_DIR="$SCRIPT_DIR/DocCropper"
fi

printf '\xF0\x9F\x94\xA7 Verifica pacchetti richiesti...\n'
for cmd in git python3 pip3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ $cmd non trovato" >&2
    exit 1
  fi
done

if [ -d "$TARGET_DIR/.git" ]; then
  echo "📁 Repository già presente in $TARGET_DIR"
  read -r -p "🔄 Vuoi aggiornare il repository da GitHub? [s/N] " ans
  if [[ "$ans" =~ ^[sS]$ ]]; then
    echo "📥 Aggiornamento repository..."
    git -C "$TARGET_DIR" pull --rebase --autostash origin "$BRANCH"
  fi
else
  echo "📥 Clonazione repository in $TARGET_DIR..."
  git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
fi

printf '\xE2\x9C\x85 Operazione completata.\n'

# Ask for license key and name
SETTINGS_FILE="$TARGET_DIR/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
  cat > "$SETTINGS_FILE" <<'EOF'
{
  "language": "en",
  "layout": 1,
  "orientation": "portrait",
  "arrangement": "auto",
  "scale_mode": "fit",
  "scale_percent": 100,
  "port": 8000,
  "license_key": "",
  "license_name": ""
}
EOF
fi

read -r -p "🔑 Enter license key (leave blank for demo): " LIC_KEY
if [ -n "$LIC_KEY" ]; then
  UPPER_KEY="$(echo "$LIC_KEY" | tr '[:lower:]' '[:upper:]')"
  DEV_KEY="${DOCROPPER_DEV_LICENSE:-ILTUOCONSULENTEIT-DEV}"
  DEV_KEY_UPPER="$(echo "$DEV_KEY" | tr '[:lower:]' '[:upper:]')"
  if [ "$UPPER_KEY" = "VALID" ] || [ "$UPPER_KEY" = "$DEV_KEY_UPPER" ]; then
    read -r -p "👤 Licensed to: " LIC_NAME
    python3 - "$SETTINGS_FILE" "$LIC_KEY" "$LIC_NAME" <<'PY'
import json, sys
f, key, name = sys.argv[1:]
with open(f) as fh:
    data = json.load(fh)
data['license_key'] = key
data['license_name'] = name
with open(f, 'w') as fh:
    json.dump(data, fh)
PY
    echo "✅ License saved"
  else
    echo "❌ License key invalid. Continuing in demo mode."
  fi
else
  echo "ℹ️  Demo mode enabled"
fi

read -r -p "🚀 Launch DocCropper now? [Y/n] " RUN_APP
if [[ ! "$RUN_APP" =~ ^[Nn]$ ]]; then
  "$SCRIPT_DIR/start_DocCropper.sh"
fi
