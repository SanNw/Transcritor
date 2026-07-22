"""Tabela única de idiomas de CONTEÚDO (o idioma do documento/áudio sendo
transcrito — não confundir com o idioma da INTERFACE do app, que é tratado
inteiramente no frontend via `frontend/i18n.js`).

Cada motor de transcrição usa um código de idioma diferente (Tesseract usa
códigos de 3 letras do ISO 639-2/T, Whisper usa ISO 639-1 de 2 letras, as IAs
multimodais só precisam de um nome legível no prompt) — esta tabela existe
para não espalhar esses mapeamentos em cada módulo.
"""
from __future__ import annotations

from dataclasses import dataclass

AUTO = "auto"


@dataclass(frozen=True)
class Language:
    code: str
    name_pt: str
    name_en: str
    tesseract: str | None  # código de 3 letras do tessdata_fast; None = Tesseract não suporta
    whisper: str | None  # ISO 639-1 usado pelo Whisper (local e API); None = Whisper não suporta
    tesseract_limited: bool = False  # aviso: OCR local historicamente mais fraco neste idioma/script


LANGUAGES: tuple[Language, ...] = (
    Language("por", "Português", "Portuguese", "por", "pt"),
    Language("eng", "Inglês", "English", "eng", "en"),
    Language("spa", "Espanhol", "Spanish", "spa", "es"),
    Language("fra", "Francês", "French", "fra", "fr"),
    Language("deu", "Alemão", "German", "deu", "de"),
    Language("ita", "Italiano", "Italian", "ita", "it"),
    Language("nld", "Holandês", "Dutch", "nld", "nl"),
    Language("rus", "Russo", "Russian", "rus", "ru"),
    Language("jpn", "Japonês", "Japanese", "jpn", "ja", tesseract_limited=True),
    Language("kor", "Coreano", "Korean", "kor", "ko", tesseract_limited=True),
    Language("chi_sim", "Chinês (simplificado)", "Chinese (simplified)", "chi_sim", "zh", tesseract_limited=True),
    Language("chi_tra", "Chinês (tradicional)", "Chinese (traditional)", "chi_tra", "zh", tesseract_limited=True),
    Language("ara", "Árabe", "Arabic", "ara", "ar", tesseract_limited=True),
    Language("hin", "Hindi", "Hindi", "hin", "hi", tesseract_limited=True),
    Language("ben", "Bengali", "Bengali", "ben", "bn", tesseract_limited=True),
    Language("vie", "Vietnamita", "Vietnamese", "vie", "vi", tesseract_limited=True),
    Language("tha", "Tailandês", "Thai", "tha", "th", tesseract_limited=True),
    Language("tur", "Turco", "Turkish", "tur", "tr"),
    Language("pol", "Polonês", "Polish", "pol", "pl"),
    Language("swa", "Suaíli", "Swahili", "swa", "sw", tesseract_limited=True),
    Language("ukr", "Ucraniano", "Ukrainian", "ukr", "uk"),
    Language("ell", "Grego", "Greek", "ell", "el"),
    Language("heb", "Hebraico", "Hebrew", "heb", "he", tesseract_limited=True),
    Language("ind", "Indonésio", "Indonesian", "ind", "id"),
)

BY_CODE: dict[str, Language] = {lang.code: lang for lang in LANGUAGES}


def get(code: str) -> Language | None:
    return BY_CODE.get(code)


def tesseract_code(code: str) -> str:
    """Converte um código combinado (ex.: 'por+eng') em código(s) do Tesseract."""
    parts = []
    for part in code.split("+"):
        lang = BY_CODE.get(part)
        if lang is None or lang.tesseract is None:
            raise ValueError(f"Idioma '{part}' não é suportado pelo Tesseract.")
        parts.append(lang.tesseract)
    return "+".join(parts)


def whisper_code(code: str) -> str | None:
    """Código Whisper (ISO 639-1) para um único idioma, ou None (auto-detecção)."""
    if code == AUTO or "+" in code:
        return None
    lang = BY_CODE.get(code)
    return lang.whisper if lang else None


def display_name(code: str, pt: bool = True) -> str:
    if code == AUTO:
        return "detecção automática" if pt else "automatic detection"
    parts = []
    for part in code.split("+"):
        lang = BY_CODE.get(part)
        parts.append((lang.name_pt if pt else lang.name_en) if lang else part)
    return " + ".join(parts)
