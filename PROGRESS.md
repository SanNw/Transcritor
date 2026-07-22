# Progresso do Transcritor

Este arquivo existe para dar contexto rápido a qualquer sessão do Claude
(ou de outra pessoa) que continue este projeto — o que já foi feito, o que
falta, e decisões importantes tomadas pelo caminho. Atualize-o conforme o
projeto evolui.

> **Nota sobre este merge**: duas sessões trabalharam em paralelo por um
> tempo — uma reescrevendo a interface em Qt/PySide6 (app desktop nativo),
> outra terminando o empacotamento antigo (web) e adicionando áudio/vídeo +
> servidor MCP + idiomas. Este arquivo é o resultado das duas frentes
> integradas: o app agora é Qt nativo (`qt_main.py`), mas o modo
> servidor/web (`main.py`) continua existindo e é hoje o único lugar com
> áudio, detecção automática de idioma e a lista completa de idiomas — ver
> "Pendências" abaixo para o que falta portar pro Qt.

## O que o app faz hoje

App desktop **nativo em Qt/PySide6** (interface principal) que converte
livros, revistas, PDFs, EPUBs e — no modo servidor/web e via MCP — também
áudio/vídeo, em `.docx`:

- Extração de texto nativo de PDF/EPUB, com OCR automático (página a
  página) para o que estiver escaneado.
- Dois motores de OCR à escolha do usuário: Tesseract local (grátis) ou IA
  (Claude, OpenAI, Gemini — usuário cola a própria chave de API).
- Transcrição de áudio/vídeo (MP3/WAV/FLAC/M4A/MP4/MKV): Whisper local
  (grátis, offline, instalação opcional) ou IA em nuvem (OpenAI/Google — a
  Anthropic Claude não suporta áudio nesta API). Ver `audio_transcriber.py`
  — disponível no modo servidor/web e via MCP; **ainda não está na
  interface Qt**.
- Pós-processamento opcional por IA: correção gramatical + formatação como
  livro, ou instrução livre (resumir, traduzir, listar personagens etc.),
  com divisão em blocos + síntese final para documentos longos.
- Idioma do conteúdo: mais de 20 idiomas (`backend/languages.py`) com
  detecção automática, no modo servidor/web e MCP. O app Qt hoje só tem
  Português/Inglês/Português+Inglês, sem detecção automática.
- Idioma da interface do modo web: Português, English, Español (detecção
  automática do navegador). O app Qt está só em português por enquanto.
- Interface Qt em 4 cards (Arquivo / Configuração da transcrição /
  Inteligência Artificial / Execução), inspirada em Qt Creator/Obsidian/VS
  Code/JetBrains — widgets nativos, sem HTML por baixo.
- Checagem automática de dependências (Tesseract) na primeira execução —
  diálogo nativo no Qt, banner com instalação automática (Windows via
  `winget`, macOS via `brew`) no modo web.
- A transcrição pode ser chamada diretamente do Claude Desktop/Claude Code
  como ferramenta MCP (`mcp_server.py`, tool `transcrever`), sem abrir
  nenhuma interface.

Detalhes de instalação e arquitetura estão no `README.md`.

## ✅ Reescrita da interface: HTML/CSS/JS → Qt/PySide6 nativo (concluída)

O usuário pediu inicialmente melhorias visuais no frontend web, depois
mudou de ideia: quer um app desktop **nativo de verdade**, sem HTML por
baixo, inspirado em Qt Creator/Obsidian/VS Code/JetBrains, com layout de 4
cards. Foi avisado que `desktop_app.py` (pywebview, já removido) entregava
"janela própria sem navegador" sem precisar reescrever nada, mas preferiu a
reescrita nativa mesmo assim — decisão consciente, não mal-entendido.

**O que mudou:**
- Novo pacote `backend/qt_app/` (`theme.py`, `icons.py`, `widgets.py`,
  `worker.py`, `main_window.py`, `settings_dialog.py`,
  `dependency_dialog.py`) + `backend/qt_main.py` como entry point. Testado
  de ponta a ponta com renderização real via `QT_QPA_PLATFORM=offscreen`
  (screenshots em 1366×768, 1600×900, 4K e tamanho mínimo) e uma transcrição
  real ponta a ponta (worker QThread → `.docx` gerado).
- `frontend/` (HTML/CSS/JS) continua existindo para o modo servidor/web
  opcional — não é mais o modo de distribuição principal, mas segue
  funcional e é hoje o único lugar com áudio/idiomas completos/i18n.
- `desktop_app.py` (pywebview) foi **removido** — substituído pelo
  `qt_main.py`. Motivo: pywebview no Linux depende de GTK+WebKit do
  sistema, com nomes de pacote que variam entre versões de distro — muito
  frágil para um pacote genérico. Qt bundlado via PyInstaller não tem esse
  problema (só precisa de libs X11/xcb base, presentes em qualquer desktop
  Linux).
- `requirements-desktop.txt` trocou `pywebview` por `PySide6`.
- Empacotamento (`.deb`/AppImage/`.exe`) atualizado para compilar
  `qt_main.py` em vez de `web_launcher.py` — ver "Estado do empacotamento".
- `install.sh`: por padrão agora instala e configura o app desktop Qt.
  `transcritor` abre a janela Qt; `transcritor --web` abre o modo
  servidor/navegador (com áudio/idiomas completos), opt-in.

**Backend de lógica de negócio não mudou de propósito**: `ocr.py`,
`ai_providers.py`, `docx_builder.py`, `settings_store.py`,
`system_check.py`, `paths.py`, `languages.py`, `audio_transcriber.py`
seguem sendo a camada compartilhada — o worker Qt (`qt_app/worker.py`) só
chama essas funções a partir de uma `QThread`, em vez de via HTTP. Esses
módulos ganharam suporte a áudio/idiomas (trabalho da outra sessão) sem
quebrar o Qt: `extract_pages(lang=...)` continua aceitando os mesmos
códigos ("por", "eng", "por+eng") que o Qt já usava.

**Diferença de comportamento**: o modo web tem fila de jobs (vários
arquivos em paralelo) + download em `.zip` + áudio + idiomas completos. O
app Qt processa **um arquivo por vez**, só documentos, só
por/eng/por+eng — mais simples, casa com o layout de 4 cards do mockup de
referência.

## Estado do empacotamento (importante!)

- **`.deb`**: `packaging/build-deb.sh` — testado de ponta a ponta **com o
  binário Qt** (build → `apt install` → `transcritor` roda via PATH →
  `apt remove`). Funciona. `Depends` inclui
  `tesseract-ocr, tesseract-ocr-por, libxkbcommon0, libgl1` (libs X11/xcb
  extras como `libxcb-icccm4` ficam embutidas no binário pelo PyInstaller).
- **AppImage**: `packaging/build-appimage.sh` — a AppDir e o `AppRun` foram
  testados **com o binário Qt** (sobe o app corretamente em offscreen). O
  passo final (`appimagetool` gerando o `.AppImage`) foi testado **antes da
  reescrita Qt** (com o binário web antigo) numa sessão Windows + Docker
  (`ubuntu:22.04`); precisa ser **re-testado com o binário Qt** — o script
  em si não mudou de comportamento, só o binário que ele empacota. Dica de
  quem já fez isso: em container sem FUSE, rode `appimagetool` (e o
  `.AppImage` gerado) com `--appimage-extract-and-run`.
- **Windows `.exe`**: `packaging/windows/transcritor.iss` +
  `packaging/windows/build-windows.ps1` — atualizado para compilar
  `qt_main.py` com `--windowed` (sem console) e `requirements-desktop.txt`.
  A detecção do `ISCC.exe` foi corrigida numa sessão anterior (também busca
  no registro do Windows por `InstallLocation` de "Inno Setup*", não só em
  `Program Files (x86)`) e **essa correção foi preservada** no merge. O
  fluxo completo (build → instalar silenciosamente → abrir → desinstalar)
  foi testado numa sessão Windows real **antes da reescrita Qt** (com o
  binário web antigo) — precisa ser **re-testado com o binário Qt**.

### Prompt sugerido para re-testar o `.exe`/AppImage com o binário Qt (rodar numa máquina Windows/Linux com internet normal)

```
Estou no repositório do Transcritor. O app foi reescrito como um app
Qt/PySide6 nativo (entry point: backend/qt_main.py) — os scripts de
empacotamento (packaging/build-appimage.sh no Linux,
packaging/windows/build-windows.ps1 no Windows) já foram atualizados pra
compilar esse binário, mas o resultado final (.AppImage / .exe) não foi
re-testado depois dessa mudança de arquitetura (só o binário web antigo
tinha sido testado ponta a ponta). Rode o script correspondente ao seu SO,
gere o pacote, instale/rode de verdade e confirme que abre uma JANELA
NATIVA (não deve abrir navegador nenhum). Se algo quebrar, é provavelmente
relacionado ao binário Qt (bibliotecas gráficas faltando, etc.), não ao
script de empacotamento em si — investigue e corrija. Leia PROGRESS.md
inteiro antes de começar para mais contexto.
```

## Pendências conhecidas / próximos passos

**Concluído** (não são mais pendências): servidor MCP, transcrição de
áudio/vídeo, idiomas de conteúdo (20+, detecção automática), i18n da
interface web, instalação automática do Tesseract no Windows via `winget` —
tudo isso existe hoje no modo servidor/web e (áudio/MCP/idiomas) via MCP.

**Pendência nova, criada pela reescrita Qt**: portar pra interface Qt o que
só existe no modo web hoje —

1. Áudio/vídeo como opção de arquivo no card "Arquivo" do app Qt (motor
   `whisper`/`ai` em vez de `tesseract`/`ai`).
2. Lista completa de idiomas de conteúdo (`languages.py`) no lugar dos 3
   hardcoded em `qt_app/main_window.py` (`lang_combo`), com detecção
   automática.
3. Fila de múltiplos arquivos + download em lote (`.zip`) — hoje o Qt
   processa um arquivo por vez, sem fila. Avaliar se isso é desejado ou se
   "um por vez" é intencional para o app desktop (o mockup de referência do
   usuário sugeria um fluxo de arquivo único).
4. i18n da interface Qt (hoje só português) — se fizer sentido dado que
   `frontend/i18n.js` já tem a estrutura pt/en/es pronta como referência.

**Re-teste de empacotamento** (ver seção acima): AppImage e `.exe` com o
binário Qt.

Lacunas conhecidas e deixadas como estão (avaliadas, não bugs escondidos):

- Idioma da interface web tem só 3 opções (pt-BR/en/es); os *nomes* dos
  idiomas de CONTEÚDO no seletor só existem traduzidos pra
  português/inglês. Mensagens de `system_check.py` (dependência do
  Tesseract) ainda são só em português.
- Skills de terceiros que o usuário encontrou via `openskills install`
  (`alper-dev/build-for-good-ux-skill`, `fratilanico/apex-os-bad-boy`,
  `JeremyKalmus/parade`, `juspay/kolu`) foram auditadas com o
  `skill-security-auditor`: só `build-for-good-ux-skill` passou limpo. As
  outras três não são skills de verdade (sem `SKILL.md`, achados
  CRITICAL/HIGH). Nenhuma foi instalada.

Roadmap maior discutido com o usuário (lista de features vinda de uma
sessão de brainstorm com ChatGPT, avaliada e priorizada por esforço/valor —
ver histórico da conversa para a lista completa categorizada). Bucket
resumido, do mais barato ao mais caro:

- **Vitórias rápidas**: exportar também para TXT/Markdown/HTML, mais ações
  de IA prontas (explicar, simplificar, linguagem acadêmica/jurídica,
  palavras-chave, linha do tempo, perguntas e respostas), estatísticas do
  documento, preservar negrito/itálico na extração de PDF nativo.
- **Esforço médio**: OCR de tabelas via IA multimodal, "biblioteca" com
  metadados (SQLite local), comparação entre dois documentos.
- **Esforço alto** (mudança de arquitetura): busca semântica / chat com
  documentos (RAG com embeddings), editor rico com versionamento, leitor
  integrado, geração de audiolivro (TTS), automação por pasta monitorada,
  reconstrução de scans antigos.

## Decisões técnicas que valem lembrar

### Sobre a reescrita Qt

- **`qt_main.py` vs pacote `qt_app/`**: não podem ter o mesmo nome no mesmo
  diretório (`qt_app.py` colidiria com o pacote `qt_app/`). Por isso o
  entry point se chama `qt_main.py`.
- **Ícones no app Qt**: `qt_app/icons.py` renderiza os mesmos SVGs do modo
  web (`QSvgRenderer` + `QPixmap`) para manter a identidade visual.
- **Responsividade do app Qt**: o conteúdo tem `max-width: 1400px` e fica
  centralizado (`qt_app/main_window.py`) — sem isso, os cards esticavam
  feio em telas 4K. Também importante: `left_col.addStretch(1)` /
  `right_col.addStretch(1)` depois dos cards, senão o Qt distribui o
  espaço sobrando esticando os cards em vez de deixá-los no tamanho
  natural.
- **Card "Inteligência Artificial" sempre visível**: o seletor de provedor
  e o status da chave ficam sempre visíveis, mesmo com motor Tesseract —
  só a validação de "precisa de chave" acontece condicionalmente ao
  iniciar. Escondê-los deixava o card vazio/quebrado visualmente.
- **PyInstaller + PySide6 no Linux**: precisa de `libxcb-icccm4`,
  `libxcb-keysyms1`, `libxcb-shape0`, `libtiff6` instalados na máquina que
  *compila* o binário (senão dá warning e o Qt pode falhar em abrir em
  algumas máquinas) — o PyInstaller embute essas libs no binário final se
  presentes no build. `libegl1` e `libgl1-mesa-dri` também precisam estar
  instalados para o Qt (mesmo offscreen) funcionar.

### Sobre o backend compartilhado (áudio, idiomas, MCP — válido para Qt e web)

- **Áudio não usa `ocr.py`**: um áudio/vídeo não é "página por página" — o
  arquivo inteiro vira um texto único numa chamada só. Por isso é um módulo
  novo (`audio_transcriber.py`), não uma extensão de `extract_pages`. O
  resultado sempre passa por `build_docx_from_text`, nunca por
  `build_docx`.
- **Anthropic Claude não transcreve áudio**: a API da Anthropic não tem
  modalidade de áudio hoje. `AIProvider.supports_audio` (`ai_providers.py`)
  é `False` por padrão, `True` só em `OpenAIProvider`/`GoogleProvider`.
  Validado em `main.py` e `mcp_server.py`.
- **Whisper local**: `transcribe_audio_local` (`audio_transcriber.py`) usa
  `openai-whisper` (modelo `base` por padrão), testado de verdade —
  funciona offline, sem chave de API. Fica em `requirements-whisper.txt`
  separado (traz o PyTorch) — não embutido nos pacotes por padrão. Pesos
  do modelo baixam sozinhos em `~/.cache/whisper`. Exige `ffmpeg` no
  sistema.
- **MCP server reaproveita o mesmo `config.json`**: `mcp_server.py` importa
  `settings_store.py` igual `main.py` — chaves configuradas pela interface
  valem pro MCP também, sem configuração duplicada. Testado via protocolo
  MCP real (`mcp.client.stdio`), não só chamando a função Python direto.
- **Tesseract automático no Windows via `winget`, não download direto**: o
  domínio oficial da UB-Mannheim se mostrou instável a partir de sandbox;
  `winget install -e --id UB-Mannheim.TesseractOCR --silent
  --accept-package-agreements --accept-source-agreements` baixa do GitHub
  Releases deles e foi testado de ponta a ponta. Ver `_install_hint()` em
  `backend/system_check.py`.
- **PATH desatualizado após instalar (Windows)**: um processo já em
  execução não vê atualizações de PATH até reiniciar — limitação do SO.
  Contornado checando diretamente `C:\Program
  Files\Tesseract-OCR\tesseract.exe` quando o PATH não resolve
  (`find_tesseract()` em `system_check.py`).
- **Tessdata gerenciado pelo próprio app**: em vez de depender da pasta de
  instalação do Tesseract (não gravável sem admin), o Transcritor baixa
  `.traineddata` sob demanda de `tessdata_fast` no GitHub para
  `TESSDATA_DIR` (`paths.py`) e aponta o Tesseract pra lá via a variável de
  ambiente `TESSDATA_PREFIX` (não `--tessdata-dir` — `shlex.split` no
  Windows mantém aspas literais no path, quebrando o caminho).
- **`languages.py` como fonte única de idiomas de conteúdo**: ~24 idiomas,
  cada um com código Tesseract/Whisper/nome. `"auto"` é válido só para
  `engine="ai"`/`"whisper"` (detectam sozinhos) — inválido pro Tesseract,
  validado em `main.py`/`mcp_server.py` e auto-corrigido na UI web.
- **Prompts de IA reforçam "não traduza"**: sem essa instrução explícita, o
  LLM poderia "ajudar" traduzindo pro idioma da conversa. Testado de
  verdade: imagem em português com `lang=auto` via OpenAI saiu em
  português, mesmo com a conversa em português.
- **i18n da interface web é um sistema à parte de `languages.py`**: vive só
  em `frontend/i18n.js` (`TRANSLATIONS`/`t()`/`applyTranslations()`),
  detecção via `navigator.language`, sem nada no backend. Elementos com
  estado dinâmico escutam o evento customizado `i18n:applied` para
  se re-renderizar — não usam `data-i18n` estático porque esse atributo é
  sobrescrito pelas funções que renderizam o estado real.

### Gerais / infraestrutura

- **Chaves de API**: ficam em texto puro em `~/.transcritor/config.json`
  (pacotes/produção) ou `backend/data/config.json` (dev). Nunca voltam
  completas pela API/UI (mascaradas, só os 4 últimos caracteres).
- **Ordem de rotas no FastAPI** (modo servidor/web):
  `/api/jobs/download-all` precisa estar declarada *antes* de
  `/api/jobs/{job_id}` em `main.py`, senão o FastAPI interpreta
  "download-all" como um `job_id` e retorna 404.
- **Bug de CSS já corrigido** (modo servidor/web, `frontend/style.css`):
  `[hidden]` tem prioridade baixa por padrão; qualquer classe com
  `display:` explícito (como `.overlay` ou `.options-row`) sobrescrevia
  isso. Corrigido com `[hidden] { display: none !important; }` — não
  remover essa regra.
- **Bug de CRLF ao clonar em Windows**: com `core.autocrlf=true` (comum em
  Windows), o checkout converte `LF` → `CRLF` em `.sh`/`.desktop`/`VERSION`,
  quebrando os scripts de build e contaminando nomes de arquivo gerados
  (`\r` literal no nome do `.AppImage`). Corrigido com `.gitattributes` na
  raiz (`* text=auto eol=lf`, `*.ps1`/`*.bat` forçados para `eol=crlf`) —
  já commitado. Se aparecer de novo, `sed -i 's/\r$//' <arquivo>` resolve.
- **Ambiente de desenvolvimento (sandbox Linux, usado nesta sessão)**: sem
  acesso à internet irrestrito — só repos GitHub explicitamente
  autorizados e PyPI (via proxy). Downloads diretos do GitHub Releases
  (`appimagetool`) são bloqueados. Não deve afetar o usuário final rodando
  os scripts na própria máquina. Testes visuais do app Qt foram feitos via
  `QT_QPA_PLATFORM=offscreen` + `widget.grab().save(...)` (renderização
  real, não simulada).

## Como testar rapidamente depois de mudanças

**App Qt (principal):**

```bash
cd backend
pip install -r requirements-desktop.txt -r requirements-ai.txt   # ai opcional
python qt_main.py
```

Sem display disponível (CI/sandbox), renderize offscreen e tire screenshot:

```bash
export QT_QPA_PLATFORM=offscreen
python3 -c "
from PySide6.QtWidgets import QApplication
app = QApplication([])
from qt_app.main_window import MainWindow
from qt_app.theme import build_stylesheet
app.setStyleSheet(build_stylesheet())
win = MainWindow(); win.show(); app.processEvents()
win.grab().save('/tmp/preview.png')
"
```

**Modo servidor/web (áudio, idiomas, MCP):**

```bash
cd backend
pip install -r requirements.txt -r requirements-ai.txt   # ai opcional
uvicorn main:app --reload
# abrir http://localhost:8000, testar upload de PDF/EPUB/imagem/áudio
```

Whisper local: `pip install -r requirements-whisper.txt` (+ `ffmpeg` no
sistema), escolher motor "whisper" ao enviar um áudio.

Servidor MCP: `pip install -r requirements-mcp.txt` e rodar
`python mcp_server.py` (stdio) — ou registrar no Claude Desktop/Code, ver
seção "Servidor MCP" no `README.md`.

Idiomas: troque o seletor de interface (canto superior direito, modo web) e
confira se os textos mudam; no seletor "Idioma do conteúdo", escolha um
idioma de suporte limitado (chinês, árabe) com Tesseract selecionado e
confira o aviso; troque para "Detectar automaticamente" e confirme que o
motor muda sozinho pra IA.

Para regenerar os pacotes: ver seção "Gerar os pacotes" no `README.md`.
