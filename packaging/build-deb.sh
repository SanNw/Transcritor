#!/usr/bin/env bash
# Gera um pacote .deb do Transcritor (Debian/Ubuntu e derivados).
# Uso: packaging/build-deb.sh [versão]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
PKG_NAME="transcritor"
ARCH="amd64"
VERSION="${1:-$(cat "$REPO_DIR/VERSION" 2>/dev/null || echo "1.0.0")}"

echo "== Compilando binário =="
"$REPO_DIR/packaging/build-pyinstaller.sh"

echo "== Montando estrutura do pacote =="
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT
chmod 755 "$STAGE_DIR"

mkdir -p \
  "$STAGE_DIR/DEBIAN" \
  "$STAGE_DIR/usr/bin" \
  "$STAGE_DIR/usr/share/applications" \
  "$STAGE_DIR/usr/share/doc/$PKG_NAME" \
  "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps" \
  "$STAGE_DIR/usr/share/icons/hicolor/128x128/apps" \
  "$STAGE_DIR/usr/share/icons/hicolor/48x48/apps"

install -m 755 "$BACKEND_DIR/dist/transcritor" "$STAGE_DIR/usr/bin/transcritor"
install -m 644 "$REPO_DIR/packaging/debian/transcritor.desktop" "$STAGE_DIR/usr/share/applications/"
install -m 644 "$REPO_DIR/README.md" "$STAGE_DIR/usr/share/doc/$PKG_NAME/README.md"
install -m 644 "$REPO_DIR/packaging/icons/transcritor-256.png" "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps/transcritor.png"
install -m 644 "$REPO_DIR/packaging/icons/transcritor-128.png" "$STAGE_DIR/usr/share/icons/hicolor/128x128/apps/transcritor.png"
install -m 644 "$REPO_DIR/packaging/icons/transcritor-48.png" "$STAGE_DIR/usr/share/icons/hicolor/48x48/apps/transcritor.png"

INSTALLED_SIZE=$(du -sk "$STAGE_DIR/usr" | cut -f1)

cat > "$STAGE_DIR/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Installed-Size: $INSTALLED_SIZE
Depends: tesseract-ocr, tesseract-ocr-por
Maintainer: Transcritor <noreply@transcritor.local>
Description: Transcreve livros, revistas, PDFs e EPUBs em .docx
 Converte PDFs, EPUBs e imagens de livros/revistas (digitais ou
 escaneados) em arquivos .docx, com OCR local (Tesseract) ou via IA
 (Claude, OpenAI, Gemini), incluindo correção gramatical, formatação
 como livro e instruções livres como resumir ou traduzir.
EOF

echo "== Empacotando =="
OUT_DIR="$REPO_DIR/dist-packages"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

dpkg-deb --build --root-owner-group "$STAGE_DIR" "$OUT_FILE"

echo
echo "Pacote gerado em $OUT_FILE"
echo "Instale com: sudo apt install $OUT_FILE"
