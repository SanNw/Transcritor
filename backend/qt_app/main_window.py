"""Janela principal do Transcritor — layout de 4 cards (Arquivo, Configuração
da transcrição, Inteligência Artificial, Execução), inspirado em Qt
Creator/Obsidian/VS Code/JetBrains.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from paths import OUTPUT_DIR
from settings_store import masked_settings
from system_check import check_system

from .dependency_dialog import DependencyDialog
from .icons import svg_icon, svg_pixmap
from .settings_dialog import SettingsDialog
from .widgets import make_button, make_card, make_combo, make_field, make_info_box
from .worker import TranscriptionWorker

SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF",
    ".epub": "EPUB",
    ".png": "Imagem",
    ".jpg": "Imagem",
    ".jpeg": "Imagem",
    ".tif": "Imagem",
    ".tiff": "Imagem",
    ".bmp": "Imagem",
    ".webp": "Imagem",
}

FILE_DIALOG_FILTER = (
    "Documentos suportados (*.pdf *.epub *.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp);;"
    "Todos os arquivos (*)"
)

STAGE_LABELS = {
    "extraindo": "Transcrevendo",
    "aplicando_ia": "Aplicando IA",
}
STAGE_UNITS = {
    "extraindo": "páginas",
    "aplicando_ia": "blocos",
}


class DropZone(QFrame):
    fileChosen = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(svg_pixmap("cloud_upload", color="#B9974D", size=48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        self.title_label = QLabel("Arraste um arquivo aqui ou clique para escolher")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 15px; font-weight: 700;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.hint_label = QLabel("PDF, EPUB, PNG, JPG, TIFF, BMP ou WEBP · até 200 MB")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #79746A; font-size: 11px;")
        layout.addWidget(self.hint_label)

        self.choose_button = make_button("Escolher arquivo", icon_name="folder", primary=False)
        self.choose_button.clicked.connect(self._open_dialog)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.choose_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (nome definido pelo Qt)
        if event.button() == Qt.LeftButton:
            self._open_dialog()
        super().mousePressEvent(event)

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Escolher arquivo", "", FILE_DIALOG_FILTER)
        if path:
            self.fileChosen.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        urls = event.mimeData().urls()
        if urls:
            self.fileChosen.emit(urls[0].toLocalFile())


class FeatureBadge(QWidget):
    def __init__(self, icon_name: str, title: str, description: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        icon_label = QLabel()
        icon_label.setPixmap(svg_icon(icon_name, color="#2C4A3F").pixmap(20, 20))
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 700; font-size: 12px;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #79746A; font-size: 11px;")
        layout.addWidget(desc_label)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Transcritor")
        self.resize(1180, 860)
        self.setMinimumSize(880, 640)

        self.staged_file: Path | None = None
        self.worker: TranscriptionWorker | None = None

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        body.setMaximumWidth(1400)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(20)

        columns = QHBoxLayout()
        columns.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        left_col.addWidget(self._build_file_card())
        left_col.addWidget(self._build_ai_card())
        left_col.addStretch(1)

        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        right_col.addWidget(self._build_config_card())
        right_col.addWidget(self._build_execution_card())
        right_col.addStretch(1)

        columns.addLayout(left_col, 1)
        columns.addLayout(right_col, 1)
        body_layout.addLayout(columns)

        # Centraliza o conteúdo em telas muito largas (ex.: 4K) em vez de
        # esticar os cards até ficarem vazios — igual VS Code/Obsidian.
        center_wrapper = QWidget()
        center_layout = QHBoxLayout(center_wrapper)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addStretch(1)
        center_layout.addWidget(body)
        center_layout.addStretch(1)

        scroll.setWidget(center_wrapper)
        root.addWidget(scroll, 1)

        root.addWidget(self._build_footer())

        self._sync_visibility()
        self._check_dependencies(startup=True)

    # ---------- Cabeçalho ----------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet("background: #F3E9D2; border-bottom: 1px solid #B9974D;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        crest = QLabel()
        crest.setPixmap(self._build_crest_pixmap())
        layout.addWidget(crest)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel("TRANSCRITOR")
        title.setObjectName("appTitle")
        subtitle = QLabel("Livros, revistas, PDFs e EPUBs transformados em manuscritos .docx")
        subtitle.setObjectName("appSubtitle")
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        layout.addLayout(text_col)

        layout.addStretch(1)

        settings_btn = make_button("Configurações de IA", icon_name="gear", primary=False)
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        return header

    def _build_crest_pixmap(self):
        from PySide6.QtCore import QByteArray, QSize
        from PySide6.QtGui import QPainter, QPixmap
        from PySide6.QtSvg import QSvgRenderer

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 72">'
            '<path d="M32 4 L58 14 V34 C58 51 47 62 32 68 C17 62 6 51 6 34 V14 Z" '
            'fill="#1B2A41" stroke="#B9974D" stroke-width="2.5"/>'
            '<path d="M32 28 V48 M32 28 C26 24 20 25 16 28 V46 C20 43 26 42 32 46 '
            'M32 28 C38 24 44 25 48 28 V46 C44 43 38 42 32 46" '
            'stroke="#B9974D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            "</svg>"
        )
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(QSize(48, 54))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setStyleSheet("background: #F3E9D2; border-top: 1px solid #B9974D;")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 8, 24, 8)

        help_btn = make_button("Ajuda", icon_name="lightbulb", primary=False)
        help_btn.clicked.connect(self._open_help)
        layout.addWidget(help_btn)

        layout.addStretch(1)

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #79746A; font-size: 11px;")
        layout.addWidget(version_label)

        return footer

    # ---------- Card 1: Arquivo ----------

    def _build_file_card(self) -> QWidget:
        card, layout = make_card("1. Arquivo", icon_name="file")

        self.dropzone = DropZone()
        self.dropzone.fileChosen.connect(self._on_file_chosen)
        layout.addWidget(self.dropzone)

        self.file_info_row = QFrame()
        self.file_info_row.setObjectName("infoBox")
        info_layout = QHBoxLayout(self.file_info_row)
        info_layout.setContentsMargins(12, 10, 12, 10)

        self.file_icon_label = QLabel()
        info_layout.addWidget(self.file_icon_label)

        name_col = QVBoxLayout()
        self.file_name_label = QLabel("")
        self.file_name_label.setStyleSheet("font-weight: 700;")
        self.file_meta_label = QLabel("")
        self.file_meta_label.setStyleSheet("color: #79746A; font-size: 11px;")
        name_col.addWidget(self.file_name_label)
        name_col.addWidget(self.file_meta_label)
        info_layout.addLayout(name_col, 1)

        remove_btn = QPushButton()
        remove_btn.setIcon(svg_icon("trash", color="#5B1E2D"))
        remove_btn.setObjectName("secondaryButton")
        remove_btn.setFixedSize(34, 34)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(self._clear_file)
        info_layout.addWidget(remove_btn)

        self.file_info_row.hide()
        layout.addWidget(self.file_info_row)

        return card

    # ---------- Card 2: Configuração da transcrição ----------

    def _build_config_card(self) -> QWidget:
        card, layout = make_card("2. Configuração da transcrição", icon_name="gear")

        self.lang_combo = make_combo(
            [("por", "Português"), ("eng", "Inglês"), ("por+eng", "Português + Inglês")]
        )
        layout.addWidget(make_field("Idioma do conteúdo", self.lang_combo, icon_name="globe"))

        self.engine_combo = make_combo(
            [("tesseract", "Tesseract (local, grátis)"), ("ai", "Inteligência artificial")]
        )
        self.engine_combo.currentIndexChanged.connect(self._sync_visibility)
        layout.addWidget(make_field("Motor de transcrição (OCR)", self.engine_combo, icon_name="gear"))

        self.postprocess_combo = make_combo(
            [
                ("none", "Nenhum"),
                ("grammar", "Corrigir e formatar como livro"),
                ("custom", "Instrução personalizada"),
            ]
        )
        self.postprocess_combo.currentIndexChanged.connect(self._sync_visibility)
        layout.addWidget(make_field("Pós-processamento", self.postprocess_combo, icon_name="sparkle"))

        return card

    # ---------- Card 3: Inteligência Artificial ----------

    def _build_ai_card(self) -> QWidget:
        card, layout = make_card("3. Inteligência artificial", icon_name="robot")

        self.provider_combo = make_combo(
            [
                ("anthropic", "Anthropic Claude"),
                ("openai", "OpenAI"),
                ("google", "Google Gemini"),
            ]
        )
        self.provider_combo.currentIndexChanged.connect(self._sync_visibility)
        self.provider_field = make_field("Provedor de IA", self.provider_combo, icon_name="robot")
        layout.addWidget(self.provider_field)

        self.provider_info_box, self.provider_info_label = make_info_box("")
        layout.addWidget(self.provider_info_box)

        self.instruction_field_wrapper = QWidget()
        instruction_layout = QVBoxLayout(self.instruction_field_wrapper)
        instruction_layout.setContentsMargins(0, 0, 0, 0)
        instruction_layout.setSpacing(5)

        instruction_label = QLabel("Instrução personalizada (opcional)")
        instruction_label.setObjectName("fieldLabel")
        instruction_layout.addWidget(instruction_label)

        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setPlaceholderText(
            "Ex.: resuma esta obra em até 2 páginas · traduza para o inglês · "
            "liste os personagens principais"
        )
        self.instruction_input.setMaximumHeight(90)
        self.instruction_input.textChanged.connect(self._on_instruction_changed)
        instruction_layout.addWidget(self.instruction_input)

        self.instruction_counter = QLabel("0/1000")
        self.instruction_counter.setAlignment(Qt.AlignRight)
        self.instruction_counter.setStyleSheet("color: #79746A; font-size: 10px;")
        instruction_layout.addWidget(self.instruction_counter)

        layout.addWidget(self.instruction_field_wrapper)

        return card

    # ---------- Card 4: Execução ----------

    def _build_execution_card(self) -> QWidget:
        card, layout = make_card("4. Execução", icon_name="play")

        self.status_info_box, self.status_info_label = make_info_box(
            "Pronto para transcrever. Revise as configurações ao lado e clique em iniciar."
        )
        layout.addWidget(self.status_info_box)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(18)
        badges_row.addWidget(FeatureBadge("shield", "Privacidade", "Seus arquivos não saem do seu computador."))
        badges_row.addWidget(FeatureBadge("lock", "Seguro", "Processamento local sempre que possível."))
        badges_row.addWidget(FeatureBadge("gauge", "Eficiente", "Tecnologia otimizada para resultados de qualidade."))
        layout.addLayout(badges_row)

        progress_header = QHBoxLayout()
        progress_label = QLabel("Progresso")
        progress_label.setObjectName("fieldLabel")
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setStyleSheet("color: #79746A; font-size: 11px;")
        progress_header.addWidget(progress_label)
        progress_header.addStretch(1)
        progress_header.addWidget(self.progress_percent_label)
        layout.addLayout(progress_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        status_header = QHBoxLayout()
        status_caption = QLabel("Status")
        status_caption.setObjectName("fieldLabel")
        self.status_text_label = QLabel("Aguardando início…")
        self.status_text_label.setStyleSheet("font-size: 12px;")
        status_header.addWidget(status_caption)
        status_header.addSpacing(10)
        status_header.addWidget(self.status_text_label, 1)
        layout.addLayout(status_header)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        self.clear_button = make_button("Limpar tudo", icon_name="trash", primary=False)
        self.clear_button.clicked.connect(self._clear_file)
        self.start_button = make_button("Iniciar transcrição", icon_name="play")
        self.start_button.setObjectName("primaryAction")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self._start_transcription)
        buttons_row.addWidget(self.clear_button)
        buttons_row.addWidget(self.start_button)
        layout.addLayout(buttons_row)

        return card

    # ---------- Comportamento ----------

    def _on_file_chosen(self, path: str) -> None:
        file_path = Path(path)
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            QMessageBox.warning(
                self,
                "Formato não suportado",
                f"'{suffix or 'desconhecido'}' não é suportado.\n\n"
                f"Formatos aceitos: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.",
            )
            return

        self.staged_file = file_path
        self.file_name_label.setText(file_path.name)
        size_mb = file_path.stat().st_size / (1024 * 1024)
        self.file_meta_label.setText(f"{size_mb:.2f} MB · {SUPPORTED_EXTENSIONS[suffix]}")
        self.file_icon_label.setPixmap(svg_icon("file", color="#1B2A41").pixmap(24, 24))
        self.file_info_row.show()
        self.start_button.setEnabled(True)
        self.status_info_label.setText("Pronto para transcrever. Revise as configurações ao lado e clique em iniciar.")

    def _clear_file(self) -> None:
        self.staged_file = None
        self.file_info_row.hide()
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")
        self.status_text_label.setText("Aguardando início…")
        self.status_info_label.setText("Pronto para transcrever. Revise as configurações ao lado e clique em iniciar.")

    def _on_instruction_changed(self) -> None:
        count = len(self.instruction_input.toPlainText())
        if count > 1000:
            text = self.instruction_input.toPlainText()[:1000]
            self.instruction_input.blockSignals(True)
            self.instruction_input.setPlainText(text)
            self.instruction_input.blockSignals(False)
            count = 1000
        self.instruction_counter.setText(f"{count}/1000")

    def _sync_visibility(self) -> None:
        post_process = self.postprocess_combo.currentData()
        self.instruction_field_wrapper.setVisible(post_process == "custom")

        # O provedor de IA fica sempre visível no card (como no design de
        # referência) — só é obrigatório de fato quando o motor é "ai" ou
        # há pós-processamento, o que é validado na hora de iniciar.
        provider = self.provider_combo.currentData()
        status = masked_settings().get(provider, {})
        if status.get("configured"):
            self.provider_info_label.setText(
                f"Configurado ({status['key_preview']}) · modelo {status['model']}"
            )
        else:
            self.provider_info_label.setText("Configure a chave deste provedor em Configurações de IA.")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()
        self._sync_visibility()

    def _open_help(self) -> None:
        QMessageBox.information(
            self,
            "Dicas e ajuda",
            "• Escolha o arquivo primeiro, ajuste as opções e clique em Iniciar transcrição.\n\n"
            "• PDFs escaneados e imagens passam por OCR automaticamente.\n\n"
            "• O motor de IA e o pós-processamento exigem uma chave de API configurada em "
            "Configurações de IA.\n\n"
            "• Instruções personalizadas aceitam qualquer pedido em texto livre: resumir, "
            "traduzir, listar personagens etc.",
        )

    def _check_dependencies(self, startup: bool = False) -> None:
        info = check_system()
        if not info["tesseract_installed"]:
            if startup:
                # Não bloqueia o uso do app — só avisa, já que o motor de IA
                # continua disponível sem o Tesseract.
                DependencyDialog(info, self).show()

    def _start_transcription(self) -> None:
        if not self.staged_file:
            return

        engine = self.engine_combo.currentData()
        post_process = self.postprocess_combo.currentData()
        ai_provider = self.provider_combo.currentData()
        custom_instruction = self.instruction_input.toPlainText().strip()

        needs_ai = engine == "ai" or post_process != "none"
        if needs_ai:
            status = masked_settings().get(ai_provider, {})
            if not status.get("configured"):
                QMessageBox.warning(
                    self,
                    "Chave de API necessária",
                    "Configure a chave do provedor selecionado em Configurações de IA antes de continuar.",
                )
                return
        if post_process == "custom" and not custom_instruction:
            QMessageBox.warning(self, "Instrução necessária", "Escreva a instrução personalizada para a IA.")
            return

        self.start_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")
        self.status_text_label.setText("Iniciando…")
        self.status_info_label.setText("Transcrição em andamento — isso pode levar alguns minutos.")

        output_path = OUTPUT_DIR / f"{self.staged_file.stem}.docx"
        title = self.staged_file.stem

        self.worker = TranscriptionWorker(
            file_path=self.staged_file,
            title=title,
            lang=self.lang_combo.currentData(),
            engine=engine,
            ai_provider=ai_provider if needs_ai else None,
            post_process=post_process,
            custom_instruction=custom_instruction or None,
            output_path=output_path,
        )
        self.worker.stage_changed.connect(self._on_stage_changed)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_stage_changed(self, stage: str) -> None:
        label = STAGE_LABELS.get(stage, stage)
        self.status_text_label.setText(f"{label}…")

    def _on_progress(self, done: int, total: int) -> None:
        stage = "aplicando_ia" if "Aplicando" in self.status_text_label.text() else "extraindo"
        unit = STAGE_UNITS.get(stage, "itens")
        if total > 0:
            percent = int((done / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_percent_label.setText(f"{percent}%")
            self.status_text_label.setText(f"{self.status_text_label.text().split('…')[0]}… ({done}/{total} {unit})")
        else:
            self.progress_bar.setValue(0)

    def _on_finished(self, output_path: str) -> None:
        self.progress_bar.setValue(100)
        self.progress_percent_label.setText("100%")
        self.status_text_label.setText("Concluído")
        self.status_info_label.setText(f"Transcrição concluída: {output_path}")
        self.start_button.setEnabled(True)
        self.clear_button.setEnabled(True)

        result = QMessageBox.question(
            self,
            "Transcrição concluída",
            f"Arquivo gerado em:\n{output_path}\n\nAbrir a pasta agora?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self._open_containing_folder(Path(output_path))

    def _on_failed(self, message: str) -> None:
        self.status_text_label.setText("Erro")
        self.status_info_label.setText(f"Falha na transcrição: {message}")
        self.start_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        QMessageBox.critical(self, "Falha na transcrição", message)

    @staticmethod
    def _open_containing_folder(path: Path) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
