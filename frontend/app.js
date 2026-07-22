const dropzone = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const langSelect = document.getElementById("lang-select");
const jobsSection = document.getElementById("jobs");
const jobTemplate = document.getElementById("job-template");

const jobElements = new Map();
const pollTimers = new Map();

const STATUS_LABELS = {
  queued: "Na fila…",
  processing: "Transcrevendo…",
  done: "Concluído",
  error: "Erro",
};

dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  const files = event.dataTransfer.files;
  if (files.length) uploadFile(files[0]);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
  fileInput.value = "";
});

async function uploadFile(file) {
  const card = renderJob({
    id: `pending-${Date.now()}`,
    filename: file.name,
    status: "queued",
    pages_done: 0,
    pages_total: 0,
  });

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`/api/transcribe?lang=${encodeURIComponent(langSelect.value)}`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Falha no envio (${response.status})`);
    }

    const job = await response.json();
    jobElements.delete(card.dataset.tempId);
    card.remove();
    renderJob(job);
    pollJob(job.id);
  } catch (error) {
    updateJobCard(card, {
      status: "error",
      filename: file.name,
      error: error.message,
    });
  }
}

function renderJob(job) {
  const existing = jobElements.get(job.id);
  if (existing) {
    updateJobCard(existing, job);
    return existing;
  }

  const node = jobTemplate.content.firstElementChild.cloneNode(true);
  node.dataset.tempId = job.id;
  jobsSection.prepend(node);
  jobElements.set(job.id, node);
  updateJobCard(node, job);
  return node;
}

function updateJobCard(node, job) {
  const nameEl = node.querySelector("[data-name]");
  const statusEl = node.querySelector("[data-status]");
  const barEl = node.querySelector("[data-progress-bar]");
  const downloadEl = node.querySelector("[data-download]");

  nameEl.textContent = job.filename;
  statusEl.className = "job-status";

  if (job.status === "error") {
    statusEl.textContent = `Erro: ${job.error || "falha desconhecida"}`;
    statusEl.classList.add("error");
    barEl.style.width = "0%";
  } else if (job.status === "done") {
    statusEl.textContent = STATUS_LABELS.done;
    statusEl.classList.add("done");
    barEl.style.width = "100%";
    downloadEl.hidden = false;
    downloadEl.href = `/api/jobs/${job.id}/download`;
  } else {
    const total = job.pages_total || 0;
    const done = job.pages_done || 0;
    statusEl.textContent =
      total > 0 ? `${STATUS_LABELS[job.status] || job.status} (${done}/${total} páginas)` : STATUS_LABELS[job.status] || job.status;
    barEl.style.width = total > 0 ? `${(done / total) * 100}%` : "8%";
  }
}

function pollJob(jobId) {
  const timer = setInterval(async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`);
      if (!response.ok) throw new Error("Job não encontrado");
      const job = await response.json();
      renderJob(job);

      if (job.status === "done" || job.status === "error") {
        clearInterval(timer);
        pollTimers.delete(jobId);
      }
    } catch (error) {
      clearInterval(timer);
      pollTimers.delete(jobId);
    }
  }, 1200);

  pollTimers.set(jobId, timer);
}

async function loadExistingJobs() {
  try {
    const response = await fetch("/api/jobs");
    if (!response.ok) return;
    const jobs = await response.json();
    jobs.forEach((job) => {
      renderJob(job);
      if (job.status === "queued" || job.status === "processing") pollJob(job.id);
    });
  } catch {
    // silencioso: lista fica vazia se a API ainda não respondeu
  }
}

loadExistingJobs();
