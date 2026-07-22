"""Launcher desktop: abre o Transcritor em uma janela nativa, sem precisar de navegador.

Sobe o servidor FastAPI em background e o exibe dentro de uma janela do
sistema operacional via pywebview. É o ponto de entrada usado para empacotar
o app com PyInstaller (veja README.md).
"""
from __future__ import annotations

import threading
import time
import urllib.request

import uvicorn
import webview

from main import app

HOST = "127.0.0.1"
PORT = 8765


def _wait_for_server(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.5)
            return
        except Exception:
            time.sleep(0.2)


def main() -> None:
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    url = f"http://{HOST}:{PORT}"
    _wait_for_server(url)

    webview.create_window("Transcritor", url, width=1040, height=780, min_size=(760, 600))
    webview.start()

    server.should_exit = True
    server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
