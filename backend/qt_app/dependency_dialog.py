"""Diálogo de aviso quando o Tesseract OCR não está instalado."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from system_check import check_system

from .widgets import make_button


class DependencyDialog(QDialog):
    def __init__(self, info: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tesseract OCR não encontrado")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("TESSERACT OCR NÃO ENCONTRADO")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        text = QLabel(
            "O motor de OCR local não está instalado nesta máquina. Você ainda pode usar o "
            "motor de IA (se tiver uma chave configurada em Configurações de IA), mas o "
            "Tesseract é necessário para o OCR local gratuito."
        )
        text.setWordWrap(True)
        layout.addWidget(text)

        hint = info.get("install_hint", {}) or {}
        if hint.get("note"):
            note = QLabel(hint["note"])
            note.setWordWrap(True)
            note.setStyleSheet("color: #79746A; font-size: 12px;")
            layout.addWidget(note)

        command_row = QHBoxLayout()
        self.command_field = QLineEdit(hint.get("command") or "Consulte a documentação do seu sistema.")
        self.command_field.setReadOnly(True)
        self.command_field.setCursorPosition(0)
        copy_btn = make_button("Copiar", primary=False)
        copy_btn.clicked.connect(self._copy_command)
        command_row.addWidget(self.command_field, 1)
        command_row.addWidget(copy_btn)
        layout.addLayout(command_row)

        self.feedback = QLabel("")
        self.feedback.setStyleSheet("font-size: 11px; color: #2C4A3F;")
        layout.addWidget(self.feedback)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close_btn = make_button("Fechar", primary=False)
        close_btn.clicked.connect(self.reject)
        recheck_btn = make_button("Já instalei, verificar de novo")
        recheck_btn.clicked.connect(self._recheck)
        buttons.addWidget(close_btn)
        buttons.addWidget(recheck_btn)
        layout.addLayout(buttons)

    def _copy_command(self) -> None:
        QApplication.clipboard().setText(self.command_field.text())
        self.feedback.setText("Comando copiado.")

    def _recheck(self) -> None:
        info = check_system()
        if info["tesseract_installed"]:
            self.accept()
        else:
            self.feedback.setText("Ainda não encontrei o Tesseract instalado.")
