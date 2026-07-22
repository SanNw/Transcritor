"""Verificação de dependências do sistema (hoje, só o Tesseract OCR).

Python 3.10+ não é checado aqui: no app empacotado (PyInstaller) o Python
já vem embutido, e no modo terminal/dev quem checa a versão é o
install.sh antes mesmo de instalar as dependências Python.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import urllib.request
from pathlib import Path

from paths import TESSDATA_DIR

# Idiomas do Tesseract baixados sob demanda de um repositório próprio, em vez
# de depender do pacote de idiomas do gerenciador de pacotes do sistema — no
# Windows, por exemplo, o pacote do winget só vem com inglês por padrão, e a
# pasta de instalação (Program Files) normalmente não é gravável sem admin.
_TESSDATA_BASE_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main"


def ensure_tessdata_language(lang_code: str) -> Path:
    """Garante que `<lang_code>.traineddata` exista em TESSDATA_DIR, baixando
    do repositório oficial `tessdata_fast` se ainda não estiver presente.
    """
    target = TESSDATA_DIR / f"{lang_code}.traineddata"
    if target.exists():
        return target

    url = f"{_TESSDATA_BASE_URL}/{lang_code}.traineddata"
    tmp_path = target.with_suffix(".traineddata.part")
    try:
        urllib.request.urlretrieve(url, tmp_path)  # noqa: S310 - URL fixa, não vem de input do usuário
        tmp_path.replace(target)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Não foi possível baixar o pacote de idioma '{lang_code}' do Tesseract ({url}): {exc}"
        ) from exc
    return target

# Instaladores do Tesseract no Windows (winget ou o .exe oficial) gravam o
# PATH no registro do sistema, mas um processo já em execução (como este
# servidor) não enxerga essa mudança até reiniciar — por isso, além do
# shutil.which (que olha o PATH do processo atual), também checamos os
# caminhos de instalação padrão diretamente.
_WINDOWS_FALLBACK_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


def find_tesseract() -> str | None:
    path = shutil.which("tesseract")
    if path:
        return path
    if platform.system() == "Windows":
        for candidate in _WINDOWS_FALLBACK_PATHS:
            if Path(candidate).is_file():
                return candidate
    return None


def _tesseract_version() -> str | None:
    path = find_tesseract()
    if not path:
        return None
    try:
        output = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=5
        ).stdout
        return output.splitlines()[0].strip() if output else "instalado"
    except (OSError, subprocess.SubprocessError, IndexError):
        return "instalado"


def _install_hint() -> dict:
    system = platform.system()

    if system == "Linux":
        return {
            "os": "linux",
            "command": "sudo apt-get install -y tesseract-ocr tesseract-ocr-por",
            "note": "Em distribuições sem apt (Fedora, Arch), use dnf/pacman com o pacote 'tesseract'.",
            "url": "https://github.com/tesseract-ocr/tesseract",
            "auto_installable": False,
        }
    if system == "Darwin":
        return {
            "os": "macos",
            "command": "brew install tesseract tesseract-lang",
            "note": "Requer o Homebrew (https://brew.sh) instalado.",
            "url": "https://github.com/tesseract-ocr/tesseract",
            "auto_installable": True,
        }
    if system == "Windows":
        return {
            "os": "windows",
            "command": (
                "winget install -e --id UB-Mannheim.TesseractOCR "
                "--silent --accept-package-agreements --accept-source-agreements"
            ),
            "note": (
                "Instala via winget (pacote oficial da UB Mannheim). Se o winget não estiver "
                "disponível, baixe e rode o instalador manualmente, marcando o idioma 'Portuguese'."
            ),
            "url": "https://github.com/UB-Mannheim/tesseract/wiki",
            "auto_installable": True,
        }

    return {
        "os": "unknown",
        "command": None,
        "note": "Instale o Tesseract OCR pelo gerenciador de pacotes do seu sistema.",
        "url": "https://github.com/tesseract-ocr/tesseract",
        "auto_installable": False,
    }


def check_system() -> dict:
    version = _tesseract_version()
    result = {
        "tesseract_installed": version is not None,
        "tesseract_version": version,
    }
    if version is None:
        result["install_hint"] = _install_hint()
    return result
