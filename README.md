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

## Pré-requisitos

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado no
  sistema, com o pacote de idioma português (necessário mesmo se você for
  usar OCR por IA, pois é o motor padrão):

  ```bash
  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr tesseract-ocr-por

  # macOS (Homebrew)
  brew install tesseract tesseract-lang

  # Windows: instale o instalador oficial e marque o idioma "Portuguese"
  # https://github.com/UB-Mannheim/tesseract/wiki
  ```

## Instalação

```bash
cd backend
pip install -r requirements.txt
```

## Como rodar (modo navegador)

```bash
cd backend
uvicorn main:app --reload
```

Abra **http://localhost:8000** no navegador. Arraste um PDF, EPUB, livro
escaneado ou imagem para a área indicada, escolha o idioma e acompanhe o
progresso. Quando terminar, baixe o `.docx` individualmente ou clique em
**Baixar tudo (.zip)** para pegar todas as transcrições concluídas de uma vez.

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
uma janela nativa, sem precisar do navegador:

```bash
cd backend
pip install -r requirements-desktop.txt
python desktop_app.py
```

### Gerar um executável (opcional)

Empacota tudo — backend e frontend — em um único executável para distribuir
sem exigir Python instalado na máquina de destino (o Tesseract OCR continua
sendo um requisito do sistema):

```bash
cd backend

# Linux/macOS
pyinstaller --name Transcritor --onefile --windowed \
  --add-data "../frontend:frontend" desktop_app.py

# Windows (PowerShell)
pyinstaller --name Transcritor --onefile --windowed `
  --add-data "../frontend;frontend" desktop_app.py
```

O executável final fica em `backend/dist/Transcritor`. Os arquivos gerados
pelo usuário (uploads temporários, `.docx` de saída e `config.json` com as
chaves de API) ficam salvos em `~/.transcritor/`.

## Estrutura do projeto

```
backend/
  main.py                  # API FastAPI: upload, fila, download, zip, configurações
  paths.py                 # Diretórios de dados (dev e executável empacotado)
  ocr.py                   # Extração de texto de PDF/EPUB + OCR plugável (Tesseract ou IA)
  ai_providers.py          # Camada de provedores de IA (Claude, OpenAI, Gemini)
  settings_store.py        # Armazenamento local das chaves de API
  docx_builder.py          # Geração do arquivo .docx final
  desktop_app.py           # Launcher do app desktop (janela via pywebview)
  requirements.txt         # Dependências do modo web
  requirements-ai.txt      # Dependências dos provedores de IA (opcional)
  requirements-desktop.txt # Dependências extras do modo desktop/empacotamento
frontend/
  index.html
  style.css
  app.js
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
- O executável empacotado não inclui o Tesseract OCR — ele precisa estar
  instalado separadamente na máquina onde o app roda.
