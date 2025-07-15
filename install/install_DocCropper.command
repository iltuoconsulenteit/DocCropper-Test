#!/bin/bash
set -e

REPO_URL="https://github.com/iltuoconsulenteit/DocCropper"
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
    git -C "$TARGET_DIR" pull --rebase --autostash
  fi
else
  echo "📥 Clonazione repository in $TARGET_DIR..."
  git clone "$REPO_URL" "$TARGET_DIR"
fi

printf '\xE2\x9C\x85 Operazione completata.\n'
