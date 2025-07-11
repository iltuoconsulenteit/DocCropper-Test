#!/bin/bash
set -e

REPO_URL="https://github.com/iltuoconsulenteit/DocCropper"
TARGET_DIR="$HOME/Scrivania/DocCropper"

merge_settings() {
  local repo_settings="$TARGET_DIR/settings.json.repo"
  git -C "$TARGET_DIR" show HEAD:settings.json > "$repo_settings" || return 0
  python3 - "$TARGET_DIR" "$repo_settings" <<'EOF'
import json, sys, os
target=sys.argv[1]+"/settings.json"
repo=sys.argv[2]
try:
    with open(target) as f: local=json.load(f)
except FileNotFoundError:
    local={}
with open(repo) as f: base=json.load(f)
changed=False
for k,v in base.items():
    if k not in local:
        local[k]=v
        changed=True
if changed:
    with open(target,'w') as f:
        json.dump(local,f,indent=2)
os.remove(repo)
EOF
}

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
    git -C "$TARGET_DIR" pull --rebase --autostash
    merge_settings
  fi
else
  echo "📥 Clonazione repository..."
  git clone "$REPO_URL" "$TARGET_DIR"
  merge_settings
fi

printf '\xE2\x9C\x85 Operazione completata.\n'
