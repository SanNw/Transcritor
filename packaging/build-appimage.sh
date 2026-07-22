#!/usr/bin/env bash
# Gera um AppImage do Transcritor (qualquer distro Linux x86_64).
# Uso: packaging/build-appimage.sh [versão]
#
# Requer o binário `appimagetool` no PATH (ou em $APPIMAGETOOL). Baixe em
# https://github.com/AppImage/AppImageKit/releases
# (arquivo appimagetool-x86_64.AppImage — torne executável antes de usar).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
APPDIR="$REPO_DIR/packaging/Transcritor.AppDir"
VERSION="${1:-$(cat "$REPO_DIR/VERSION" 2>/dev/null || echo "1.0.0")}"

echo "== Compilando binário =="
"$REPO_DIR/packaging/build-pyinstaller.sh"

echo "== Montando AppDir =="
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

install -m 755 "$BACKEND_DIR/dist/transcritor" "$APPDIR/usr/bin/transcritor"
install -m 644 "$REPO_DIR/packaging/icons/transcritor-256.png" "$APPDIR/transcritor.png"
install -m 644 "$REPO_DIR/packaging/debian/transcritor.desktop" "$APPDIR/transcritor.desktop"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(CDPATH= cd -- "$(dirname -- "$(readlink -f -- "${0}")")" && pwd)"
exec "$HERE/usr/bin/transcritor" "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo "AppDir pronto em $APPDIR"

echo "== Gerando o .AppImage =="
APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"
if ! command -v "$APPIMAGETOOL" >/dev/null 2>&1; then
  cat >&2 <<EOF

appimagetool não encontrado no PATH.
Baixe em https://github.com/AppImage/AppImageKit/releases
(arquivo appimagetool-x86_64.AppImage), torne executável e rode de novo,
ou aponte APPIMAGETOOL=/caminho/para/appimagetool e rode este script outra vez.

O AppDir já está pronto em: $APPDIR
Para gerar manualmente depois: appimagetool "$APPDIR" transcritor.AppImage
EOF
  exit 1
fi

OUT_DIR="$REPO_DIR/dist-packages"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/Transcritor-${VERSION}-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUT_FILE"

echo
echo "AppImage gerado em $OUT_FILE"
