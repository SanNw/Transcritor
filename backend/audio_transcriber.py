"""Transcrição de áudio/vídeo (fala -> texto), via IA em nuvem ou Whisper local.

Ao contrário de PDF/EPUB/imagem, um áudio não é dividido em "páginas": o
arquivo inteiro vira um texto único. Por isso este módulo não usa `ocr.py`
(que processa página a página).

Dois motores possíveis:
- Nuvem (`transcribe_audio_file`): usa um provedor de IA com suporte a áudio
  (ver `AIProvider.supports_audio` em `ai_providers.py` — hoje OpenAI e
  Google, não a Anthropic).
- Local (`transcribe_audio_local`): usa o pacote `openai-whisper` (grátis,
  offline, equivalente ao Tesseract para OCR). Não vem instalado por padrão
  nem embutido nos pacotes .exe/.deb/AppImage — é opcional
  (`pip install -r requirements-whisper.txt`) justamente para não inchar o
  instalador com o PyTorch. Os pesos do modelo baixam sozinhos na primeira
  execução e ficam em `~/.cache/whisper` (pasta do usuário, não a pasta de
  instalação do programa).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from ai_providers import AIProvider

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".mp4", ".mkv"}

_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
}

_WHISPER_LOCAL_LANGUAGE = {"por": "pt", "eng": "en"}
DEFAULT_LOCAL_MODEL = "base"

_local_model_cache: dict[str, object] = {}


def transcribe_audio_file(path: Path, lang: str, provider: AIProvider) -> str:
    """Lê o arquivo inteiro e devolve o texto transcrito por um provedor de IA em nuvem."""
    mime_type = _MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")
    audio_bytes = path.read_bytes()
    return provider.transcribe_audio(audio_bytes, path.name, mime_type, lang)


def transcribe_audio_local(path: Path, lang: str, model_name: str = DEFAULT_LOCAL_MODEL) -> str:
    """Transcreve com o Whisper local (open-source, grátis, offline)."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg não encontrado no PATH — necessário para o Whisper local. Instale com "
            "'sudo apt-get install ffmpeg' (Linux), 'brew install ffmpeg' (macOS) ou baixe em "
            "https://ffmpeg.org/download.html (Windows) e reinicie o terminal."
        )

    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "Pacote 'openai-whisper' não instalado. Rode: pip install -r requirements-whisper.txt "
            "(aviso: instala o PyTorch, é uma dependência grande)."
        ) from exc

    model = _local_model_cache.get(model_name)
    if model is None:
        model = whisper.load_model(model_name)
        _local_model_cache[model_name] = model

    result = model.transcribe(str(path), language=_WHISPER_LOCAL_LANGUAGE.get(lang))
    return (result.get("text") or "").strip()
