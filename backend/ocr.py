"""Extração de texto de PDFs e imagens, com OCR automático para páginas escaneadas."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}

# Abaixo desse número de caracteres de texto "nativo", a página é tratada
# como escaneada e passa pelo OCR em vez do texto extraído do PDF.
MIN_NATIVE_TEXT_CHARS = 20

# Resolução (DPI) usada para rasterizar páginas de PDF antes do OCR.
OCR_RENDER_DPI = 300


@dataclass
class PageResult:
    number: int
    text: str
    used_ocr: bool


def _ocr_image(image: Image.Image, lang: str) -> str:
    return pytesseract.image_to_string(image, lang=lang).strip()


def _extract_pdf(path: Path, lang: str, on_progress: Callable[[int, int], None] | None) -> list[PageResult]:
    doc = fitz.open(path)
    total = doc.page_count
    results: list[PageResult] = []

    for index, page in enumerate(doc):
        native_text = page.get_text("text").strip()

        if len(native_text) >= MIN_NATIVE_TEXT_CHARS:
            results.append(PageResult(number=index + 1, text=native_text, used_ocr=False))
        else:
            zoom = OCR_RENDER_DPI / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            text = _ocr_image(image, lang)
            results.append(PageResult(number=index + 1, text=text, used_ocr=True))

        if on_progress:
            on_progress(index + 1, total)

    doc.close()
    return results


def _extract_image(path: Path, lang: str, on_progress: Callable[[int, int], None] | None) -> list[PageResult]:
    image = Image.open(path)
    image = image.convert("RGB")
    text = _ocr_image(image, lang)
    if on_progress:
        on_progress(1, 1)
    return [PageResult(number=1, text=text, used_ocr=True)]


def extract_pages(
    path: Path,
    lang: str = "por",
    on_progress: Callable[[int, int], None] | None = None,
) -> list[PageResult]:
    """Extrai o texto de cada página de um PDF ou de uma imagem única.

    Para PDFs, usa o texto nativo quando disponível e recorre a OCR
    apenas nas páginas sem texto selecionável (escaneadas/fotografadas).
    """
    suffix = path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        return _extract_pdf(path, lang, on_progress)
    if suffix in IMAGE_EXTENSIONS:
        return _extract_image(path, lang, on_progress)

    raise ValueError(f"Formato de arquivo não suportado: {suffix}")
