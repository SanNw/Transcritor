"""Armazenamento local das chaves de API de cada provedor de IA.

As chaves ficam em texto puro em CONFIG_PATH (na pasta de dados do app,
nunca no repositório). Isso é comum para apps locais/desktop, mas vale
deixar claro: quem tiver acesso a essa máquina tem acesso às chaves.
"""
from __future__ import annotations

import json
from typing import Any

from paths import CONFIG_PATH

PROVIDERS = ("anthropic", "openai", "google")

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-4o",
    "google": "gemini-2.0-flash",
}

PROVIDER_LABELS = {
    "anthropic": "Anthropic Claude",
    "openai": "OpenAI",
    "google": "Google Gemini",
}


def load_settings() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_settings(update: dict[str, dict[str, Any]]) -> dict[str, Any]:
    current = load_settings()
    for provider, values in update.items():
        if provider not in PROVIDERS:
            continue
        entry = current.setdefault(provider, {})
        for key, value in values.items():
            if value is None:
                continue
            if value == "":
                entry.pop(key, None)
            else:
                entry[key] = value
    CONFIG_PATH.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    return current


def get_provider_config(provider: str) -> dict[str, Any]:
    return load_settings().get(provider, {})


def masked_settings() -> dict[str, Any]:
    current = load_settings()
    result = {}
    for provider in PROVIDERS:
        entry = current.get(provider, {})
        key = entry.get("api_key", "")
        result[provider] = {
            "label": PROVIDER_LABELS[provider],
            "configured": bool(key),
            "key_preview": f"••••{key[-4:]}" if key else None,
            "model": entry.get("model") or DEFAULT_MODELS[provider],
        }
    return result
