"""Worker em background (QThread) para rodar a extração/OCR e o
pós-processamento por IA sem travar a interface.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from ai_providers import GRAMMAR_INSTRUCTION, ProviderError, get_provider, run_ai_postprocess
from docx_builder import build_docx, build_docx_from_text
from ocr import extract_pages


class TranscriptionWorker(QThread):
    stage_changed = Signal(str)  # "extraindo" | "aplicando_ia"
    progress = Signal(int, int)  # done, total
    finished_ok = Signal(str)  # caminho do .docx gerado
    failed = Signal(str)  # mensagem de erro

    def __init__(
        self,
        file_path: Path,
        title: str,
        lang: str,
        engine: str,
        ai_provider: str | None,
        post_process: str,
        custom_instruction: str | None,
        output_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self.title = title
        self.lang = lang
        self.engine = engine
        self.ai_provider = ai_provider
        self.post_process = post_process
        self.custom_instruction = custom_instruction
        self.output_path = output_path

    def run(self) -> None:
        try:
            provider = None
            needs_ai = self.engine == "ai" or self.post_process != "none"
            if needs_ai:
                provider = get_provider(self.ai_provider)  # type: ignore[arg-type]

            self.stage_changed.emit("extraindo")
            ocr_fn = provider.transcribe_image if self.engine == "ai" else None
            pages = extract_pages(
                self.file_path,
                lang=self.lang,
                on_progress=lambda done, total: self.progress.emit(done, total),
                ocr_fn=ocr_fn,
            )

            if self.post_process == "none":
                build_docx(pages, title=self.title, output_path=self.output_path)
            else:
                self.stage_changed.emit("aplicando_ia")
                self.progress.emit(0, 0)

                instruction = (
                    GRAMMAR_INSTRUCTION if self.post_process == "grammar" else self.custom_instruction
                )
                full_text = "\n\n".join(page.text for page in pages if page.text.strip())
                if not full_text.strip():
                    raise ValueError("Nenhum texto foi extraído do documento para processar com IA.")

                processed_text = run_ai_postprocess(
                    full_text,
                    instruction or "",
                    provider,  # type: ignore[arg-type]
                    on_progress=lambda done, total: self.progress.emit(done, total),
                )
                build_docx_from_text(processed_text, title=self.title, output_path=self.output_path)

            self.finished_ok.emit(str(self.output_path))
        except (ProviderError, ValueError) as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - reportado ao usuário via sinal
            self.failed.emit(str(exc))
