"""Transcritor: API local que converte PDFs/imagens de livros e revistas em .docx."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from docx_builder import build_docx
from ocr import extract_pages

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

for directory in (UPLOAD_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB

JobStatus = Literal["queued", "processing", "done", "error"]


@dataclass
class Job:
    id: str
    original_filename: str
    status: JobStatus = "queued"
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


def _run_transcription(job_id: str, upload_path: Path, lang: str, title: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        job.status = "processing"

    def on_progress(done: int, total: int) -> None:
        with _jobs_lock:
            job.pages_done = done
            job.pages_total = total

    try:
        pages = extract_pages(upload_path, lang=lang, on_progress=on_progress)
        output_filename = f"{job_id}.docx"
        output_path = OUTPUT_DIR / output_filename
        build_docx(pages, title=title, output_path=output_path)

        with _jobs_lock:
            job.status = "done"
            job.output_filename = output_filename
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
    lang: str = "por",
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado ({suffix or 'desconhecido'}). "
            f"Use PDF ou imagem ({', '.join(sorted(SUPPORTED_EXTENSIONS))}).",
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

    background_tasks.add_task(_run_transcription, job_id, upload_path, lang, title)

    return job.as_dict()


@app.get("/api/jobs")
async def list_jobs() -> list[dict]:
    with _jobs_lock:
        jobs = sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)
        return [job.as_dict() for job in jobs]


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


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
