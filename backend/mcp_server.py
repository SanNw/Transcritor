"""Servidor MCP: expõe a transcrição do Transcritor como ferramenta para
Claude Desktop/Claude Code, sem precisar abrir o app web.

Reaproveita diretamente os módulos do backend (ocr.py, audio_transcriber.py,
ai_providers.py, docx_builder.py) — não sobe o servidor FastAPI, não depende
de main.py.

Rodar (stdio, como o Claude Desktop/Code esperam):
    python mcp_server.py

Ver no README como registrar isso no Claude Desktop ou com `claude mcp add`.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from ai_providers import GRAMMAR_INSTRUCTION, get_provider, run_ai_postprocess
from audio_transcriber import AUDIO_EXTENSIONS, transcribe_audio_file, transcribe_audio_local
from docx_builder import build_docx, build_docx_from_text
from ocr import PageResult, extract_pages
from paths import OUTPUT_DIR

DOCUMENT_EXTENSIONS = {".pdf", ".epub", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
SUPPORTED_EXTENSIONS = DOCUMENT_EXTENSIONS | AUDIO_EXTENSIONS

mcp = FastMCP("transcritor")


@mcp.tool()
def transcrever(
    caminho_arquivo: str,
    motor: str = "tesseract",
    provedor_ia: str = "",
    idioma: str = "por",
    pos_processamento: str = "none",
    instrucao: str = "",
    formato_saida: str = "docx",
) -> str:
    """Transcreve um PDF, EPUB, imagem ou áudio/vídeo em texto.

    Args:
        caminho_arquivo: Caminho absoluto do arquivo a transcrever. Formatos
            aceitos: PDF, EPUB, PNG, JPG, JPEG, TIF, TIFF, BMP, WEBP (documento)
            ou MP3, WAV, FLAC, M4A, MP4, MKV (áudio/vídeo).
        motor: Para documentos, "tesseract" (OCR local, grátis) ou "ai"
            (motor de IA, mais preciso em digitalizações difíceis). Para
            áudio/vídeo, "whisper" (local, grátis, offline — requer
            `pip install -r requirements-whisper.txt` e `ffmpeg` instalado)
            ou "ai" (nuvem, via OpenAI ou Google).
        provedor_ia: "anthropic", "openai" ou "google". Necessário quando
            motor="ai" ou pos_processamento != "none". Para áudio/vídeo com
            motor="ai", use "openai" ou "google" — a Anthropic Claude não
            suporta áudio nesta API.
        idioma: "por", "eng" ou "por+eng".
        pos_processamento: "none", "grammar" (corrige e formata como livro)
            ou "custom" (segue `instrucao` livre — resumir, traduzir, listar
            personagens etc.). Sempre exige um provedor de IA em nuvem,
            mesmo quando a transcrição em si usa um motor local.
        instrucao: obrigatória quando pos_processamento="custom".
        formato_saida: "docx" (padrão — devolve o caminho do arquivo .docx
            gerado) ou "text" (devolve o texto transcrito diretamente).

    Returns:
        O caminho do .docx gerado, ou o texto transcrito (conforme
        `formato_saida`).
    """
    path = Path(caminho_arquivo).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Arquivo não encontrado: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Formato não suportado ({suffix or 'desconhecido'}). "
            f"Use um destes: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    is_audio = suffix in AUDIO_EXTENSIONS
    valid_engines = ("ai", "whisper") if is_audio else ("tesseract", "ai")
    if motor not in valid_engines:
        raise ValueError(
            f"Motor inválido para este tipo de arquivo: '{motor}'. Use um destes: {', '.join(valid_engines)}."
        )
    if pos_processamento not in ("none", "grammar", "custom"):
        raise ValueError("pos_processamento inválido: use 'none', 'grammar' ou 'custom'.")
    if pos_processamento == "custom" and not instrucao.strip():
        raise ValueError("Informe `instrucao` quando pos_processamento='custom'.")
    if formato_saida not in ("docx", "text"):
        raise ValueError("formato_saida inválido: use 'docx' ou 'text'.")

    needs_ai = motor == "ai" or pos_processamento != "none"
    provider = None
    if needs_ai:
        if provedor_ia not in ("anthropic", "openai", "google"):
            raise ValueError("Informe `provedor_ia`: 'anthropic', 'openai' ou 'google'.")
        if is_audio and motor == "ai" and provedor_ia == "anthropic":
            raise ValueError(
                "A Anthropic Claude não suporta transcrição de áudio/vídeo nesta API. "
                "Use provedor_ia='openai' ou 'google'."
            )
        provider = get_provider(provedor_ia)

    title = path.stem
    pages: list[PageResult] | None = None

    if is_audio:
        if motor == "whisper":
            raw_text = transcribe_audio_local(path, idioma)
        else:
            raw_text = transcribe_audio_file(path, idioma, provider)  # type: ignore[arg-type]
        if not raw_text.strip():
            raise ValueError("Nenhuma fala foi reconhecida neste áudio.")
    else:
        ocr_fn = provider.transcribe_image if motor == "ai" else None  # type: ignore[union-attr]
        pages = extract_pages(path, lang=idioma, ocr_fn=ocr_fn)
        raw_text = "\n\n".join(page.text for page in pages if page.text.strip())

    if pos_processamento == "none":
        final_text = raw_text
    else:
        if not raw_text.strip():
            raise ValueError("Nenhum texto foi extraído do documento para processar com IA.")
        instruction = GRAMMAR_INSTRUCTION if pos_processamento == "grammar" else instrucao
        final_text = run_ai_postprocess(raw_text, instruction, provider)  # type: ignore[arg-type]

    if formato_saida == "text":
        return final_text

    output_path = OUTPUT_DIR / f"mcp-{uuid.uuid4().hex}.docx"
    if pages is not None and pos_processamento == "none":
        build_docx(pages, title=title, output_path=output_path)
    else:
        build_docx_from_text(final_text, title=title, output_path=output_path)

    return str(output_path)


if __name__ == "__main__":
    mcp.run()
