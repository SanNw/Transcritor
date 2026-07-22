# Transcritor

App desktop nativo (Qt/PySide6, Windows + Linux) que converte livros,
revistas, PDFs e EPUBs — digitais ou escaneados/fotografados — em arquivos
**.docx**.

- PDFs e EPUBs com texto: o texto é extraído diretamente.
- PDFs escaneados ou imagens (foto de página, JPG/PNG/TIFF/BMP/WEBP): o texto
  é reconhecido via OCR local (Tesseract) ou via IA (Claude, OpenAI ou
  Google Gemini), à sua escolha.
- Opcionalmente, uma IA pode revisar o resultado: corrigir ortografia e
  gramática e reorganizar o texto em capítulos como um livro, ou seguir
  qualquer instrução livre — resumir a obra, traduzir, listar personagens
  etc.
- O app decide página por página se precisa de OCR ou não, então um PDF pode
  ter parte digital e parte escaneada sem configuração extra.
- Interface nativa (widgets Qt, não HTML) organizada em 4 cards: Arquivo,
  Configuração da transcrição, Inteligência Artificial e Execução.

## Instalação

Se o Tesseract OCR não estiver instalado, o próprio Transcritor detecta isso
na primeira execução e mostra o comando certo para o seu sistema — não
precisa instalar antes.

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
servidor/navegador, ver abaixo).

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

## Uso

1. Escolha o arquivo (arraste para o card **Arquivo** ou clique em
   **Escolher arquivo**).
2. Ajuste o idioma, o motor de OCR e o pós-processamento no card
   **Configuração da transcrição**.
3. Se for usar IA (motor ou pós-processamento), configure a chave em
   **Configurações de IA** (botão no canto superior direito) e escolha o
   provedor no card **Inteligência Artificial**.
4. Clique em **Iniciar transcrição** no card **Execução** e acompanhe o
   progresso. Ao concluir, o app oferece abrir a pasta com o `.docx` gerado.

## Modo servidor/web (opcional)

Além do app desktop, o backend também roda como servidor local com interface
web (útil para automações ou acesso remoto), usando o mesmo código de
extração/IA:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Abra **http://localhost:8000** no navegador. Esse modo mantém fila de jobs,
download em lote (`.zip`) e a mesma API (`/api/transcribe`, `/api/settings`,
`/api/system-check`). Quem instalou via `install.sh`, roda com
`transcritor --web`.

## Integração com IA (opcional)

Além do Tesseract local, o Transcritor pode usar um modelo de IA como motor
de OCR — útil para digitalizações difíceis, manuscritos ou páginas com
layout complexo — e/ou para revisar o texto depois de transcrito.

1. Instale as dependências dos provedores que for usar:

   ```bash
   cd backend
   pip install -r requirements-ai.txt
   ```

2. Clique em **Configurações de IA** e cole a chave de API de um ou mais
   provedores (Anthropic Claude, OpenAI, Google Gemini). As chaves ficam
   salvas apenas na sua máquina, em texto puro, em `~/.transcritor/config.json`
   (app instalado) ou `backend/data/config.json` (modo desenvolvimento) —
   nunca são enviadas a nada além da API do próprio provedor escolhido.

3. No card **Configuração da transcrição**, escolha:
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
  main.py                    # API FastAPI (modo servidor/web opcional)
  web_launcher.py            # Launcher do modo servidor/web (abre o navegador)
  paths.py                   # Diretórios de dados (dev e executável empacotado)
  ocr.py                     # Extração de texto de PDF/EPUB + OCR plugável (Tesseract ou IA)
  ai_providers.py            # Camada de provedores de IA (Claude, OpenAI, Gemini)
  settings_store.py          # Armazenamento local das chaves de API
  system_check.py            # Detecção do Tesseract OCR + comando de instalação por SO
  docx_builder.py            # Geração do arquivo .docx final
  requirements.txt           # Dependências base (extração, OCR, docx, FastAPI)
  requirements-ai.txt        # Dependências dos provedores de IA (opcional)
  requirements-desktop.txt   # Base + PySide6 + PyInstaller (app desktop)
frontend/                    # HTML/CSS/JS do modo servidor/web opcional
  index.html
  style.css
  app.js
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

- Qualidade do OCR local depende da resolução/nitidez do scan ou foto.
- OCR e pós-processamento por IA têm custo por chamada de API e enviam o
  conteúdo do documento ao provedor escolhido — considere isso para obras de
  terceiros ou com direitos autorais.
- As chaves de API ficam em texto puro no arquivo de configuração local;
  qualquer pessoa com acesso a essa máquina tem acesso a elas.
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
- O modo servidor/web (`main.py` via `uvicorn`) processa um job por vez em
  background e mantém fila em memória — reiniciar o servidor limpa a lista
  (os `.docx` já gerados continuam salvos em disco). O app desktop Qt
  processa um arquivo por vez, sem fila.
