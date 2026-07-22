"""Diálogo de Configurações de IA — chaves de API por provedor."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from settings_store import PROVIDER_LABELS, PROVIDERS, masked_settings, save_settings

from .widgets import make_button


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações de IA")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("CONFIGURAÇÕES DE IA")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        note = QLabel(
            "As chaves ficam salvas apenas nesta máquina, em texto puro, e são usadas para "
            "chamar a API do provedor escolhido diretamente. Nunca são enviadas a nenhum "
            "outro serviço."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #79746A; font-size: 12px;")
        layout.addWidget(note)

        self._inputs: dict[str, QLineEdit] = {}
        self._status_labels: dict[str, QLabel] = {}

        for provider in PROVIDERS:
            layout.addWidget(self._build_provider_row(provider))

        self.feedback_label = QLabel("")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet("color: #2C4A3F; font-size: 12px;")
        layout.addWidget(self.feedback_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close_btn = make_button("Fechar", primary=False)
        close_btn.clicked.connect(self.reject)
        save_btn = make_button("Salvar chaves", icon_name="check")
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(close_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

        self._refresh_status()

    def _build_provider_row(self, provider: str) -> QWidget:
        box = QFrame()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 8, 0, 8)
        v.setSpacing(4)

        header = QHBoxLayout()
        name_label = QLabel(PROVIDER_LABELS[provider])
        name_label.setStyleSheet("font-weight: 700;")
        status_label = QLabel("")
        status_label.setStyleSheet("color: #79746A; font-size: 11px;")
        header.addWidget(name_label)
        header.addStretch(1)
        header.addWidget(status_label)
        v.addLayout(header)

        input_field = QLineEdit()
        input_field.setEchoMode(QLineEdit.Password)
        input_field.setPlaceholderText("Chave de API")
        v.addWidget(input_field)

        self._inputs[provider] = input_field
        self._status_labels[provider] = status_label

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #E4D9BE; max-height: 1px; border: none;")
        v.addWidget(divider)

        return box

    def _refresh_status(self) -> None:
        status = masked_settings()
        for provider, label in self._status_labels.items():
            info = status.get(provider, {})
            if info.get("configured"):
                label.setText(f"Configurado ({info['key_preview']}) · modelo {info['model']}")
            else:
                label.setText("Não configurado")

    def _on_save(self) -> None:
        update = {}
        for provider, field in self._inputs.items():
            value = field.text().strip()
            if value:
                update[provider] = {"api_key": value}

        if not update:
            self.feedback_label.setText("Nenhuma chave nova para salvar.")
            return

        save_settings(update)
        for field in self._inputs.values():
            field.clear()

        self.feedback_label.setText("Chaves salvas com sucesso.")
        self._refresh_status()
