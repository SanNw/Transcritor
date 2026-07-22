"""Caminhos compartilhados entre os módulos do backend.

Em um executável empacotado (PyInstaller), os arquivos ficam extraídos em
sys._MEIPASS e o diretório de trabalho não é gravável — por isso os dados
do usuário (uploads, saídas, chaves de API) vão para a pasta pessoal em vez
de ficar ao lado do código.
"""
from __future__ import annotations

import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    FRONTEND_DIR = BASE_DIR / "frontend"
    DATA_DIR = Path.home() / ".transcritor"
else:
    BASE_DIR = Path(__file__).resolve().parent
    FRONTEND_DIR = BASE_DIR.parent / "frontend"
    DATA_DIR = BASE_DIR / "data"

UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
TESSDATA_DIR = DATA_DIR / "tessdata"
CONFIG_PATH = DATA_DIR / "config.json"

for directory in (UPLOAD_DIR, OUTPUT_DIR, TESSDATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)
