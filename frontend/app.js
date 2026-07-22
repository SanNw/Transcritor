const dropzone = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const langSelect = document.getElementById("lang-select");
const engineSelect = document.getElementById("engine-select");
const postprocessSelect = document.getElementById("postprocess-select");
const providerRow = document.getElementById("provider-row");
const providerSelect = document.getElementById("provider-select");
const providerHint = document.getElementById("provider-hint");
const customInstructionRow = document.getElementById("custom-instruction-row");
const customInstructionInput = document.getElementById("custom-instruction");
const jobsSection = document.getElementById("jobs");
const jobTemplate = document.getElementById("job-template");
const downloadAllBtn = document.getElementById("download-all");

const openSettingsBtn = document.getElementById("open-settings");
const closeSettingsBtn = document.getElementById("close-settings");
const saveSettingsBtn = document.getElementById("save-settings");
const settingsOverlay = document.getElementById("settings-overlay");
const settingsFeedback = document.getElementById("settings-feedback");

const dependencyBanner = document.getElementById("dependency-banner");
const dependencyNote = document.getElementById("dependency-note");
const dependencyCommand = document.getElementById("dependency-command");
const dependencyLink = document.getElementById("dependency-link");
const dependencyFeedback = document.getElementById("dependency-feedback");
const copyCommandBtn = document.getElementById("copy-command");
const autoInstallBtn = document.getElementById("auto-install");
const recheckBtn = document.getElementById("recheck-dependency");

const jobElements = new Map();
const pollTimers = new Map();

let providerStatus = {};

const STATUS_LABELS = {
  queued: "Na fila…",
  processing: "Transcrevendo…",
  done: "Concluído",
  error: "Erro",
};

const STAGE_LABELS = {
  extraindo: "Transcrevendo",
  aplicando_ia: "Aplicando IA",
};

const STAGE_UNITS = {
  extraindo: "páginas",
  aplicando_ia: "blocos",
};

/* ---------- Upload / dropzone ---------- */

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

downloadAllBtn.addEventListener("click", () => {
  window.location.href = "/api/jobs/download-all";
});

/* ---------- Opções de IA no formulário ---------- */

function updateOptionsVisibility() {
  const needsProvider = engineSelect.value === "ai" || postprocessSelect.value !== "none";
  providerRow.hidden = !needsProvider;
  customInstructionRow.hidden = postprocessSelect.value !== "custom";
  updateProviderHint();
}

function updateProviderHint() {
  const provider = providerSelect.value;
  const status = providerStatus[provider];
  if (!status || !status.configured) {
    providerHint.textContent = "Configure a chave deste provedor em Configurações de IA.";
    providerHint.classList.add("warning");
  } else {
    providerHint.textContent = `Configurado (${status.key_preview}) · modelo ${status.model}`;
    providerHint.classList.remove("warning");
  }
}

engineSelect.addEventListener("change", updateOptionsVisibility);
postprocessSelect.addEventListener("change", updateOptionsVisibility);
providerSelect.addEventListener("change", updateProviderHint);

/* ---------- Configurações de IA ---------- */

function openSettings() {
  settingsFeedback.textContent = "";
  settingsFeedback.classList.remove("error");
  settingsOverlay.hidden = false;
}

function closeSettings() {
  settingsOverlay.hidden = true;
}

openSettingsBtn.addEventListener("click", openSettings);
closeSettingsBtn.addEventListener("click", closeSettings);
settingsOverlay.addEventListener("click", (event) => {
  if (event.target === settingsOverlay) closeSettings();
});

async function loadSettings() {
  try {
    const response = await fetch("/api/settings");
    if (!response.ok) return;
    providerStatus = await response.json();

    document.querySelectorAll(".settings-provider").forEach((node) => {
      const provider = node.dataset.provider;
      const status = providerStatus[provider];
      const statusEl = node.querySelector("[data-status]");
      if (status && status.configured) {
        statusEl.textContent = `Configurado (${status.key_preview}) · modelo ${status.model}`;
        statusEl.classList.remove("unset");
      } else {
        statusEl.textContent = "Não configurado";
        statusEl.classList.add("unset");
      }
    });

    updateProviderHint();
  } catch {
    // silencioso: painel fica com o estado padrão se a API não responder
  }
}

saveSettingsBtn.addEventListener("click", async () => {
  const payload = {};
  document.querySelectorAll(".settings-provider").forEach((node) => {
    const provider = node.dataset.provider;
    const input = node.querySelector("[data-key-input]");
    if (input.value.trim()) {
      payload[provider] = { api_key: input.value.trim() };
    }
  });

  if (Object.keys(payload).length === 0) {
    settingsFeedback.textContent = "Nenhuma chave nova para salvar.";
    settingsFeedback.classList.remove("error");
    return;
  }

  try {
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Falha ao salvar.");

    document.querySelectorAll(".settings-provider [data-key-input]").forEach((input) => {
      input.value = "";
    });

    settingsFeedback.textContent = "Chaves salvas com sucesso.";
    settingsFeedback.classList.remove("error");
    await loadSettings();
  } catch (error) {
    settingsFeedback.textContent = error.message || "Falha ao salvar as chaves.";
    settingsFeedback.classList.add("error");
  }
});

/* ---------- Jobs ---------- */

async function uploadFile(file) {
  const needsProvider = engineSelect.value === "ai" || postprocessSelect.value !== "none";
  if (needsProvider) {
    const status = providerStatus[providerSelect.value];
    if (!status || !status.configured) {
      openSettings();
      settingsFeedback.textContent = "Configure a chave do provedor selecionado antes de transcrever.";
      settingsFeedback.classList.add("error");
      return;
    }
  }
  if (postprocessSelect.value === "custom" && !customInstructionInput.value.trim()) {
    customInstructionInput.focus();
    return;
  }

  const card = renderJob({
    id: `pending-${Date.now()}`,
    filename: file.name,
    status: "queued",
    stage: "extraindo",
    pages_done: 0,
    pages_total: 0,
  });

  const formData = new FormData();
  formData.append("file", file);
  formData.append("lang", langSelect.value);
  formData.append("engine", engineSelect.value);
  formData.append("post_process", postprocessSelect.value);
  if (needsProvider) formData.append("ai_provider", providerSelect.value);
  if (postprocessSelect.value === "custom") {
    formData.append("custom_instruction", customInstructionInput.value.trim());
  }

  try {
    const response = await fetch("/api/transcribe", {
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
    downloadAllBtn.hidden = false;
  } else {
    const total = job.pages_total || 0;
    const done = job.pages_done || 0;
    const stageLabel = STAGE_LABELS[job.stage] || STATUS_LABELS[job.status] || job.status;
    const unit = STAGE_UNITS[job.stage] || "páginas";
    statusEl.textContent = total > 0 ? `${stageLabel}… (${done}/${total} ${unit})` : `${stageLabel}…`;
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

/* ---------- Checagem de dependências (Tesseract) ---------- */

async function checkDependencies() {
  try {
    const response = await fetch("/api/system-check");
    if (!response.ok) return;
    const info = await response.json();

    if (info.tesseract_installed) {
      dependencyBanner.hidden = true;
      return;
    }

    const hint = info.install_hint || {};
    dependencyBanner.hidden = false;
    dependencyNote.textContent = hint.note || "";
    dependencyCommand.textContent = hint.command || "Consulte a documentação do seu sistema.";
    dependencyLink.href = hint.url || "#";
    autoInstallBtn.hidden = !hint.auto_installable;
    dependencyFeedback.textContent = "";
    dependencyFeedback.classList.remove("error");
  } catch {
    // silencioso: sem checagem, assume que está tudo certo
  }
}

copyCommandBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(dependencyCommand.textContent);
    dependencyFeedback.textContent = "Comando copiado.";
    dependencyFeedback.classList.remove("error");
  } catch {
    dependencyFeedback.textContent = "Não foi possível copiar automaticamente — selecione o texto manualmente.";
    dependencyFeedback.classList.add("error");
  }
});

recheckBtn.addEventListener("click", checkDependencies);

autoInstallBtn.addEventListener("click", async () => {
  autoInstallBtn.disabled = true;
  dependencyFeedback.textContent = "Instalando… isso pode levar alguns minutos.";
  dependencyFeedback.classList.remove("error");
  try {
    const response = await fetch("/api/system-check/install", { method: "POST" });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || "Falha na instalação automática.");

    dependencyFeedback.textContent = "Instalado com sucesso!";
    await checkDependencies();
  } catch (error) {
    dependencyFeedback.textContent = error.message;
    dependencyFeedback.classList.add("error");
  } finally {
    autoInstallBtn.disabled = false;
  }
});

updateOptionsVisibility();
loadSettings();
loadExistingJobs();
checkDependencies();
