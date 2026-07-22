"""Ícones monocromáticos (SVG inline, mesma família em todo o app) usados
pelos widgets do app desktop. Reaproveita os mesmos traçados do modo web
para manter a identidade visual consistente entre as duas interfaces.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="{color}" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)

PATHS = {
    "file": '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v4h4"/>',
    "globe": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M3 12h18M12 3c2.5 2.5 4 5.5 4 9s-1.5 6.5-4 9'
        'c-2.5-2.5-4-5.5-4-9s1.5-6.5 4-9z"/>'
    ),
    "gear": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1'
        'M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>'
    ),
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/>',
    "robot": (
        '<rect x="5" y="8" width="14" height="10" rx="2"/>'
        '<circle cx="9.5" cy="13" r="1" fill="{color}"/>'
        '<circle cx="14.5" cy="13" r="1" fill="{color}"/>'
        '<path d="M12 8V5M9 5h6"/>'
    ),
    "pencil": '<path d="M4 20l1-4L16 5l3 3L8 19l-4 1z"/><path d="M14 7l3 3"/>',
    "cloud_upload": (
        '<path d="M7 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 16.9 8.1 4.5 4.5 0 0 1 16.5 18H7z"/>'
        '<path d="M12 11v6M9.5 13.5 12 11l2.5 2.5"/>'
    ),
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 11h1v5"/>',
    "lightbulb": (
        '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3 11.2c.6.4 1 1 1 1.8h4'
        'c0-.8.4-1.4 1-1.8A6 6 0 0 0 12 3z"/>'
    ),
    "play": '<path d="M6 4l14 8-14 8V4z"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "gauge": '<circle cx="12" cy="12" r="9"/><path d="M12 12l4-4M12 7v1"/>',
    "check": '<path d="M4 12l5 5L20 6"/>',
}


def svg_markup(name: str, color: str = "#B9974D") -> str:
    body = PATHS[name].replace("{color}", color)
    return _SVG_TEMPLATE.format(color=color, body=body)


def svg_icon(name: str, color: str = "#B9974D", size: int = 20) -> QIcon:
    renderer = QSvgRenderer(QByteArray(svg_markup(name, color).encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def svg_pixmap(name: str, color: str = "#B9974D", size: int = 48) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg_markup(name, color).encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


ICON_SIZE = QSize(18, 18)
