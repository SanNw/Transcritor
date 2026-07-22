# Transcritor

Aplicativo que converte livros, revistas, PDFs e EPUBs — digitais ou
escaneados/fotografados — em arquivos **.docx**.

- PDFs e EPUBs com texto: o texto é extraído diretamente.
- PDFs escaneados ou imagens (foto de página, JPG/PNG/TIFF/BMP/WEBP): o texto
  é reconhecido automaticamente via OCR (Tesseract).
- O app decide página por página se precisa de OCR ou não, então um PDF pode
  ter parte digital e parte escaneada sem configuração extra.
- Dá para transcrever vários arquivos e depois baixar tudo de uma vez em um
  `.zip`.
- Roda como app web local (navegador) ou como app desktop com janela própria.

## Pré-requisitos

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado no
  sistema, com o pacote de idioma português:

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
escaneado ou imagem para a área indicada, escolha o idioma do OCR e acompanhe
o progresso. Quando terminar, baixe o `.docx` individualmente ou clique em
**Baixar tudo (.zip)** para pegar todas as transcrições concluídas de uma vez.

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
pelo usuário (uploads temporários e `.docx` de saída) ficam salvos em
`~/.transcritor/`.

## Estrutura do projeto

```
backend/
  main.py                  # API FastAPI: upload, fila de processamento, download, zip
  ocr.py                   # Extração de texto de PDF/EPUB + OCR de páginas/imagens
  docx_builder.py          # Geração do arquivo .docx final
  desktop_app.py           # Launcher do app desktop (janela via pywebview)
  requirements.txt         # Dependências do modo web
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
- Qualidade do OCR depende da resolução/nitidez do scan ou foto.
- O executável empacotado não inclui o Tesseract OCR — ele precisa estar
  instalado separadamente na máquina onde o app roda.
