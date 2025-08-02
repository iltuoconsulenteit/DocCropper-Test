#!/bin/bash
set -e

REPO_URL="https://github.com/iltuoconsulenteit/DocCropper"
DEV_KEY="${DOCROPPER_DEV_LICENSE:-ILTUOCONSULENTEIT-DEV}"
DEV_BRANCH="${DOCROPPER_BRANCH:-dgwo4q-codex/add-features-from-doccropper-project}"

DEFAULT_DIR="/opt/DocCropper"
read -r -p "Installation directory [$DEFAULT_DIR]: " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-$DEFAULT_DIR}
mkdir -p "$TARGET_DIR"
echo "Installing to: $TARGET_DIR"

DEFAULT_KEY=""
if [ -f "$TARGET_DIR/settings.json" ]; then
  DEFAULT_KEY=$(python3 - <<PY
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    print(d.get('license_key',''))
except Exception:
    pass
PY
 "$TARGET_DIR/settings.json")
fi
read -r -p "🔑 Enter license key (leave blank for demo) [${DEFAULT_KEY}]: " LIC_KEY
[ -z "$LIC_KEY" ] && LIC_KEY="$DEFAULT_KEY"
UPPER_KEY=$(echo "$LIC_KEY" | tr '[:lower:]' '[:upper:]')
DEV_UPPER=$(echo "$DEV_KEY" | tr '[:lower:]' '[:upper:]')
BRANCH="main"
if [ "$UPPER_KEY" = "$DEV_UPPER" ]; then
  BRANCH="$DEV_BRANCH"
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
    DEV_UP=$(echo "$DEV_KEY" | tr '[:lower:]' '[:upper:]')
    if [ "$UPPER_KEY" = "$DEV_UP" ]; then
      echo "🔀 Switching to developer branch $DEV_BRANCH"
      git -C "$TARGET_DIR" fetch origin "$DEV_BRANCH"
      git -C "$TARGET_DIR" checkout "$DEV_BRANCH"
      git -C "$TARGET_DIR" pull --rebase --autostash origin "$DEV_BRANCH"
    fi
  else
    echo "❌ License key invalid. Continuing in demo mode."
  fi
else
  echo "ℹ️  Demo mode enabled"
fi

read -r -p "🚀 Launch DocCropper with tray icon now? [Y/n] " RUN_APP
if [[ ! "$RUN_APP" =~ ^[Nn]$ ]]; then
  pushd "$TARGET_DIR" >/dev/null
  if command -v pythonw >/dev/null 2>&1; then
    (pythonw doccropper_tray.py &)
  else
    (python3 doccropper_tray.py &)
  fi
  popd >/dev/null
fi
