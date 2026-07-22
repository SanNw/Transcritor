"""Transcritor: API local que converte PDFs/imagens de livros e revistas em .docx."""
from __future__ import annotations

import io
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_providers import GRAMMAR_INSTRUCTION, ProviderError, get_provider, run_ai_postprocess
from docx_builder import build_docx, build_docx_from_text
from ocr import extract_pages
from paths import FRONTEND_DIR, OUTPUT_DIR, UPLOAD_DIR
from settings_store import PROVIDERS, load_settings, masked_settings, save_settings

SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB

JobStatus = Literal["queued", "processing", "done", "error"]
Stage = Literal["extraindo", "aplicando_ia"]


@dataclass
class TranscribeOptions:
    lang: str
    engine: str  # "tesseract" | "ai"
    ai_provider: str | None
    post_process: str  # "none" | "grammar" | "custom"
    custom_instruction: str | None


@dataclass
class Job:
    id: str
    original_filename: str
    status: JobStatus = "queued"
    stage: Stage = "extraindo"
    pages_done: int = 0
    pages_total: int = 0
    error: str | None = None
    output_filename: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.original_filename,
            "status": self.status,
            "stage": self.stage,
            "pages_done": self.pages_done,
            "pages_total": self.pages_total,
            "error": self.error,
            "output_filename": self.output_filename,
            "created_at": self.created_at,
        }


_jobs: dict[str, Job] = {}
_jobs_lock = Lock()

app = FastAPI(title="Transcritor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run_transcription(job_id: str, upload_path: Path, options: TranscribeOptions, title: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        job.status = "processing"
        job.stage = "extraindo"

    def on_extract_progress(done: int, total: int) -> None:
        with _jobs_lock:
            job.pages_done = done
            job.pages_total = total

    def on_ai_progress(done: int, total: int) -> None:
        with _jobs_lock:
            job.pages_done = done
            job.pages_total = total

    try:
        provider = None
        needs_ai = options.engine == "ai" or options.post_process != "none"
        if needs_ai:
            provider = get_provider(options.ai_provider)  # type: ignore[arg-type]

        ocr_fn = provider.transcribe_image if options.engine == "ai" else None
        pages = extract_pages(upload_path, lang=options.lang, on_progress=on_extract_progress, ocr_fn=ocr_fn)

        output_filename = f"{job_id}.docx"
        output_path = OUTPUT_DIR / output_filename

        if options.post_process == "none":
            build_docx(pages, title=title, output_path=output_path)
        else:
            with _jobs_lock:
                job.stage = "aplicando_ia"
                job.pages_done = 0
                job.pages_total = 0

            instruction = GRAMMAR_INSTRUCTION if options.post_process == "grammar" else options.custom_instruction
            full_text = "\n\n".join(page.text for page in pages if page.text.strip())
            if not full_text.strip():
                raise ValueError("Nenhum texto foi extraído do documento para processar com IA.")

            processed_text = run_ai_postprocess(
                full_text, instruction or "", provider, on_progress=on_ai_progress  # type: ignore[arg-type]
            )
            build_docx_from_text(processed_text, title=title, output_path=output_path)

        with _jobs_lock:
            job.status = "done"
            job.output_filename = output_filename
    except (ProviderError, ValueError) as exc:
        with _jobs_lock:
            job.status = "error"
            job.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - reportado ao usuário via job.error
        with _jobs_lock:
            job.status = "error"
            job.error = str(exc)
    finally:
        upload_path.unlink(missing_ok=True)


@app.post("/api/transcribe")
async def create_transcription(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    lang: str = Form("por"),
    engine: str = Form("tesseract"),
    ai_provider: str = Form(""),
    post_process: str = Form("none"),
    custom_instruction: str = Form(""),
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado ({suffix or 'desconhecido'}). "
            f"Use um destes: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.",
        )

    if engine not in ("tesseract", "ai"):
        raise HTTPException(status_code=400, detail="Motor de transcrição inválido.")
    if post_process not in ("none", "grammar", "custom"):
        raise HTTPException(status_code=400, detail="Modo de pós-processamento inválido.")
    if post_process == "custom" and not custom_instruction.strip():
        raise HTTPException(status_code=400, detail="Escreva a instrução personalizada para a IA.")

    needs_ai = engine == "ai" or post_process != "none"
    if needs_ai:
        if ai_provider not in PROVIDERS:
            raise HTTPException(status_code=400, detail="Selecione um provedor de IA válido.")
        settings = load_settings()
        if not settings.get(ai_provider, {}).get("api_key"):
            raise HTTPException(
                status_code=400,
                detail=f"Configure a chave de API do provedor selecionado em Configurações.",
            )

    job_id = uuid.uuid4().hex
    upload_path = UPLOAD_DIR / f"{job_id}{suffix}"

    size = 0
    with upload_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                buffer.close()
                upload_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Arquivo maior que o limite de 200 MB.")
            buffer.write(chunk)

    title = Path(file.filename or "documento").stem
    job = Job(id=job_id, original_filename=file.filename or "documento")
    with _jobs_lock:
        _jobs[job_id] = job

    options = TranscribeOptions(
        lang=lang,
        engine=engine,
        ai_provider=ai_provider or None,
        post_process=post_process,
        custom_instruction=custom_instruction.strip() or None,
    )
    background_tasks.add_task(_run_transcription, job_id, upload_path, options, title)

    return job.as_dict()


@app.get("/api/jobs")
async def list_jobs() -> list[dict]:
    with _jobs_lock:
        jobs = sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)
        return [job.as_dict() for job in jobs]


@app.get("/api/jobs/download-all")
async def download_all_jobs() -> StreamingResponse:
    with _jobs_lock:
        done_jobs = [job for job in _jobs.values() if job.status == "done" and job.output_filename]

    if not done_jobs:
        raise HTTPException(status_code=409, detail="Nenhuma transcrição concluída para baixar.")

    buffer = io.BytesIO()
    used_names: set[str] = set()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for job in done_jobs:
            output_path = OUTPUT_DIR / job.output_filename
            if not output_path.exists():
                continue

            name = f"{Path(job.original_filename).stem}.docx"
            if name in used_names:
                name = f"{Path(job.original_filename).stem}-{job.id[:8]}.docx"
            used_names.add(name)

            archive.write(output_path, arcname=name)

    buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="transcricoes-{timestamp}.zip"'},
    )


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job.as_dict()


@app.get("/api/jobs/{job_id}/download")
async def download_job(job_id: str) -> FileResponse:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    if job.status != "done" or not job.output_filename:
        raise HTTPException(status_code=409, detail="Transcrição ainda não concluída.")

    output_path = OUTPUT_DIR / job.output_filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de saída não encontrado.")

    download_name = f"{Path(job.original_filename).stem}.docx"
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=download_name,
    )


class ProviderSettings(BaseModel):
    api_key: str | None = None
    model: str | None = None


class SettingsUpdate(BaseModel):
    anthropic: ProviderSettings | None = None
    openai: ProviderSettings | None = None
    google: ProviderSettings | None = None


@app.get("/api/settings")
async def get_settings() -> dict:
    return masked_settings()


@app.post("/api/settings")
async def update_settings(payload: SettingsUpdate) -> dict:
    save_settings(payload.model_dump(exclude_none=True))
    return masked_settings()


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
