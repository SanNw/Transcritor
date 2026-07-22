# Transcritor

App desktop nativo (Qt/PySide6, Windows + Linux) que converte livros,
revistas, PDFs, EPUBs e áudio/vídeo — digitais, escaneados/fotografados, ou
fala gravada — em arquivos **.docx**.

- PDFs e EPUBs com texto: o texto é extraído diretamente.
- PDFs escaneados ou imagens (foto de página, JPG/PNG/TIFF/BMP/WEBP): o texto
  é reconhecido via OCR local (Tesseract) ou via IA (Claude, OpenAI ou
  Google Gemini), à sua escolha.
- Áudio ou vídeo (MP3, WAV, FLAC, M4A, MP4, MKV): a fala é transcrita via
  Whisper local (grátis, offline, instalação opcional) ou via IA em nuvem
  (OpenAI Whisper API ou Google Gemini — a Anthropic Claude ainda não
  suporta áudio nesta API). Hoje disponível no **modo servidor/web** e via
  **MCP**; o app desktop Qt ainda não tem essa opção na interface — ver
  [Limitações conhecidas](#limitações-conhecidas).
- Opcionalmente, uma IA pode revisar o resultado: corrigir ortografia e
  gramática e reorganizar o texto em capítulos como um livro, ou seguir
  qualquer instrução livre — resumir a obra, traduzir, listar personagens
  etc.
- O app decide página por página se precisa de OCR ou não, então um PDF pode
  ter parte digital e parte escaneada sem configuração extra.
- Interface nativa (widgets Qt, não HTML) organizada em 4 cards: Arquivo,
  Configuração da transcrição, Inteligência Artificial e Execução.
- A transcrição pode ser chamada diretamente do Claude Desktop/Claude Code
  como ferramenta MCP, sem abrir nenhuma interface — ver
  [Servidor MCP](#servidor-mcp-claude-desktop--claude-code).

## Instalação

Se o Tesseract OCR não estiver instalado, o próprio Transcritor detecta isso
na primeira execução e mostra o comando certo para o seu sistema — não
precisa instalar antes. No Windows e no macOS, dá pra instalar com um clique
direto pela interface web (ver [Detecção automática do Tesseract](#detecção-automática-do-tesseract)).

### Opção 1 — pacote pronto (recomendado)

| Sistema | Arquivo | Como instalar |
|---|---|---|
| Debian/Ubuntu | `transcritor_<versão>_amd64.deb` | `sudo apt install ./transcritor_<versão>_amd64.deb` (o apt já resolve o Tesseract como dependência) |
| Qualquer distro Linux | `Transcritor-<versão>-x86_64.AppImage` | `chmod +x Transcritor-*.AppImage && ./Transcritor-*.AppImage` |
| Windows | `Transcritor-<versão>-setup.exe` | rode o instalador normalmente |

Esses pacotes abrem o Transcritor em uma **janela própria nativa** — sem
navegador, sem HTML por baixo. Veja `packaging/` para os scripts que geram
cada um — ver a seção [Gerar os pacotes](#gerar-os-pacotes-deb-appimage-exe)
abaixo.

### Opção 2 — script de instalação (Linux/macOS, a partir do código-fonte)

```bash
git clone <este repositório>
cd Transcritor
./install.sh          # instala o app desktop (Qt)
./install.sh --ai     # inclui os SDKs de IA (Claude/OpenAI/Gemini)
```

O script detecta o Python e o gerenciador de pacotes do sistema, confere se o
Tesseract está instalado (perguntando antes de instalar via `sudo`), cria um
ambiente virtual e instala um comando `transcritor` em `~/.local/bin`. Depois
é só rodar `transcritor` (janela própria) ou `transcritor --web` (modo
servidor/navegador, com áudio/vídeo e mais idiomas — ver abaixo).

### Opção 3 — manual (qualquer sistema, para desenvolvimento)

```bash
cd backend
pip install -r requirements-desktop.txt
python qt_main.py
```

Pré-requisito: Python 3.10+ e, opcionalmente, o
[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) já instalado
(`sudo apt-get install tesseract-ocr tesseract-ocr-por` no Ubuntu/Debian,
`brew install tesseract tesseract-lang` no macOS, ou o instalador oficial no
Windows — https://github.com/UB-Mannheim/tesseract/wiki).

## Uso (app desktop Qt)

1. Escolha o arquivo (arraste para o card **Arquivo** ou clique em
   **Escolher arquivo**).
2. Ajuste o idioma, o motor de OCR e o pós-processamento no card
   **Configuração da transcrição**.
3. Se for usar IA (motor ou pós-processamento), configure a chave em
   **Configurações de IA** (botão no canto superior direito) e escolha o
   provedor no card **Inteligência Artificial**.
4. Clique em **Iniciar transcrição** no card **Execução** e acompanhe o
   progresso. Ao concluir, o app oferece abrir a pasta com o `.docx` gerado.

## Modo servidor/web (áudio, mais idiomas, fila de jobs)

Além do app desktop, o backend também roda como servidor local com interface
web, usando o mesmo código de extração/IA — e é hoje o único modo com suporte
a **áudio/vídeo**, **detecção automática de idioma** e a lista completa de
**20+ idiomas** (o app Qt usa uma lista reduzida por enquanto):

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Abra **http://localhost:8000** no navegador. Esse modo mantém fila de jobs
(vários arquivos em paralelo), download em lote (`.zip`) e a mesma API
(`/api/transcribe`, `/api/settings`, `/api/system-check`, `/api/languages`).
Quem instalou via `install.sh`, roda com `transcritor --web`.

### Detecção automática do Tesseract

Quando o Tesseract não é encontrado, o botão "Instalar automaticamente" na
interface web tenta:

- **Windows**: `winget install -e --id UB-Mannheim.TesseractOCR --silent
  --accept-package-agreements --accept-source-agreements` — baixa direto do
  GitHub Releases da UB Mannheim (não do site deles, que pode ser instável).
  Requer o `winget` (App Installer), já vem por padrão na maioria das
  instalações do Windows 10/11.
- **macOS**: `brew install tesseract tesseract-lang` (requer o
  [Homebrew](https://brew.sh)).
- **Linux**: não é automático (mostra o comando `apt` certo) — instalação de
  pacote de sistema geralmente exige `sudo`, mais delicado de automatizar
  com segurança de dentro do app.

Se o `winget`/`brew` não estiverem disponíveis, ou em qualquer outro sistema,
a interface sempre mostra o link para o instalador oficial como alternativa
manual.

**Importante sobre PATH no Windows**: instaladores (winget ou o `.exe`
oficial) atualizam o PATH do sistema, mas um processo já em execução (como o
próprio Transcritor, se já estiver aberto) não enxerga essa mudança até
reiniciar. Para contornar isso sem exigir reinício, o Transcritor também
checa diretamente o caminho de instalação padrão
(`C:\Program Files\Tesseract-OCR\tesseract.exe`) quando o PATH não resolve —
funciona imediatamente após a instalação, sem precisar fechar e abrir o app
de novo (ver `find_tesseract()` em `backend/system_check.py`).

**Pacotes de idioma**: em vez de depender do que o instalador do sistema
trouxe (o pacote do winget, por exemplo, só vem com inglês por padrão), o
Transcritor baixa os arquivos `.traineddata` de cada idioma sob demanda do
repositório oficial
[`tessdata_fast`](https://github.com/tesseract-ocr/tessdata_fast) na
primeira vez que são usados, guardando em `~/.transcritor/tessdata`
(produção) ou `backend/data/tessdata` (dev) — não na pasta de instalação do
Tesseract, que normalmente não é gravável sem privilégio de administrador
(ver `ensure_tessdata_language()` em `backend/system_check.py`).

## Integração com IA (opcional)

Além do Tesseract local, o Transcritor pode usar um modelo de IA como motor
de OCR — útil para digitalizações difíceis, manuscritos ou páginas com
layout complexo — e/ou para revisar o texto depois de transcrito.

1. Instale as dependências dos provedores que for usar:

   ```bash
   cd backend
   pip install -r requirements-ai.txt
   ```

2. Configure a chave de API de um ou mais provedores (Anthropic Claude,
   OpenAI, Google Gemini) — no app Qt, pelo botão **Configurações de IA**;
   no modo web, pelo mesmo botão na interface. As chaves ficam salvas
   apenas na sua máquina, em texto puro, em `~/.transcritor/config.json`
   (app instalado) ou `backend/data/config.json` (modo desenvolvimento) —
   nunca são enviadas a nada além da API do próprio provedor escolhido.

3. Escolha:
   - **Motor de transcrição**: Tesseract (grátis, local) ou Inteligência
     artificial (mais precisa em digitalizações difíceis, tem custo por
     página via a API do provedor escolhido).
   - **Pós-processamento**: nenhum, correção gramatical + formatação como
     livro, ou uma instrução personalizada livre (ex.: "resuma esta obra em
     3 páginas", "traduza para o inglês", "liste os personagens principais").

Documentos longos são divididos em blocos antes de ir para a IA (limite de
contexto), processados em paralelo lógico e depois unidos numa passada final
de síntese — isso vale tanto para a correção gramatical quanto para
instruções livres como resumir.

## Transcrição de áudio/vídeo (modo servidor/web e MCP)

Arquivos MP3, WAV, FLAC, M4A, MP4 ou MKV também podem ser enviados: em vez de
OCR página por página, o arquivo inteiro é transcrito de uma vez (fala →
texto) e o resultado vira um `.docx` de fluxo único, igual ao de uma
instrução de pós-processamento.

Dois motores possíveis (o campo "Motor de transcrição" ganha uma terceira
opção quando um arquivo de áudio/vídeo é selecionado):

- **Whisper local** (`engine=whisper`) — grátis, offline, equivalente ao
  Tesseract para OCR. Usa o pacote `openai-whisper`, que **não vem
  instalado por padrão nem embutido nos pacotes .exe/.deb/AppImage** (traz o
  PyTorch, uma dependência grande demais para o instalador base). Instale à
  parte:

  ```bash
  cd backend
  pip install -r requirements-whisper.txt
  ```

  Os pesos do modelo (padrão: `base`, ~150 MB) baixam sozinhos na primeira
  execução e ficam em `~/.cache/whisper` — na pasta do usuário, não na pasta
  de instalação do programa. Requer também o `ffmpeg` instalado no sistema
  (`sudo apt-get install ffmpeg`, `brew install ffmpeg`, ou
  https://ffmpeg.org/download.html no Windows). Sem GPU, pode ser lento.
- **IA em nuvem** (`engine=ai`) — use **OpenAI** (Whisper via API) ou
  **Google Gemini**, ambos com suporte nativo a áudio. A **Anthropic Claude
  não é compatível** com transcrição de áudio nesta API; se selecionada, a
  interface troca automaticamente para OpenAI, e a API rejeita a chamada com
  um erro claro caso venha assim mesmo.

MP4/MKV são tratados como vídeo — só o áudio é considerado.

## Idiomas (modo servidor/web e MCP)

Dois seletores de idioma independentes:

- **Idioma da interface** (canto superior direito, modo web): traduz os
  textos do app — hoje em Português, English e Español, detectado
  automaticamente do navegador na primeira visita (com opção de trocar
  manualmente, persistida por navegador). Ver `frontend/i18n.js`.
- **Idioma do conteúdo**: o idioma do documento ou áudio sendo transcrito.
  Padrão: **detecção automática** (o motor de IA ou o Whisper identificam
  sozinhos), sempre preservando o idioma original — a transcrição nunca
  traduz, a menos que você peça isso explicitamente via pós-processamento
  personalizado. O Tesseract é a exceção: como não detecta idioma sozinho,
  exige escolher um idioma específico da lista. Mais de 20 idiomas
  disponíveis (`backend/languages.py`); idiomas com suporte historicamente
  mais fraco no OCR local aparecem marcados, sugerindo o motor de IA.

O app desktop Qt hoje só oferece Português, Inglês e Português+Inglês (sem
detecção automática) — a lista completa está disponível no modo servidor/web
e via MCP.

## Servidor MCP (Claude Desktop / Claude Code)

Além da interface, a transcrição pode ser chamada diretamente pelo Claude
Desktop ou Claude Code como uma ferramenta MCP — sem abrir nada.
`backend/mcp_server.py` expõe uma tool `transcrever` que reaproveita os
mesmos módulos do app (`ocr.py`, `audio_transcriber.py`, `ai_providers.py`,
`docx_builder.py`) e devolve o caminho do `.docx` gerado (ou o texto direto,
se pedido).

1. Instale as dependências do servidor MCP:

   ```bash
   cd backend
   pip install -r requirements-mcp.txt
   ```

2. Registre o servidor:

   **Claude Code** (via CLI):

   ```bash
   claude mcp add transcritor -- /caminho/absoluto/para/backend/.venv/bin/python /caminho/absoluto/para/backend/mcp_server.py
   ```

   (no Windows, use o `python.exe` do seu ambiente virtual, ex.:
   `C:\caminho\para\backend\.venv\Scripts\python.exe`)

   **Claude Desktop**: edite o arquivo de configuração —
   `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS),
   `%APPDATA%\Claude\claude_desktop_config.json` (Windows) ou
   `~/.config/Claude/claude_desktop_config.json` (Linux) — adicionando:

   ```json
   {
     "mcpServers": {
       "transcritor": {
         "command": "/caminho/absoluto/para/backend/.venv/bin/python",
         "args": ["/caminho/absoluto/para/backend/mcp_server.py"]
       }
     }
   }
   ```

   Reinicie o Claude Desktop depois de salvar.

3. Use pedindo algo como "transcreva este PDF: /caminho/do/arquivo.pdf" — o
   Claude chama a tool `transcrever` com os parâmetros certos.

Parâmetros da tool `transcrever`: `caminho_arquivo` (obrigatório),
`motor` (`tesseract`/`ai` para documentos, `whisper`/`ai` para áudio —
padrão `tesseract`), `provedor_ia` (`anthropic`/`openai`/`google`, necessário
quando `motor="ai"` ou há pós-processamento), `idioma` (padrão `auto`),
`pos_processamento` (`none`/`grammar`/`custom`, padrão `none`), `instrucao`
(obrigatória em `custom`) e `formato_saida` (`docx`/`text`, padrão `docx`).
As chaves de API usadas são as mesmas configuradas no app (mesmo
`config.json` local).

## Gerar os pacotes (.deb, AppImage, .exe)

Os scripts ficam em `packaging/`. Todos compilam primeiro um binário
standalone com PyInstaller a partir de `backend/qt_main.py` (o app Qt
completo, sem dependência de navegador) e depois embrulham esse binário no
formato de cada sistema.

```bash
# .deb (Debian/Ubuntu) — testado e funcional, declara o Tesseract como
# dependência do pacote (o apt instala automaticamente)
./packaging/build-deb.sh

# AppImage (qualquer distro Linux x86_64) — requer o binário `appimagetool`
# no PATH (baixe em https://github.com/AppImage/AppImageKit/releases,
# arquivo appimagetool-x86_64.AppImage, e torne executável). Sem ele, o
# script monta a AppDir e para, avisando como terminar manualmente.
./packaging/build-appimage.sh

# Windows (.exe) — precisa rodar em uma máquina Windows com Python 3.10+ e
# o Inno Setup instalados (https://jrsoftware.org/isinfo.php)
.\packaging\windows\build-windows.ps1
```

Os pacotes gerados vão para `dist-packages/`. Em todos os três, se o
Tesseract OCR não estiver instalado no sistema de destino, o Transcritor
avisa e orienta a instalação num diálogo, na primeira execução (não é um
requisito para abrir o app — só para usar o motor de OCR local).

Os arquivos gerados pelo usuário (`.docx` de saída e `config.json` com as
chaves de API) ficam em `~/.transcritor/` em qualquer um dos pacotes.

## Estrutura do projeto

```
backend/
  qt_main.py                # Entry point do app desktop nativo (Qt/PySide6) — modo principal
  qt_app/
    theme.py                 # Paleta e QSS (folha de estilo Qt) do tema medieval
    icons.py                 # Ícones SVG monocromáticos reutilizáveis
    widgets.py                # Funções utilitárias para construir widgets padronizados
    worker.py                 # QThread que roda extração/OCR/IA em background
    main_window.py             # Janela principal (4 cards)
    settings_dialog.py        # Diálogo de Configurações de IA
    dependency_dialog.py      # Diálogo de aviso do Tesseract ausente
  main.py                    # API FastAPI (modo servidor/web opcional) — fila, zip, áudio, idiomas
  web_launcher.py            # Launcher do modo servidor/web (abre o navegador)
  mcp_server.py              # Servidor MCP (tool `transcrever` para Claude Desktop/Code)
  paths.py                   # Diretórios de dados (dev e executável empacotado)
  ocr.py                     # Extração de texto de PDF/EPUB + OCR plugável (Tesseract ou IA)
  audio_transcriber.py       # Transcrição de áudio/vídeo (fala -> texto): Whisper local ou IA
  languages.py                # Tabela única de idiomas de CONTEÚDO (Tesseract/Whisper/IA)
  ai_providers.py            # Camada de provedores de IA (Claude, OpenAI, Gemini)
  settings_store.py          # Armazenamento local das chaves de API
  system_check.py            # Detecção/instalação do Tesseract OCR + tessdata sob demanda
  docx_builder.py            # Geração do arquivo .docx final
  requirements.txt           # Dependências base (extração, OCR, docx, FastAPI)
  requirements-ai.txt        # Dependências dos provedores de IA (opcional)
  requirements-whisper.txt   # Whisper local para áudio (opcional, traz o PyTorch)
  requirements-mcp.txt       # Dependências do servidor MCP (opcional)
  requirements-desktop.txt   # Base + PySide6 + PyInstaller (app desktop)
frontend/                    # HTML/CSS/JS do modo servidor/web opcional
  index.html
  style.css
  app.js
  i18n.js                    # Idioma da INTERFACE web (não confundir com languages.py)
packaging/
  build-pyinstaller.sh       # Compila o binário standalone do app Qt (usado pelos 3 scripts abaixo)
  build-deb.sh               # Gera o .deb
  build-appimage.sh          # Gera o AppImage
  debian/                    # control/desktop entry do .deb
  windows/                   # script Inno Setup + build-windows.ps1 do .exe
  icons/                     # ícone do app em vários tamanhos + .ico
install.sh                   # Instalador via terminal (Linux/macOS)
```

## Limitações conhecidas

- O app desktop Qt (`qt_main.py`) ainda não expõe áudio/vídeo, detecção
  automática de idioma, nem a lista completa de 20+ idiomas — esses recursos
  existem hoje no modo servidor/web e via MCP. Portar para a interface Qt é
  um próximo passo natural.
- O modo servidor/web mantém a fila de jobs em memória: reiniciar o servidor
  a limpa (os `.docx` já gerados continuam salvos em disco). O app desktop
  Qt processa um arquivo por vez, sem fila.
- Limite de upload no modo web: 200 MB por arquivo.
- Qualidade do OCR local depende da resolução/nitidez do scan ou foto.
- OCR, transcrição de áudio por IA em nuvem e pós-processamento têm custo
  por chamada de API e enviam o conteúdo ao provedor escolhido — considere
  isso para obras de terceiros ou com direitos autorais. O Whisper local
  evita isso para áudio, mas exige instalação separada
  (`requirements-whisper.txt`, traz o PyTorch), `ffmpeg` no sistema, e é
  mais lento sem GPU.
- As chaves de API ficam em texto puro no arquivo de configuração local;
  qualquer pessoa com acesso a essa máquina tem acesso a elas.
- A interface web tem 3 idiomas (pt-BR/en/es); os nomes dos idiomas de
  CONTEÚDO no seletor (ex.: "Alemão"/"German") só existem traduzidos para
  português e inglês — com a interface em espanhol, esses nomes aparecem em
  inglês.
- Os pacotes empacotados não incluem o Tesseract OCR (exceto o `.deb`, que o
  declara como dependência e o apt instala junto) — nos demais, o app avisa e
  orienta a instalação num diálogo na primeira execução.
- O instalador Windows (`.exe`) e o AppImage precisam ser compilados em uma
  máquina com acesso às respectivas ferramentas (Inno Setup no Windows;
  `appimagetool` no Linux) — não foram gerados/testados neste ambiente de
  desenvolvimento por não termos acesso a essas ferramentas aqui. Os scripts
  em `packaging/` estão prontos para rodar em uma máquina com esse acesso.
  O `.deb` foi gerado e testado de verdade (build → `apt install` → app abre
  → `apt remove`) neste ambiente.
