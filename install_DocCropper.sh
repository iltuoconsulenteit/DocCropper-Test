#!/bin/bash
set -e

REPO_URL="https://github.com/iltuoconsulenteit/DocCropper"
TARGET_DIR="$HOME/Scrivania/DocCropper"

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
    if [ -n "$(git -C "$TARGET_DIR" status --porcelain)" ]; then
      echo "💾 Modifiche locali rilevate: eseguo stash temporaneo..."
      git -C "$TARGET_DIR" stash push -u -m "pre-update-$(date +%s)"
      STASHED=true
    fi
    git -C "$TARGET_DIR" pull --rebase
    if [ "$STASHED" = true ]; then
      echo "↩️  Ripristino modifiche locali..."
      git -C "$TARGET_DIR" stash pop || true
    fi
  fi
else
  echo "📥 Clonazione repository..."
  git clone "$REPO_URL" "$TARGET_DIR"
fi

printf '\xE2\x9C\x85 Operazione completata.\n'
