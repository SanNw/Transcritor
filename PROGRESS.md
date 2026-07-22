# Progresso do Transcritor

Este arquivo existe para dar contexto rápido a qualquer sessão do Claude
(ou de outra pessoa) que continue este projeto — o que já foi feito, o que
falta, e decisões importantes tomadas pelo caminho. Atualize-o conforme o
projeto evolui.

## O que o app faz hoje

App desktop **nativo em Qt/PySide6** (não é mais HTML/CSS/JS — essa foi uma
reescrita completa, ver seção abaixo) que converte livros, revistas, PDFs e
EPUBs (digitais ou escaneados/fotografados) em `.docx`, com:

- Extração de texto nativo de PDF/EPUB, com OCR automático (página a
  página) para o que estiver escaneado.
- Dois motores de OCR à escolha do usuário: Tesseract local (grátis) ou IA
  (Claude, OpenAI, Gemini — usuário cola a própria chave de API).
- Pós-processamento opcional por IA: correção gramatical + formatação como
  livro, ou instrução livre (resumir, traduzir, listar personagens etc.),
  com divisão em blocos + síntese final para documentos longos.
- Interface em 4 cards (Arquivo / Configuração da transcrição /
  Inteligência Artificial / Execução), inspirada em Qt Creator/Obsidian/VS
  Code/JetBrains — sem HTML por baixo, widgets Qt nativos de verdade.
- Checagem automática de dependências (Tesseract) na primeira execução, com
  diálogo nativo mostrando o comando de instalação certo para o SO.
- Um modo servidor/web opcional ainda existe (`main.py` via `uvicorn`), para
  quem quiser rodar como serviço local/automação — mas não é mais o modo de
  distribuição principal.

Detalhes de instalação e arquitetura estão no `README.md`.

## ✅ Reescrita da interface: HTML/CSS/JS → Qt/PySide6 nativo (concluída)

O usuário pediu inicialmente melhorias visuais no frontend web (mandou uma
imagem de referência gerada por IA, estilo "web app bonito"). Depois mudou
de ideia: quer um app desktop **nativo de verdade**, sem HTML por baixo,
inspirado em Qt Creator/Obsidian/VS Code/JetBrains, com layout de 4 cards.
Foi avisado que `desktop_app.py` (pywebview, já removido) entregava "janela
própria sem navegador" sem precisar reescrever nada, mas preferiu a
reescrita nativa mesmo assim — decisão consciente, não mal-entendido.

**O que mudou:**
- Novo pacote `backend/qt_app/` (`theme.py`, `icons.py`, `widgets.py`,
  `worker.py`, `main_window.py`, `settings_dialog.py`,
  `dependency_dialog.py`) + `backend/qt_main.py` como entry point. App
  desktop nativo completo, testado de ponta a ponta (renderização real via
  `QT_QPA_PLATFORM=offscreen`, screenshots conferidos em 1366×768, 1600×900,
  4K e tamanho mínimo — sem GUI real neste sandbox, mas o Qt renderiza de
  verdade em offscreen, não é só "importa sem erro").
- `frontend/` (HTML/CSS/JS) continua existindo só para o modo servidor/web
  opcional (`main.py`/`uvicorn`) — não é mais o modo de distribuição
  principal, mas não foi apagado (ainda é útil e funcional).
- `desktop_app.py` (pywebview) foi **removido** — totalmente substituído
  pelo `qt_main.py`.
- `requirements-desktop.txt` trocou `pywebview` por `PySide6`.
- Empacotamento (`.deb`/AppImage/`.exe`) atualizado para compilar
  `qt_main.py` em vez de `web_launcher.py` — ver próxima seção.
- `install.sh`: por padrão agora instala e configura o app desktop Qt
  (antes, o padrão era o modo web). `transcritor` abre a janela Qt;
  `transcritor --web` abre o modo servidor/navegador (opt-in).

**Backend de lógica de negócio não mudou**: `ocr.py`, `ai_providers.py`,
`docx_builder.py`, `settings_store.py`, `system_check.py`, `paths.py`
seguem exatamente iguais — o worker Qt (`qt_app/worker.py`) só chama essas
mesmas funções a partir de uma `QThread`, em vez de via HTTP.

**Diferença de comportamento importante**: o modo web tinha fila de jobs
(vários arquivos em paralelo) + download em `.zip`. O app Qt processa **um
arquivo por vez** (mais simples, casa com o layout de 4 cards do mockup de
referência) — se quiser processar vários arquivos em lote, o modo
servidor/web (`transcritor --web`) ainda oferece isso.

## Estado do empacotamento (importante!)

- **`.deb`**: `packaging/build-deb.sh` — testado de ponta a ponta neste
  ambiente **com o binário Qt** (build → `apt install` → `transcritor`
  roda via PATH → `apt remove`). Funciona. `Depends` inclui
  `tesseract-ocr, tesseract-ocr-por, libxkbcommon0, libgl1` (libs X11/xcb
  extras como `libxcb-icccm4` já ficam embutidas no binário pelo
  PyInstaller, não precisam de Depends).
- **AppImage**: `packaging/build-appimage.sh` — a AppDir é montada e
  validada com o binário Qt (o `AppRun` sobe o app corretamente em
  offscreen), mas o passo final (rodar `appimagetool` para gerar o
  `.AppImage`) **não foi testado** porque este ambiente de desenvolvimento
  não tem acesso ao GitHub Releases para baixar o `appimagetool`. Rode o
  script numa máquina com internet normal, ou baixe o
  `appimagetool-x86_64.AppImage` manualmente e aponte
  `APPIMAGETOOL=/caminho/para/ele`.
- **Windows `.exe`**: `packaging/windows/transcritor.iss` +
  `packaging/windows/build-windows.ps1` — atualizado para compilar
  `qt_main.py` com `--windowed` (sem console) e instalar
  `requirements-desktop.txt`. Segue a sintaxe padrão do Inno Setup, mas
  **nunca compilado nem testado**, porque este é um ambiente Linux sem
  Windows/Inno Setup disponível. Precisa ser compilado numa máquina Windows
  (ou CI com runner Windows) com Python 3.10+ e o Inno Setup instalados.

### Prompt sugerido para compilar o `.exe` (rodar com Claude numa máquina Windows)

```
Estou no repositório do Transcritor. Preciso compilar o instalador Windows.
O app agora é um app Qt/PySide6 nativo (entry point: backend/qt_main.py,
não é mais um app web). Rode packaging\windows\build-windows.ps1 a partir
da raiz do repositório (instale Python 3.10+ e o Inno Setup se não
estiverem presentes — Inno Setup em https://jrsoftware.org/isinfo.php). Se
der erro, investigue e corrija packaging/windows/transcritor.iss ou
build-windows.ps1 conforme necessário — foram escritos/atualizados sem
poder ser testados em Windows. Depois de gerar o .exe em dist-packages/,
teste rodando o instalador de verdade e confirmando que a janela do
Transcritor abre (não deve abrir navegador nenhum).
```

## Pendências conhecidas / próximos passos

Combinados com o usuário, ainda não iniciados (foram pausados para dar
lugar à reescrita Qt, que o usuário pediu para resolver primeiro):

1. **Servidor MCP** — expor a transcrição como ferramenta MCP, para Claude
   Desktop/Claude Code chamarem "transcreva este PDF" diretamente.
2. **Transcrição de áudio** (MP3/WAV/FLAC/M4A/MP4/MKV) — reaproveitando a
   camada `ai_providers.py` já existente (Whisper/OpenAI, Claude, Gemini
   todos suportam áudio). Vai precisar de um novo botão/estado no card
   "Arquivo" do app Qt (ou reaproveitar o mesmo, já que a extensão do
   arquivo já determina o fluxo).

Roadmap maior discutido com o usuário (lista de features vinda de uma
sessão de brainstorm com ChatGPT, avaliada e priorizada por esforço/valor —
ver histórico da conversa para a lista completa categorizada). Bucket
resumido, do mais barato ao mais caro:

- **Vitórias rápidas**: exportar também para TXT/Markdown/HTML, mais ações
  de IA prontas (explicar, simplificar, linguagem acadêmica/jurídica,
  palavras-chave, linha do tempo, perguntas e respostas), estatísticas do
  documento, preservar negrito/itálico na extração de PDF nativo.
- **Esforço médio**: transcrição de áudio (ver item 2 acima), OCR de
  tabelas via IA multimodal, "biblioteca" com metadados (SQLite local),
  comparação entre dois documentos.
- **Esforço alto** (mudança de arquitetura): busca semântica / chat com
  documentos (RAG com embeddings), editor rico com versionamento, leitor
  integrado, geração de audiolivro (TTS), automação por pasta monitorada,
  reconstrução de scans antigos.

## Decisões técnicas que valem lembrar

- **Qt em vez de pywebview**: ver seção "Reescrita da interface" acima.
  `desktop_app.py` foi removido — não recriar sem necessidade real.
- **`qt_main.py` vs pacote `qt_app/`**: não podem ter o mesmo nome no mesmo
  diretório (`qt_app.py` colidiria com o pacote `qt_app/`). Por isso o
  entry point se chama `qt_main.py`.
- **Ícones no app Qt**: `qt_app/icons.py` renderiza os mesmos SVGs do modo
  web (`QSvgRenderer` + `QPixmap`) para manter a identidade visual — não
  duplicar os paths, editar só ali se precisar mudar um ícone.
- **Responsividade do app Qt**: o conteúdo tem `max-width: 1400px` e fica
  centralizado (`qt_app/main_window.py`, `_build_...` do corpo) — sem isso,
  os cards esticavam feio em telas 4K. Também importante:
  `left_col.addStretch(1)` / `right_col.addStretch(1)` depois dos cards,
  senão o Qt distribui o espaço sobrando esticando os cards em vez de
  deixá-los no tamanho natural.
- **Card "Inteligência Artificial" sempre visível**: o seletor de provedor
  e o status da chave ficam sempre visíveis no card (não escondidos
  condicionalmente), mesmo que o motor seja Tesseract — só a validação de
  "precisa de chave configurada" acontece condicionalmente ao iniciar.
  Escondê-los deixava o card vazio/quebrado visualmente.
- **PyInstaller + PySide6 no Linux**: precisa de `libxcb-icccm4`,
  `libxcb-keysyms1`, `libxcb-shape0`, `libtiff6` instalados na máquina que
  *compila* o binário (senão dá warning e o Qt pode falhar em abrir no XCB
  em algumas máquinas) — o PyInstaller embute essas libs no binário final
  se estiverem presentes no build. `libegl1` e `libgl1-mesa-dri` também
  precisam estar instalados para o Qt (mesmo offscreen) funcionar.
- **Chaves de API**: ficam em texto puro em `~/.transcritor/config.json`
  (pacotes/produção) ou `backend/data/config.json` (dev). Nunca voltam
  completas pela API/UI (mascaradas, só os 4 últimos caracteres).
- **Ordem de rotas no FastAPI** (modo servidor/web):
  `/api/jobs/download-all` precisa estar declarada *antes* de
  `/api/jobs/{job_id}` em `main.py`, senão o FastAPI interpreta
  "download-all" como um `job_id` e retorna 404. Já corrigido.
- **Bug de CSS já corrigido** (modo servidor/web, `frontend/style.css`):
  `[hidden]` tem prioridade baixa por padrão; qualquer classe com
  `display:` explícito (como `.overlay` ou `.options-row`) sobrescrevia
  isso. Corrigido com uma regra global `[hidden] { display: none
  !important; }` — importante não remover essa regra se mexer no CSS do
  modo web.
- **Ambiente de desenvolvimento (sandbox Linux)**: sem acesso à internet
  irrestrito — só a repos GitHub explicitamente autorizados e a PyPI (via
  proxy). Downloads diretos do GitHub Releases (ex.: `appimagetool`) são
  bloqueados. Isso não deve afetar o usuário final rodando os scripts na
  própria máquina. Testes visuais do app Qt foram feitos via
  `QT_QPA_PLATFORM=offscreen` + `widget.grab().save(...)` (renderização
  real, não simulada).

## Como testar rapidamente depois de mudanças

```bash
cd backend
pip install -r requirements-desktop.txt -r requirements-ai.txt   # ai opcional
python qt_main.py
# escolher um arquivo, testar engine/pós-processamento, iniciar transcrição
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

Para regenerar os pacotes: ver seção "Gerar os pacotes" no `README.md`.
