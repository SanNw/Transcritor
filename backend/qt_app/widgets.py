"""Funções utilitárias para construir widgets padronizados — mesma altura,
raio, padding e fonte em todo o app, para não repetir esse código em cada
tela (janela principal, diálogos etc.)
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .icons import svg_icon


def make_card(title: str, icon_name: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Cria um "card" (QFrame estilizado como grupo) com título e um
    QVBoxLayout já configurado para receber o conteúdo.
    """
    card = QFrame()
    card.setObjectName("card")

    outer = QVBoxLayout(card)
    outer.setContentsMargins(20, 18, 20, 20)
    outer.setSpacing(14)

    header = QWidget()
    header_layout = _row(header, spacing=8)
    if icon_name:
        icon_label = QLabel()
        icon_label.setPixmap(svg_icon(icon_name, color="#B9974D").pixmap(20, 20))
        header_layout.addWidget(icon_label)
    title_label = QLabel(title.upper())
    title_label.setObjectName("sectionTitle")
    header_layout.addWidget(title_label)
    header_layout.addStretch(1)
    outer.addWidget(header)

    divider = QFrame()
    divider.setFrameShape(QFrame.HLine)
    divider.setStyleSheet("color: #B9974D; background: #B9974D; max-height: 1px; border: none;")
    outer.addWidget(divider)

    content = QVBoxLayout()
    content.setSpacing(14)
    outer.addLayout(content)

    return card, content


def _row(widget: QWidget, spacing: int = 8):
    from PySide6.QtWidgets import QHBoxLayout

    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(spacing)
    return layout


def make_field(label_text: str, widget: QWidget, icon_name: str | None = None) -> QWidget:
    """Envolve um widget (combo, input etc.) com um rótulo padronizado em
    cima, no mesmo estilo em todo o app.
    """
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    label_row = QWidget()
    label_layout = _row(label_row, spacing=6)
    if icon_name:
        icon_label = QLabel()
        icon_label.setPixmap(svg_icon(icon_name, color="#79746A").pixmap(14, 14))
        label_layout.addWidget(icon_label)
    label = QLabel(label_text)
    label.setObjectName("fieldLabel")
    label_layout.addWidget(label)
    label_layout.addStretch(1)

    layout.addWidget(label_row)
    layout.addWidget(widget)
    return wrapper


def make_button(
    text: str,
    icon_name: str | None = None,
    primary: bool = True,
    icon_color: str | None = None,
) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(38)
    if not primary:
        btn.setObjectName("secondaryButton")
    if icon_name:
        color = icon_color or ("#B9974D" if primary else "#5B1E2D")
        btn.setIcon(svg_icon(icon_name, color=color))
    return btn


def make_combo(options: list[tuple[str, str]]) -> QComboBox:
    """options: lista de (valor, rótulo)."""
    combo = QComboBox()
    combo.setMinimumHeight(34)
    for value, label in options:
        combo.addItem(label, value)
    return combo


def make_info_box(text: str) -> tuple[QFrame, QLabel]:
    box = QFrame()
    box.setObjectName("infoBox")
    layout = _row(box, spacing=8)
    layout.setContentsMargins(12, 10, 12, 10)

    icon_label = QLabel()
    icon_label.setPixmap(svg_icon("info", color="#8E8A7F").pixmap(16, 16))
    icon_label.setAlignment(Qt.AlignTop)
    layout.addWidget(icon_label)

    text_label = QLabel(text)
    text_label.setWordWrap(True)
    layout.addWidget(text_label, 1)

    return box, text_label
