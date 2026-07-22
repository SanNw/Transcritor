"""Paleta e folha de estilo Qt (QSS) do Transcritor — mesmas cores do
design system medieval usado no modo web, adaptadas para widgets nativos.
"""
from __future__ import annotations

COLORS = {
    "azul_profundo": "#1B2A41",
    "verde_floresta": "#2C4A3F",
    "vinho": "#5B1E2D",
    "dourado": "#B9974D",
    "pergaminho": "#F3E9D2",
    "pedra": "#8E8A7F",
    "surface": "#FBF6EA",
    "surface_alt": "#F1E6D0",
    "text": "#1B2A41",
    "muted": "#79746A",
    "border": "#B9974D",
    "success": "#2C4A3F",
    "error": "#5B1E2D",
}

# Fontes de sistema, sem depender de download — mantém a identidade visual
# sem introduzir uma dependência de rede num app desktop nativo.
FONT_BODY = '"Segoe UI", "Ubuntu", "Helvetica Neue", Arial, sans-serif'
FONT_DISPLAY = 'Georgia, "Cambria", "Times New Roman", serif'


def build_stylesheet() -> str:
    c = COLORS
    return f"""
    * {{
        font-family: {FONT_BODY};
    }}

    QMainWindow, #centralWidget, QScrollArea, QScrollArea > QWidget > QWidget {{
        background: {c['pergaminho']};
    }}

    QLabel {{
        color: {c['text']};
    }}

    QLabel#appTitle {{
        font-family: {FONT_DISPLAY};
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 1px;
        color: {c['azul_profundo']};
    }}

    QLabel#appSubtitle {{
        color: {c['muted']};
        font-size: 12px;
    }}

    QLabel#fieldLabel {{
        color: {c['muted']};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }}

    QLabel#sectionTitle {{
        font-size: 13px;
        font-weight: 700;
        color: {c['azul_profundo']};
    }}

    QFrame#card {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
    }}

    QFrame#dropZone {{
        background: {c['surface']};
        border: 2px dashed {c['dourado']};
        border-radius: 10px;
    }}

    QFrame#dropZone[dragActive="true"] {{
        background: {c['surface_alt']};
        border-color: {c['azul_profundo']};
    }}

    QFrame#infoBox {{
        background: {c['surface_alt']};
        border: 1px solid {c['dourado']};
        border-radius: 6px;
    }}

    QFrame#infoBox QLabel {{
        color: {c['muted']};
        font-size: 12px;
    }}

    QPushButton {{
        background: {c['azul_profundo']};
        color: {c['dourado']};
        border: 1.5px solid {c['dourado']};
        border-radius: 6px;
        padding: 9px 20px;
        font-weight: 700;
        font-size: 12px;
    }}

    QPushButton:hover {{
        background: #24354e;
    }}

    QPushButton:pressed {{
        background: #16233a;
    }}

    QPushButton:disabled {{
        background: #d9d2bd;
        color: #a39c8a;
        border-color: #d9d2bd;
    }}

    QPushButton#secondaryButton {{
        background: transparent;
        color: {c['vinho']};
        border: 1.5px solid {c['vinho']};
    }}

    QPushButton#secondaryButton:hover {{
        background: rgba(91, 30, 45, 0.08);
    }}

    QPushButton#primaryAction {{
        padding: 12px 28px;
        font-size: 13px;
    }}

    QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {{
        background: white;
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {c['text']};
        selection-background-color: {c['dourado']};
    }}

    QComboBox {{
        min-height: 22px;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background: white;
        border: 1px solid {c['border']};
        selection-background-color: {c['dourado']};
        selection-color: {c['azul_profundo']};
        outline: none;
    }}

    QProgressBar {{
        border: 1px solid {c['border']};
        border-radius: 6px;
        background: {c['surface_alt']};
        text-align: center;
        color: {c['text']};
        height: 18px;
    }}

    QProgressBar::chunk {{
        background: {c['dourado']};
        border-radius: 5px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
    }}

    QScrollBar::handle:vertical {{
        background: {c['dourado']};
        border-radius: 5px;
        min-height: 24px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QDialog {{
        background: {c['pergaminho']};
    }}

    QToolTip {{
        background: {c['azul_profundo']};
        color: {c['pergaminho']};
        border: 1px solid {c['dourado']};
        padding: 4px 8px;
    }}
    """
