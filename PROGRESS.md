# Progresso do Transcritor

Este arquivo existe para dar contexto rápido a qualquer sessão do Claude
(ou de outra pessoa) que continue este projeto — o que já foi feito, o que
falta, e decisões importantes tomadas pelo caminho. Atualize-o conforme o
projeto evolui.

## O que o app faz hoje

Aplicativo que converte livros, revistas, PDFs e EPUBs (digitais ou
escaneados/fotografados) em `.docx`, com:

- Extração de texto nativo de PDF/EPUB, com OCR automático (página a
  página) para o que estiver escaneado.
- Dois motores de OCR à escolha do usuário: Tesseract local (grátis) ou IA
  (Claude, OpenAI, Gemini — usuário cola a própria chave de API).
- Pós-processamento opcional por IA: correção gramatical + formatação como
  livro, ou instrução livre (resumir, traduzir, listar personagens etc.),
  com divisão em blocos + síntese final para documentos longos.
- Download individual ou em lote (`.zip`).
- Três formas de rodar: navegador (`uvicorn main:app`), app desktop com
  janela própria (`desktop_app.py`, via pywebview), ou pacotes instaláveis
  (`.deb`, AppImage, instalador Windows).
- Checagem automática de dependências (Tesseract) na primeira execução, com
  aviso e comando de instalação certo para o SO.
- Visual com tema medieval (paleta e tipografia definidas pelo usuário a
  partir de uma imagem de design system) — ver `frontend/style.css`.

Detalhes de instalação e arquitetura estão no `README.md`.

## Estado do empacotamento (importante!)

- **`.deb`**: `packaging/build-deb.sh` — testado de ponta a ponta neste
  ambiente (build → `apt install` → app abre → `apt remove`). Funciona.
- **AppImage**: `packaging/build-appimage.sh` — a AppDir é montada e
  validada (o `AppRun` sobe o servidor corretamente), mas o passo final
  (rodar `appimagetool` para gerar o `.AppImage`) **não foi testado**
  porque este ambiente de desenvolvimento não tem acesso ao GitHub
  Releases para baixar o `appimagetool`. Rode o script numa máquina com
  internet normal, ou baixe o `appimagetool-x86_64.AppImage` manualmente e
  aponte `APPIMAGETOOL=/caminho/para/ele`.
- **Windows `.exe`**: `packaging/windows/transcritor.iss` +
  `packaging/windows/build-windows.ps1` — escritos seguindo a sintaxe
  padrão do Inno Setup, mas **nunca compilados nem testados**, porque este
  é um ambiente Linux sem Windows/Inno Setup disponível. Precisa ser
  compilado numa máquina Windows (ou CI com runner Windows) com Python
  3.10+ e o Inno Setup instalados. Ao abrir uma sessão do Claude numa
  máquina Windows para isso, veja o prompt sugerido abaixo.

### Prompt sugerido para compilar o `.exe` (rodar com Claude numa máquina Windows)

```
Estou no repositório do Transcritor. Preciso compilar o instalador Windows.
Rode packaging\windows\build-windows.ps1 a partir da raiz do repositório
(instale Python 3.10+ e o Inno Setup se não estiverem presentes — Inno
Setup em https://jrsoftware.org/isinfo.php). Se der erro, investigue e
corrija packaging/windows/transcritor.iss ou build-windows.ps1 conforme
necessário — foram escritos sem poder ser testados em Windows. Depois de
gerar o .exe em dist-packages/, teste rodando o instalador e confirmando
que o Transcritor abre no navegador em http://127.0.0.1:8000.
```

## Pendências conhecidas / próximos passos

Combinados com o usuário, ainda não iniciados:

1. **Servidor MCP** — expor a transcrição como ferramenta MCP, para Claude
   Desktop/Claude Code chamarem "transcreva este PDF" diretamente, sem abrir
   o app web.
2. **Transcrição de áudio** (MP3/WAV/FLAC/M4A/MP4/MKV) — reaproveitando a
   camada `ai_providers.py` já existente (Whisper/OpenAI, Claude, Gemini
   todos suportam áudio).

Roadmap maior discutido com o usuário (lista de features vinda de uma
sessão de brainstorm com ChatGPT, avaliada e priorizada por esforço/valor —
ver histórico da conversa para a lista completa categorizada). Usuário
decidiu terminar o empacotamento antes de priorizar esses itens. Bucket
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

- **`web_launcher.py` vs `desktop_app.py`**: os pacotes `.deb`/AppImage/`.exe`
  usam `web_launcher.py` (sobe o servidor + abre o navegador padrão), não o
  `desktop_app.py` (janela nativa via pywebview). Motivo: pywebview no Linux
  depende de GTK+WebKit do sistema, com nomes de pacote que variam entre
  versões de distro (`gir1.2-webkit2-4.0` vs `4.1`) — muito frágil para um
  pacote genérico. `desktop_app.py` continua disponível para quem instalar
  manualmente (`pip install -r requirements-desktop.txt`).
- **Chaves de API**: ficam em texto puro em `~/.transcritor/config.json`
  (pacotes/produção) ou `backend/data/config.json` (dev). Nunca voltam
  completas pela API (`GET /api/settings` mascara, só mostra os 4 últimos
  caracteres).
- **Bug de CSS já corrigido**: `[hidden]` no navegador tem prioridade baixa
  por padrão; qualquer classe com `display:` explícito (como `.overlay` ou
  `.options-row`) sobrescrevia isso e deixava elementos "escondidos"
  clicáveis. Corrigido com uma regra global `[hidden] { display: none
  !important; }` em `frontend/style.css` — importante não remover essa regra.
- **Ordem de rotas no FastAPI**: `/api/jobs/download-all` precisa estar
  declarada *antes* de `/api/jobs/{job_id}` em `main.py`, senão o FastAPI
  interpreta "download-all" como um `job_id` e retorna 404. Já corrigido,
  mas atenção ao adicionar novas rotas sob `/api/jobs/`.
- **Ambiente de desenvolvimento (sandbox Linux)**: sem acesso à internet
  irrestrito — só a repos GitHub explicitamente autorizados e a PyPI (via
  proxy). Downloads diretos do GitHub Releases (ex.: `appimagetool`) são
  bloqueados. Isso não deve afetar o usuário final rodando os scripts na
  própria máquina.

## Como testar rapidamente depois de mudanças

```bash
cd backend
pip install -r requirements.txt -r requirements-ai.txt   # ai opcional
uvicorn main:app --reload
# abrir http://localhost:8000, testar upload de PDF/EPUB/imagem
```

Para regenerar os pacotes: ver seção "Gerar os pacotes" no `README.md`.
