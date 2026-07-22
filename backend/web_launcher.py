"""Launcher usado pelos pacotes .deb/AppImage/.exe: sobe o servidor local e
abre o navegador padrão do sistema — ao contrário do modo desktop
(desktop_app.py), não depende de GTK/WebKit, o que o torna muito mais
portátil entre distribuições Linux.
"""
from __future__ import annotations

import threading
import time
import urllib.request
import webbrowser

import uvicorn

from main import app

HOST = "127.0.0.1"
PORT = 8000


def _open_when_ready(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.5)
            webbrowser.open(url)
            return
        except Exception:
            time.sleep(0.2)


def main() -> None:
    url = f"http://{HOST}:{PORT}"
    threading.Thread(target=_open_when_ready, args=(url,), daemon=True).start()
    print(f"Transcritor rodando em {url} (Ctrl+C para encerrar)")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
