"""Ponto de entrada do app desktop nativo (Qt/PySide6) do Transcritor.

Diferente do antigo desktop_app.py (pywebview) e web_launcher.py (navegador),
este é um app Qt nativo de verdade — sem HTML/CSS por baixo, sem depender
de GTK/WebKit/WebView2. Rode com: python qt_main.py
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from qt_app.main_window import MainWindow
from qt_app.theme import build_stylesheet


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Transcritor")
    app.setStyleSheet(build_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
