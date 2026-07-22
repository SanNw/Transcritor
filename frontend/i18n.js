/* Idioma da INTERFACE do app (botões, rótulos, mensagens) — não confundir
 * com o idioma do CONTEÚDO (documento/áudio sendo transcrito), que é outro
 * seletor, alimentado por /api/languages e sempre com detecção automática
 * disponível.
 *
 * Detecta o idioma do navegador (navigator.language) na primeira visita,
 * com override manual persistido em localStorage. Adicionar um novo idioma
 * de interface = acrescentar uma entrada em TRANSLATIONS e em UI_LANGUAGES.
 */

const UI_LANGUAGES = [
  { code: "pt-BR", label: "Português" },
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
];

const TRANSLATIONS = {
  "pt-BR": {
    appSubtitle: "Livros, revistas, PDFs e EPUBs transformados em manuscritos .docx",
    settingsButton: "Configurações de IA",
    dependencyTitle: "Tesseract OCR não encontrado",
    dependencyBody:
      "O motor de OCR local não está instalado nesta máquina. Você ainda pode usar o motor de IA (se tiver uma chave configurada), mas o Tesseract é necessário para o OCR local gratuito.",
    copyButton: "Copiar",
    dependencyLink: "Ver documentação",
    autoInstallButton: "Instalar automaticamente",
    recheckButton: "Já instalei, verificar de novo",
    dropzoneTitle: "Arraste um arquivo aqui ou clique para escolher",
    dropzoneHint1: "PDF, EPUB, PNG, JPG, TIFF, BMP, WEBP, MP3, WAV, FLAC, M4A, MP4 ou MKV · até 200 MB",
    dropzoneHint2:
      "Áudio/vídeo: escolha Whisper local (grátis, offline) ou IA em nuvem (OpenAI/Google — a Anthropic Claude ainda não transcreve áudio)",
    langLabel: "Idioma do conteúdo",
    langAuto: "Detectar automaticamente",
    langLimitedSuffix: " (suporte limitado no OCR local)",
    langLimitedWarning: "Este idioma tem suporte limitado no OCR local (Tesseract) — para melhor precisão, considere o motor de IA.",
    engineLabel: "Motor de transcrição",
    engineTesseract: "Tesseract (local, grátis — documentos/imagens)",
    engineAi: "Inteligência artificial (nuvem)",
    engineWhisper: "Whisper local (grátis — só áudio/vídeo)",
    postprocessLabel: "Pós-processamento",
    postprocessNone: "Nenhum",
    postprocessGrammar: "Corrigir e formatar como livro",
    postprocessCustom: "Instrução personalizada",
    providerLabel: "Provedor de IA",
    customInstructionPlaceholder:
      "Ex.: resuma esta obra em até 2 páginas · traduza para o inglês · liste os personagens principais",
    downloadAllButton: "Baixar tudo (.zip)",
    settingsTitle: "Configurações de IA",
    settingsNote:
      "As chaves ficam salvas apenas nesta máquina, em texto puro, e são usadas para chamar a API do provedor escolhido diretamente. Nunca são enviadas a nenhum outro serviço.",
    notConfigured: "Não configurado",
    apiKeyPlaceholderAnthropic: "Chave de API (sk-ant-...)",
    apiKeyPlaceholderOpenAI: "Chave de API (sk-...)",
    apiKeyPlaceholderGoogle: "Chave de API (AIza...)",
    closeButton: "Fechar",
    saveKeysButton: "Salvar chaves",
    jobDownload: "Baixar .docx",
    uiLangLabel: "Idioma da interface",

    statusQueued: "Na fila…",
    statusProcessing: "Transcrevendo…",
    statusDone: "Concluído",
    statusError: "Erro",
    stageExtraindo: "Transcrevendo",
    stageTranscrevendoAudio: "Transcrevendo áudio",
    stageAplicandoIa: "Aplicando IA",
    unitPaginas: "páginas",
    unitArquivos: "arquivos",
    unitBlocos: "blocos",

    providerHintMissing: "Configure a chave deste provedor em Configurações de IA.",
    providerHintConfigured: "Configurado ({key}) · modelo {model}",
    configureProviderFirst: "Configure a chave do provedor selecionado antes de transcrever.",
    errorPrefix: "Erro: {error}",
    errorUnknown: "falha desconhecida",
    uploadFailed: "Falha no envio ({status})",
    noNewKeys: "Nenhuma chave nova para salvar.",
    keysSaved: "Chaves salvas com sucesso.",
    keysSaveFailed: "Falha ao salvar as chaves.",
    commandCopied: "Comando copiado.",
    copyFailed: "Não foi possível copiar automaticamente — selecione o texto manualmente.",
    installing: "Instalando… isso pode levar alguns minutos.",
    installSuccess: "Instalado com sucesso!",
    installFailed: "Falha na instalação automática.",
  },

  en: {
    appSubtitle: "Books, magazines, PDFs and EPUBs turned into .docx manuscripts",
    settingsButton: "AI Settings",
    dependencyTitle: "Tesseract OCR not found",
    dependencyBody:
      "The local OCR engine isn't installed on this machine. You can still use the AI engine (if you have a key configured), but Tesseract is needed for free local OCR.",
    copyButton: "Copy",
    dependencyLink: "View documentation",
    autoInstallButton: "Install automatically",
    recheckButton: "Already installed, check again",
    dropzoneTitle: "Drag a file here or click to choose",
    dropzoneHint1: "PDF, EPUB, PNG, JPG, TIFF, BMP, WEBP, MP3, WAV, FLAC, M4A, MP4 or MKV · up to 200 MB",
    dropzoneHint2:
      "Audio/video: choose local Whisper (free, offline) or cloud AI (OpenAI/Google — Anthropic Claude doesn't transcribe audio yet)",
    langLabel: "Content language",
    langAuto: "Auto-detect",
    langLimitedSuffix: " (limited local OCR support)",
    langLimitedWarning: "This language has limited local (Tesseract) OCR support — for better accuracy, consider the AI engine.",
    engineLabel: "Transcription engine",
    engineTesseract: "Tesseract (local, free — documents/images)",
    engineAi: "Artificial intelligence (cloud)",
    engineWhisper: "Local Whisper (free — audio/video only)",
    postprocessLabel: "Post-processing",
    postprocessNone: "None",
    postprocessGrammar: "Correct and format as a book",
    postprocessCustom: "Custom instruction",
    providerLabel: "AI provider",
    customInstructionPlaceholder:
      "E.g.: summarize this work in up to 2 pages · translate to English · list the main characters",
    downloadAllButton: "Download all (.zip)",
    settingsTitle: "AI Settings",
    settingsNote:
      "Keys are stored only on this machine, in plain text, and used to call the chosen provider's API directly. They're never sent to any other service.",
    notConfigured: "Not configured",
    apiKeyPlaceholderAnthropic: "API key (sk-ant-...)",
    apiKeyPlaceholderOpenAI: "API key (sk-...)",
    apiKeyPlaceholderGoogle: "API key (AIza...)",
    closeButton: "Close",
    saveKeysButton: "Save keys",
    jobDownload: "Download .docx",
    uiLangLabel: "Interface language",

    statusQueued: "Queued…",
    statusProcessing: "Transcribing…",
    statusDone: "Done",
    statusError: "Error",
    stageExtraindo: "Transcribing",
    stageTranscrevendoAudio: "Transcribing audio",
    stageAplicandoIa: "Applying AI",
    unitPaginas: "pages",
    unitArquivos: "files",
    unitBlocos: "chunks",

    providerHintMissing: "Configure this provider's key in AI Settings.",
    providerHintConfigured: "Configured ({key}) · model {model}",
    configureProviderFirst: "Configure the selected provider's key before transcribing.",
    errorPrefix: "Error: {error}",
    errorUnknown: "unknown failure",
    uploadFailed: "Upload failed ({status})",
    noNewKeys: "No new keys to save.",
    keysSaved: "Keys saved successfully.",
    keysSaveFailed: "Failed to save keys.",
    commandCopied: "Command copied.",
    copyFailed: "Couldn't copy automatically — select the text manually.",
    installing: "Installing… this may take a few minutes.",
    installSuccess: "Installed successfully!",
    installFailed: "Automatic installation failed.",
  },

  es: {
    appSubtitle: "Libros, revistas, PDFs y EPUBs convertidos en manuscritos .docx",
    settingsButton: "Configuración de IA",
    dependencyTitle: "Tesseract OCR no encontrado",
    dependencyBody:
      "El motor de OCR local no está instalado en esta máquina. Aún puedes usar el motor de IA (si tienes una clave configurada), pero Tesseract es necesario para el OCR local gratuito.",
    copyButton: "Copiar",
    dependencyLink: "Ver documentación",
    autoInstallButton: "Instalar automáticamente",
    recheckButton: "Ya lo instalé, verificar de nuevo",
    dropzoneTitle: "Arrastra un archivo aquí o haz clic para elegir",
    dropzoneHint1: "PDF, EPUB, PNG, JPG, TIFF, BMP, WEBP, MP3, WAV, FLAC, M4A, MP4 o MKV · hasta 200 MB",
    dropzoneHint2:
      "Audio/video: elige Whisper local (gratis, sin conexión) o IA en la nube (OpenAI/Google — Anthropic Claude aún no transcribe audio)",
    langLabel: "Idioma del contenido",
    langAuto: "Detectar automáticamente",
    langLimitedSuffix: " (soporte limitado en OCR local)",
    langLimitedWarning: "Este idioma tiene soporte limitado en el OCR local (Tesseract) — para mejor precisión, considera el motor de IA.",
    engineLabel: "Motor de transcripción",
    engineTesseract: "Tesseract (local, gratis — documentos/imágenes)",
    engineAi: "Inteligencia artificial (nube)",
    engineWhisper: "Whisper local (gratis — solo audio/video)",
    postprocessLabel: "Post-procesamiento",
    postprocessNone: "Ninguno",
    postprocessGrammar: "Corregir y formatear como libro",
    postprocessCustom: "Instrucción personalizada",
    providerLabel: "Proveedor de IA",
    customInstructionPlaceholder:
      "Ej.: resume esta obra en hasta 2 páginas · traduce al inglés · lista los personajes principales",
    downloadAllButton: "Descargar todo (.zip)",
    settingsTitle: "Configuración de IA",
    settingsNote:
      "Las claves se guardan solo en esta máquina, en texto plano, y se usan para llamar directamente a la API del proveedor elegido. Nunca se envían a ningún otro servicio.",
    notConfigured: "No configurado",
    apiKeyPlaceholderAnthropic: "Clave de API (sk-ant-...)",
    apiKeyPlaceholderOpenAI: "Clave de API (sk-...)",
    apiKeyPlaceholderGoogle: "Clave de API (AIza...)",
    closeButton: "Cerrar",
    saveKeysButton: "Guardar claves",
    jobDownload: "Descargar .docx",
    uiLangLabel: "Idioma de la interfaz",

    statusQueued: "En cola…",
    statusProcessing: "Transcribiendo…",
    statusDone: "Completado",
    statusError: "Error",
    stageExtraindo: "Transcribiendo",
    stageTranscrevendoAudio: "Transcribiendo audio",
    stageAplicandoIa: "Aplicando IA",
    unitPaginas: "páginas",
    unitArquivos: "archivos",
    unitBlocos: "bloques",

    providerHintMissing: "Configura la clave de este proveedor en Configuración de IA.",
    providerHintConfigured: "Configurado ({key}) · modelo {model}",
    configureProviderFirst: "Configura la clave del proveedor seleccionado antes de transcribir.",
    errorPrefix: "Error: {error}",
    errorUnknown: "falla desconocida",
    uploadFailed: "Fallo al enviar ({status})",
    noNewKeys: "No hay claves nuevas para guardar.",
    keysSaved: "Claves guardadas con éxito.",
    keysSaveFailed: "Error al guardar las claves.",
    commandCopied: "Comando copiado.",
    copyFailed: "No se pudo copiar automáticamente — selecciona el texto manualmente.",
    installing: "Instalando… esto puede tardar unos minutos.",
    installSuccess: "¡Instalado con éxito!",
    installFailed: "Falló la instalación automática.",
  },
};

const STORAGE_KEY = "transcritor.uiLang";

function detectDefaultLanguage() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && TRANSLATIONS[stored]) return stored;

  const candidates = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language];
  for (const candidate of candidates) {
    if (!candidate) continue;
    if (TRANSLATIONS[candidate]) return candidate;
    const primary = candidate.split("-")[0];
    const match = UI_LANGUAGES.find((l) => l.code === primary || l.code.split("-")[0] === primary);
    if (match) return match.code;
  }
  return "pt-BR";
}

let currentLang = detectDefaultLanguage();

function t(key, params) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS["pt-BR"];
  let text = dict[key] ?? TRANSLATIONS["pt-BR"][key] ?? key;
  if (params) {
    for (const [name, value] of Object.entries(params)) {
      text = text.replace(`{${name}}`, value);
    }
  }
  return text;
}

function setUiLanguage(code) {
  if (!TRANSLATIONS[code]) return;
  currentLang = code;
  localStorage.setItem(STORAGE_KEY, code);
  applyTranslations();
}

function getUiLanguage() {
  return currentLang;
}

function applyTranslations() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.dispatchEvent(new CustomEvent("i18n:applied"));
}
