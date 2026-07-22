"""Verificação de dependências do sistema (hoje, só o Tesseract OCR).

Python 3.10+ não é checado aqui: no app empacotado (PyInstaller) o Python
já vem embutido, e no modo terminal/dev quem checa a versão é o
install.sh antes mesmo de instalar as dependências Python.
"""
from __future__ import annotations

import platform
import shutil
import subprocess


def _tesseract_version() -> str | None:
    path = shutil.which("tesseract")
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
            "command": None,
            "note": "Baixe e rode o instalador oficial, marcando o idioma 'Portuguese'.",
            "url": "https://github.com/UB-Mannheim/tesseract/wiki",
            "auto_installable": False,
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
