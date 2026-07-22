# Transcritor

Aplicativo que converte livros, revistas, PDFs e EPUBs — digitais ou
escaneados/fotografados — em arquivos **.docx**.

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
- Dá para transcrever vários arquivos e depois baixar tudo de uma vez em um
  `.zip`.
- Roda como app web local (navegador) ou como app desktop com janela própria.

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

Esses pacotes abrem o Transcritor no seu navegador padrão (`http://127.0.0.1:8000`)
já configurado. Veja `packaging/` para os scripts que geram cada um — ver a
seção [Gerar os pacotes](#gerar-os-pacotes-deb-appimage-exe) abaixo.

### Opção 2 — script de instalação (Linux/macOS, a partir do código-fonte)

```bash
git clone <este repositório>
cd Transcritor
./install.sh              # instala o modo web
./install.sh --desktop    # inclui o modo desktop (janela própria)
./install.sh --ai         # inclui os SDKs de IA (Claude/OpenAI/Gemini)
```

O script detecta o Python e o gerenciador de pacotes do sistema, confere se o
Tesseract está instalado (perguntando antes de instalar via `sudo`), cria um
ambiente virtual e instala um comando `transcritor` em `~/.local/bin`. Depois
é só rodar `transcritor` (modo navegador) ou `transcritor --desktop`.

### Opção 3 — manual (qualquer sistema, para desenvolvimento)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Abra **http://localhost:8000** no navegador. Arraste um PDF, EPUB, livro
escaneado ou imagem para a área indicada, escolha o idioma e acompanhe o
progresso. Quando terminar, baixe o `.docx` individualmente ou clique em
**Baixar tudo (.zip)** para pegar todas as transcrições concluídas de uma vez.

Pré-requisito nesse modo manual: Python 3.10+ e, opcionalmente, o
[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) já instalado
(`sudo apt-get install tesseract-ocr tesseract-ocr-por` no Ubuntu/Debian,
`brew install tesseract tesseract-lang` no macOS, ou o instalador oficial no
Windows — https://github.com/UB-Mannheim/tesseract/wiki).

## Integração com IA (opcional)

Além do Tesseract local, o Transcritor pode usar um modelo de IA como motor
de OCR — útil para digitalizações difíceis, manuscritos ou páginas com
layout complexo — e/ou para revisar o texto depois de transcrito.

1. Instale as dependências dos provedores que for usar:

   ```bash
   cd backend
   pip install -r requirements-ai.txt
   ```

2. Na interface, clique em **Configurações de IA** e cole a chave de API de
   um ou mais provedores (Anthropic Claude, OpenAI, Google Gemini). As
   chaves ficam salvas apenas na sua máquina, em texto puro, em
   `~/.transcritor/config.json` (modo desktop) ou `backend/data/config.json`
   (modo desenvolvimento) — nunca são enviadas a nada além da API do próprio
   provedor escolhido.

3. Ao enviar um arquivo, escolha:
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

## Como rodar (app desktop, janela própria)

Instala as dependências extras (`pywebview` + `pyinstaller`) e abre o app em
uma janela nativa, sem precisar do navegador (usa GTK/WebKit no Linux, Qt/Edge
WebView2 no Windows, Cocoa no macOS):

```bash
cd backend
pip install -r requirements-desktop.txt
python desktop_app.py
```

## Gerar os pacotes (.deb, AppImage, .exe)

Os scripts ficam em `packaging/`. Todos compilam primeiro um binário
standalone com PyInstaller (a partir de `backend/web_launcher.py`, que sobe o
servidor local e abre o navegador padrão — não depende de GTK/WebKit, ao
contrário do modo desktop acima, o que o torna bem mais portável entre
distribuições) e depois embrulham esse binário no formato de cada sistema.

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
avisa e orienta a instalação na primeira execução (não é um requisito para
abrir o app — só para usar o motor de OCR local).

Os arquivos gerados pelo usuário (uploads temporários, `.docx` de saída e
`config.json` com as chaves de API) ficam em `~/.transcritor/` em qualquer um
dos pacotes.

## Estrutura do projeto

```
backend/
  main.py                  # API FastAPI: upload, fila, download, zip, configurações, system-check
  paths.py                 # Diretórios de dados (dev e executável empacotado)
  ocr.py                   # Extração de texto de PDF/EPUB + OCR plugável (Tesseract ou IA)
  ai_providers.py          # Camada de provedores de IA (Claude, OpenAI, Gemini)
  settings_store.py        # Armazenamento local das chaves de API
  system_check.py          # Detecção do Tesseract OCR + comando de instalação por SO
  docx_builder.py          # Geração do arquivo .docx final
  desktop_app.py           # Launcher do modo desktop (janela via pywebview, GTK/Qt/WebView2)
  web_launcher.py          # Launcher usado pelos pacotes .deb/AppImage/.exe (abre o navegador)
  requirements.txt         # Dependências do modo web
  requirements-ai.txt      # Dependências dos provedores de IA (opcional)
  requirements-desktop.txt # Dependências extras do modo desktop/empacotamento
frontend/
  index.html
  style.css
  app.js
packaging/
  build-pyinstaller.sh     # Compila o binário standalone (usado pelos 3 scripts abaixo)
  build-deb.sh             # Gera o .deb
  build-appimage.sh        # Gera o AppImage
  debian/                  # control/desktop entry do .deb
  windows/                 # script Inno Setup + build-windows.ps1 do .exe
  icons/                   # ícone do app em vários tamanhos + .ico
install.sh                 # Instalador via terminal (Linux/macOS)
```

## Limitações conhecidas

- O estado dos jobs fica em memória: reiniciar o servidor limpa a lista
  (os arquivos `.docx` já gerados continuam salvos em disco).
- Limite de upload: 200 MB por arquivo.
- Qualidade do OCR local depende da resolução/nitidez do scan ou foto.
- OCR e pós-processamento por IA têm custo por chamada de API e enviam o
  conteúdo do documento ao provedor escolhido — considere isso para obras de
  terceiros ou com direitos autorais.
- As chaves de API ficam em texto puro no arquivo de configuração local;
  qualquer pessoa com acesso a essa máquina tem acesso a elas.
- Os pacotes empacotados não incluem o Tesseract OCR (exceto o `.deb`, que o
  declara como dependência e o apt instala junto) — nos demais, o app avisa e
  orienta a instalação na primeira execução.
- O instalador Windows (`.exe`) e o AppImage precisam ser compilados em uma
  máquina com acesso às respectivas ferramentas (Inno Setup no Windows;
  `appimagetool` no Linux) — não foram gerados/testados neste ambiente de
  desenvolvimento por não termos acesso a essas ferramentas aqui. Os scripts
  em `packaging/` estão prontos para rodar em uma máquina com esse acesso.
