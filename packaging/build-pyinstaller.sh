#!/usr/bin/env bash
# Compila o binário standalone do app desktop Qt/PySide6 do Transcritor,
# usado pelos pacotes .deb, AppImage e pelo instalador Windows. Roda em
# Linux/macOS/Windows (via Git Bash/WSL) — o binário resultante só serve
# para o SO onde rodou.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"

cd "$BACKEND_DIR"

if [[ ! -d ".venv-build" ]]; then
  python3 -m venv .venv-build
fi

# shellcheck disable=SC1091
source .venv-build/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements-desktop.txt

rm -rf build dist transcritor.spec
pyinstaller --name transcritor --onefile --windowed \
  --icon "../packaging/icons/transcritor.ico" \
  qt_main.py

deactivate

echo "Binário gerado em $BACKEND_DIR/dist/transcritor"
