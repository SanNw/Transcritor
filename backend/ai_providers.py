"""Provedores de IA usados como motor de OCR e para pós-processar o texto
(correção gramatical, formatação como livro, ou qualquer instrução livre
como resumir, traduzir, listar personagens, etc.)
"""
from __future__ import annotations

import base64
import io
from abc import ABC, abstractmethod
from typing import Callable

from PIL import Image

import languages
from settings_store import DEFAULT_MODELS, get_provider_config

TRANSCRIBE_PROMPT_TEMPLATE = (
    "Transcreva fielmente todo o texto visível nesta imagem de página de "
    "livro, revista ou documento ({language_instruction}). Preserve "
    "parágrafos e a ordem de leitura. Escreva no idioma original do "
    "documento — NÃO traduza, mesmo que seja para o idioma que estou usando "
    "para conversar com você. Se não houver texto legível, responda com uma "
    "string vazia. Responda apenas com o texto transcrito, sem comentários, "
    "explicações ou formatação markdown."
)

AUDIO_TRANSCRIBE_PROMPT_TEMPLATE = (
    "Transcreva fielmente toda a fala presente neste áudio "
    "({language_instruction}). Ignore ruído de fundo e música, foque no que "
    "é dito. Organize em parágrafos quando fizer sentido (mudança de assunto "
    "ou pausa longa). Escreva no idioma original da fala — NÃO traduza, "
    "mesmo que seja para o idioma que estou usando para conversar com você. "
    "Se não houver fala perceptível, responda com uma string vazia. Responda "
    "apenas com o texto transcrito, sem comentários, marcações de tempo ou "
    "identificação de quem fala."
)


def _language_instruction(lang: str) -> str:
    if lang == languages.AUTO:
        return "identifique e use o idioma original automaticamente"
    return f"idioma esperado: {languages.display_name(lang)}"


GRAMMAR_INSTRUCTION = (
    "Você é um revisor editorial. Corrija erros de ortografia, gramática e "
    "pontuação no texto abaixo (provavelmente fruto de OCR, então pode ter "
    "ruído de reconhecimento). Preserve o conteúdo e o sentido original — "
    "não resuma nem invente informação. Organize o resultado em parágrafos "
    "e, quando fizer sentido, em capítulos/seções com um título curto para "
    "cada um, como em um livro bem formatado. Responda apenas com o texto "
    "revisado, sem comentários adicionais."
)

MAX_CHUNK_CHARS = 12000


class ProviderError(RuntimeError):
    """Erro de configuração ou de chamada a um provedor de IA."""


class AIProvider(ABC):
    name = "provider"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    supports_audio = False

    @abstractmethod
    def transcribe_image(self, image: Image.Image, lang: str) -> str: ...

    @abstractmethod
    def run_instruction(self, text: str, instruction: str) -> str: ...

    def transcribe_audio(self, audio_bytes: bytes, filename: str, mime_type: str, lang: str) -> str:
        raise ProviderError(
            f"{self.name} não oferece transcrição de áudio/fala nesta API. "
            "Use OpenAI ou Google Gemini para arquivos de áudio/vídeo."
        )


def _image_to_base64_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def _client(self):
        try:
            import anthropic
        except ImportError as exc:
            raise ProviderError(
                "Pacote 'anthropic' não instalado. Rode: pip install -r requirements-ai.txt"
            ) from exc
        return anthropic.Anthropic(api_key=self.api_key)

    def transcribe_image(self, image: Image.Image, lang: str) -> str:
        client = self._client()
        prompt = TRANSCRIBE_PROMPT_TEMPLATE.format(language_instruction=_language_instruction(lang))
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": _image_to_base64_png(image),
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            return "".join(block.text for block in response.content if block.type == "text").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - erro de rede/API repassado ao usuário
            raise ProviderError(f"Erro na API da Anthropic: {exc}") from exc

    def run_instruction(self, text: str, instruction: str) -> str:
        client = self._client()
        prompt = f"{instruction}\n\n---\nTEXTO:\n{text}"
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in response.content if block.type == "text").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API da Anthropic: {exc}") from exc


class OpenAIProvider(AIProvider):
    name = "openai"
    supports_audio = True

    def _client(self):
        try:
            import openai
        except ImportError as exc:
            raise ProviderError(
                "Pacote 'openai' não instalado. Rode: pip install -r requirements-ai.txt"
            ) from exc
        return openai.OpenAI(api_key=self.api_key)

    def transcribe_image(self, image: Image.Image, lang: str) -> str:
        client = self._client()
        prompt = TRANSCRIBE_PROMPT_TEMPLATE.format(language_instruction=_language_instruction(lang))
        b64 = _image_to_base64_png(image)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API da OpenAI: {exc}") from exc

    def run_instruction(self, text: str, instruction: str) -> str:
        client = self._client()
        prompt = f"{instruction}\n\n---\nTEXTO:\n{text}"
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return (response.choices[0].message.content or "").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API da OpenAI: {exc}") from exc

    def transcribe_audio(self, audio_bytes: bytes, filename: str, mime_type: str, lang: str) -> str:
        client = self._client()
        try:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, audio_bytes, mime_type),
                language=languages.whisper_code(lang),
            )
            return (response.text or "").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API da OpenAI (Whisper): {exc}") from exc


class GoogleProvider(AIProvider):
    name = "google"
    supports_audio = True

    def _client(self):
        try:
            from google import genai
        except ImportError as exc:
            raise ProviderError(
                "Pacote 'google-genai' não instalado. Rode: pip install -r requirements-ai.txt"
            ) from exc
        return genai.Client(api_key=self.api_key)

    def transcribe_image(self, image: Image.Image, lang: str) -> str:
        from google.genai import types

        client = self._client()
        prompt = TRANSCRIBE_PROMPT_TEMPLATE.format(language_instruction=_language_instruction(lang))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/png"),
                ],
            )
            return (response.text or "").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API do Google: {exc}") from exc

    def run_instruction(self, text: str, instruction: str) -> str:
        client = self._client()
        prompt = f"{instruction}\n\n---\nTEXTO:\n{text}"
        try:
            response = client.models.generate_content(model=self.model, contents=prompt)
            return (response.text or "").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API do Google: {exc}") from exc

    def transcribe_audio(self, audio_bytes: bytes, filename: str, mime_type: str, lang: str) -> str:
        from google.genai import types

        client = self._client()
        prompt = AUDIO_TRANSCRIBE_PROMPT_TEMPLATE.format(language_instruction=_language_instruction(lang))
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                ],
            )
            return (response.text or "").strip()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Erro na API do Google: {exc}") from exc


_PROVIDER_CLASSES: dict[str, type[AIProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google": GoogleProvider,
}


def get_provider(name: str) -> AIProvider:
    if name not in _PROVIDER_CLASSES:
        raise ProviderError(f"Provedor de IA desconhecido: {name}")

    config = get_provider_config(name)
    api_key = config.get("api_key")
    if not api_key:
        raise ProviderError(
            f"Nenhuma chave de API configurada para {name}. Configure em Configurações."
        )

    model = config.get("model") or DEFAULT_MODELS[name]
    return _PROVIDER_CLASSES[name](api_key=api_key, model=model)


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if current and current_len + len(paragraph) > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += len(paragraph) + 2

    if current:
        chunks.append("\n\n".join(current))

    return chunks or [text]


def run_ai_postprocess(
    full_text: str,
    instruction: str,
    provider: AIProvider,
    on_progress: Callable[[int, int], None] | None = None,
) -> str:
    """Aplica `instruction` ao texto via IA, dividindo em blocos quando o
    texto é longo demais para uma única chamada (map) e unindo o resultado
    numa passada final de síntese (reduce) quando houve mais de um bloco.
    """
    chunks = chunk_text(full_text)
    total = len(chunks)
    results: list[str] = []

    for index, chunk in enumerate(chunks):
        results.append(provider.run_instruction(chunk, instruction))
        if on_progress:
            on_progress(index + 1, total)

    if len(results) == 1:
        return results[0]

    combined = "\n\n".join(results)
    synthesis_instruction = (
        f"{instruction}\n\nO texto abaixo foi processado em partes separadas "
        "porque o documento original era longo demais para uma única "
        "chamada. Una as partes em um resultado único, coerente e sem "
        "repetições ou marcações de divisão."
    )
    return provider.run_instruction(combined, synthesis_instruction)
