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
const uiLangSelect = document.getElementById("ui-lang-select");

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
const jobData = new Map();
const pollTimers = new Map();

let providerStatus = {};
let contentLanguages = [];

const STATUS_KEYS = { queued: "statusQueued", processing: "statusProcessing", done: "statusDone", error: "statusError" };
const STAGE_KEYS = { extraindo: "stageExtraindo", transcrevendo_audio: "stageTranscrevendoAudio", aplicando_ia: "stageAplicandoIa" };
const STAGE_UNIT_KEYS = { extraindo: "unitPaginas", transcrevendo_audio: "unitArquivos", aplicando_ia: "unitBlocos" };

const AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".m4a", ".mp4", ".mkv"];

function isAudioFile(file) {
  const name = file.name.toLowerCase();
  return AUDIO_EXTENSIONS.some((ext) => name.endsWith(ext));
}

/* ---------- Idioma da interface ---------- */

function populateUiLangSelect() {
  uiLangSelect.innerHTML = "";
  UI_LANGUAGES.forEach(({ code, label }) => {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = label;
    if (code === getUiLanguage()) option.selected = true;
    uiLangSelect.appendChild(option);
  });
}

uiLangSelect.addEventListener("change", () => {
  setUiLanguage(uiLangSelect.value);
});

document.addEventListener("i18n:applied", () => {
  populateLangSelect();
  updateLangHint();
  updateProviderHint();
  renderProviderStatuses();
  jobData.forEach((job, id) => {
    const node = jobElements.get(id);
    if (node) updateJobCard(node, job);
  });
});

/* ---------- Idioma do conteúdo (documento/áudio) ---------- */

async function loadContentLanguages() {
  try {
    const response = await fetch("/api/languages");
    if (!response.ok) return;
    contentLanguages = await response.json();
    populateLangSelect();
  } catch {
    // silencioso: seletor fica só com "detectar automaticamente"
  }
}

function populateLangSelect() {
  const previous = langSelect.value || "auto";
  langSelect.innerHTML = "";

  const autoOption = document.createElement("option");
  autoOption.value = "auto";
  autoOption.textContent = t("langAuto");
  langSelect.appendChild(autoOption);

  const usePt = getUiLanguage() === "pt-BR";
  const sorted = [...contentLanguages].sort((a, b) =>
    (usePt ? a.name_pt : a.name_en).localeCompare(usePt ? b.name_pt : b.name_en)
  );
  sorted.forEach((lang) => {
    const option = document.createElement("option");
    option.value = lang.code;
    option.textContent = (usePt ? lang.name_pt : lang.name_en) + (lang.tesseract_limited ? t("langLimitedSuffix") : "");
    option.dataset.limited = lang.tesseract_limited ? "1" : "";
    langSelect.appendChild(option);
  });

  langSelect.value = [...langSelect.options].some((o) => o.value === previous) ? previous : "auto";
  if (langSelect.value === "auto" && engineSelect.value === "tesseract") {
    langSelect.value = detectContentLanguageFallback();
  }
}

function detectContentLanguageFallback() {
  const primary = (navigator.language || "en").split("-")[0].toLowerCase();
  const byBrowserLocale = contentLanguages.find((l) => l.whisper === primary);
  if (byBrowserLocale) return byBrowserLocale.code;
  const english = contentLanguages.find((l) => l.code === "eng");
  if (english) return english.code;
  const first = [...langSelect.options].find((o) => o.value !== "auto");
  return first ? first.value : "auto";
}

function updateLangHint() {
  const langHint = document.getElementById("lang-hint");
  const selected = langSelect.selectedOptions[0];
  const limited = selected && selected.dataset.limited === "1";
  langHint.textContent = limited && engineSelect.value === "tesseract" ? t("langLimitedWarning") : "";
}

langSelect.addEventListener("change", () => {
  if (langSelect.value === "auto" && engineSelect.value === "tesseract") {
    engineSelect.value = "ai";
    updateOptionsVisibility();
  }
  updateLangHint();
});

/* ---------- Opções de IA no formulário ---------- */

function updateOptionsVisibility() {
  const needsProvider = engineSelect.value === "ai" || postprocessSelect.value !== "none";
  providerRow.hidden = !needsProvider;
  customInstructionRow.hidden = postprocessSelect.value !== "custom";
  updateProviderHint();
  updateLangHint();
}

function updateProviderHint() {
  const provider = providerSelect.value;
  const status = providerStatus[provider];
  if (!status || !status.configured) {
    providerHint.textContent = t("providerHintMissing");
    providerHint.classList.add("warning");
  } else {
    providerHint.textContent = t("providerHintConfigured", { key: status.key_preview, model: status.model });
    providerHint.classList.remove("warning");
  }
}

engineSelect.addEventListener("change", () => {
  if (engineSelect.value === "tesseract" && langSelect.value === "auto") {
    langSelect.value = detectContentLanguageFallback();
  }
  updateOptionsVisibility();
});
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

function renderProviderStatuses() {
  document.querySelectorAll(".settings-provider").forEach((node) => {
    const provider = node.dataset.provider;
    const status = providerStatus[provider];
    const statusEl = node.querySelector("[data-status]");
    if (status && status.configured) {
      statusEl.textContent = t("providerHintConfigured", { key: status.key_preview, model: status.model });
      statusEl.classList.remove("unset");
    } else {
      statusEl.textContent = t("notConfigured");
      statusEl.classList.add("unset");
    }
  });
}

async function loadSettings() {
  try {
    const response = await fetch("/api/settings");
    if (!response.ok) return;
    providerStatus = await response.json();
    renderProviderStatuses();
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
    settingsFeedback.textContent = t("noNewKeys");
    settingsFeedback.classList.remove("error");
    return;
  }

  try {
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(t("keysSaveFailed"));

    document.querySelectorAll(".settings-provider [data-key-input]").forEach((input) => {
      input.value = "";
    });

    settingsFeedback.textContent = t("keysSaved");
    settingsFeedback.classList.remove("error");
    await loadSettings();
  } catch (error) {
    settingsFeedback.textContent = error.message || t("keysSaveFailed");
    settingsFeedback.classList.add("error");
  }
});

/* ---------- Jobs ---------- */

async function uploadFile(file) {
  if (isAudioFile(file)) {
    if (engineSelect.value === "tesseract") {
      engineSelect.value = "ai";
      updateOptionsVisibility();
    }
    if (engineSelect.value === "ai" && providerSelect.value === "anthropic") {
      providerSelect.value = "openai";
      updateProviderHint();
    }
  } else if (engineSelect.value === "whisper") {
    engineSelect.value = "tesseract";
    updateOptionsVisibility();
  }

  const needsProvider = engineSelect.value === "ai" || postprocessSelect.value !== "none";
  if (needsProvider) {
    const status = providerStatus[providerSelect.value];
    if (!status || !status.configured) {
      openSettings();
      settingsFeedback.textContent = t("configureProviderFirst");
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
    stage: isAudioFile(file) ? "transcrevendo_audio" : "extraindo",
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
      throw new Error(body.detail || t("uploadFailed", { status: response.status }));
    }

    const job = await response.json();
    jobElements.delete(card.dataset.tempId);
    jobData.delete(card.dataset.tempId);
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
  jobData.set(job.id || node.dataset.tempId, job);

  const nameEl = node.querySelector("[data-name]");
  const statusEl = node.querySelector("[data-status]");
  const barEl = node.querySelector("[data-progress-bar]");
  const downloadEl = node.querySelector("[data-download]");

  nameEl.textContent = job.filename;
  statusEl.className = "job-status";

  if (job.status === "error") {
    statusEl.textContent = t("errorPrefix", { error: job.error || t("errorUnknown") });
    statusEl.classList.add("error");
    barEl.style.width = "0%";
  } else if (job.status === "done") {
    statusEl.textContent = t(STATUS_KEYS.done);
    statusEl.classList.add("done");
    barEl.style.width = "100%";
    downloadEl.hidden = false;
    downloadEl.href = `/api/jobs/${job.id}/download`;
    downloadEl.textContent = t("jobDownload");
    downloadAllBtn.hidden = false;
  } else {
    const total = job.pages_total || 0;
    const done = job.pages_done || 0;
    const stageLabel = STAGE_KEYS[job.stage] ? t(STAGE_KEYS[job.stage]) : t(STATUS_KEYS[job.status] || "statusQueued");
    const unit = t(STAGE_UNIT_KEYS[job.stage] || "unitPaginas");
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
    dependencyCommand.textContent = hint.command || "";
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
    dependencyFeedback.textContent = t("commandCopied");
    dependencyFeedback.classList.remove("error");
  } catch {
    dependencyFeedback.textContent = t("copyFailed");
    dependencyFeedback.classList.add("error");
  }
});

recheckBtn.addEventListener("click", checkDependencies);

autoInstallBtn.addEventListener("click", async () => {
  autoInstallBtn.disabled = true;
  dependencyFeedback.textContent = t("installing");
  dependencyFeedback.classList.remove("error");
  try {
    const response = await fetch("/api/system-check/install", { method: "POST" });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || t("installFailed"));

    dependencyFeedback.textContent = t("installSuccess");
    await checkDependencies();
  } catch (error) {
    dependencyFeedback.textContent = error.message;
    dependencyFeedback.classList.add("error");
  } finally {
    autoInstallBtn.disabled = false;
  }
});

applyTranslations();
populateUiLangSelect();
updateOptionsVisibility();
loadContentLanguages();
loadSettings();
loadExistingJobs();
checkDependencies();
