# Transcritor

Aplicativo web local que converte livros, revistas e PDFs — digitais ou
escaneados/fotografados — em arquivos **.docx**.

- PDFs com texto selecionável: o texto é extraído diretamente.
- PDFs escaneados ou imagens (foto de página, JPG/PNG/TIFF/BMP/WEBP): o texto
  é reconhecido automaticamente via OCR (Tesseract).
- O app decide página por página se precisa de OCR ou não, então um PDF pode
  ter parte digital e parte escaneada sem configuração extra.

## Pré-requisitos

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado no
  sistema, com o pacote de idioma português:

  ```bash
  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr tesseract-ocr-por

  # macOS (Homebrew)
  brew install tesseract tesseract-lang
  ```

## Instalação

```bash
cd backend
pip install -r requirements.txt
```

## Como rodar

```bash
cd backend
uvicorn main:app --reload
```

Abra **http://localhost:8000** no navegador. Arraste um PDF, livro escaneado
ou imagem para a área indicada, escolha o idioma do OCR e acompanhe o
progresso. Quando terminar, o botão **Baixar .docx** fica disponível.

## Estrutura do projeto

```
backend/
  main.py          # API FastAPI: upload, fila de processamento, download
  ocr.py           # Extração de texto de PDF + OCR de páginas/imagens
  docx_builder.py  # Geração do arquivo .docx final
  requirements.txt
frontend/
  index.html
  style.css
  app.js
```

## Limitações conhecidas

- O estado dos jobs fica em memória: reiniciar o servidor limpa a lista
  (os arquivos `.docx` já gerados continuam em `backend/data/outputs/`).
- Limite de upload: 200 MB por arquivo.
- Qualidade do OCR depende da resolução/nitidez do scan ou foto.
