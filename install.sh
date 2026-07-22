#!/usr/bin/env bash
# Instalador do Transcritor para Linux e macOS.
#
# Uso:
#   ./install.sh          instala o app desktop (janela própria, Qt/PySide6)
#   ./install.sh --ai     inclui os SDKs de IA (Claude/OpenAI/Gemini)
#   ./install.sh --yes    não pergunta nada, assume "sim" para tudo
set -euo pipefail

BOLD="$(tput bold 2>/dev/null || true)"
DIM="$(tput dim 2>/dev/null || true)"
GOLD="$(tput setaf 3 2>/dev/null || true)"
GREEN="$(tput setaf 2 2>/dev/null || true)"
RED="$(tput setaf 1 2>/dev/null || true)"
RESET="$(tput sgr0 2>/dev/null || true)"

WITH_AI=0
ASSUME_YES=0

for arg in "$@"; do
  case "$arg" in
    --ai) WITH_AI=1 ;;
    --yes|-y) ASSUME_YES=1 ;;
    *) echo "Argumento desconhecido: $arg" >&2; exit 1 ;;
  esac
done

heading() { echo; echo "${BOLD}${GOLD}== $1 ==${RESET}"; }
ok() { echo "${GREEN}✓${RESET} $1"; }
warn() { echo "${RED}!${RESET} $1"; }

confirm() {
  local prompt="$1"
  if [[ "$ASSUME_YES" == "1" ]]; then
    return 0
  fi
  read -r -p "$prompt [S/n] " reply
  [[ -z "$reply" || "$reply" =~ ^[SsYy] ]]
}

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
BIN_DIR="$HOME/.local/bin"

echo "${BOLD}${GOLD}"
echo "  TRANSCRITOR — instalador"
echo "${RESET}${DIM}  Livros, revistas, PDFs e EPUBs transformados em manuscritos .docx${RESET}"

# ---------- 1. Python ----------
heading "Verificando Python"

PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    major="${version%%.*}"
    minor="${version##*.}"
    if [[ "$major" -eq 3 && "$minor" -ge 10 ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  warn "Python 3.10+ não encontrado."
  echo "  Instale o Python 3.10 ou mais recente e rode este script de novo:"
  echo "    Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip"
  echo "    Fedora:        sudo dnf install python3"
  echo "    Arch:          sudo pacman -S python"
  echo "    macOS:         brew install python@3.12"
  exit 1
fi
ok "Usando $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"

# ---------- 2. Tesseract OCR ----------
heading "Verificando Tesseract OCR"

if command -v tesseract >/dev/null 2>&1; then
  ok "Tesseract já instalado ($(tesseract --version 2>&1 | head -1))"
else
  warn "Tesseract OCR não encontrado."

  INSTALL_CMD=""
  if command -v apt-get >/dev/null 2>&1; then
    INSTALL_CMD="sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-por python3-venv libxkbcommon0 libgl1"
  elif command -v dnf >/dev/null 2>&1; then
    INSTALL_CMD="sudo dnf install -y tesseract tesseract-langpack-por"
  elif command -v pacman >/dev/null 2>&1; then
    INSTALL_CMD="sudo pacman -S --noconfirm tesseract tesseract-data-por"
  elif command -v brew >/dev/null 2>&1; then
    INSTALL_CMD="brew install tesseract tesseract-lang"
  fi

  if [[ -z "$INSTALL_CMD" ]]; then
    warn "Não reconheci o gerenciador de pacotes deste sistema."
    echo "  Instale o Tesseract manualmente: https://github.com/tesseract-ocr/tesseract"
    exit 1
  fi

  echo "  Comando de instalação: ${BOLD}$INSTALL_CMD${RESET}"
  if confirm "Instalar o Tesseract OCR agora?"; then
    eval "$INSTALL_CMD"
    ok "Tesseract instalado."
  else
    warn "Pulei a instalação do Tesseract — o motor de OCR local não vai funcionar até você instalá-lo."
  fi
fi

# ---------- 3. Ambiente Python ----------
heading "Preparando o ambiente Python"

cd "$BACKEND_DIR"
if [[ ! -d ".venv" ]]; then
  "$PYTHON_BIN" -m venv .venv
  ok "Ambiente virtual criado em backend/.venv"
else
  ok "Ambiente virtual já existe"
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
# requirements-desktop.txt já inclui requirements.txt (modo web/API também
# fica disponível, via `transcritor --web`, sem instalação extra).
pip install --quiet -r requirements-desktop.txt
ok "App desktop (Qt) instalado"

if [[ "$WITH_AI" == "1" ]] || confirm "Instalar também os SDKs de IA (Claude/OpenAI/Gemini)?"; then
  pip install --quiet -r requirements-ai.txt
  ok "SDKs de IA instalados"
fi

deactivate

# ---------- 4. Launcher ----------
heading "Criando o comando 'transcritor'"

mkdir -p "$BIN_DIR"
LAUNCHER="$BIN_DIR/transcritor"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -e
cd "$BACKEND_DIR"
source .venv/bin/activate
if [[ "\${1:-}" == "--web" ]]; then
  echo "Abrindo em http://127.0.0.1:8000 (Ctrl+C para encerrar)"
  exec uvicorn main:app --host 127.0.0.1 --port 8000
else
  exec python qt_main.py
fi
EOF
chmod +x "$LAUNCHER"
ok "Instalado em $LAUNCHER"

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  warn "$BIN_DIR não está no seu PATH."
  echo "  Adicione ao seu ~/.bashrc ou ~/.zshrc:"
  echo "    export PATH=\"$BIN_DIR:\$PATH\""
fi

heading "Pronto"
echo "  Rode ${BOLD}transcritor${RESET} para abrir o app em janela própria,"
echo "  ou ${BOLD}transcritor --web${RESET} para abrir no navegador (modo servidor)."
