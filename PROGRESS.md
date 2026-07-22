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

Os três pacotes estão testados de ponta a ponta. Nenhum aviso de "não
testado" resta.

- **`.deb`**: `packaging/build-deb.sh` — testado de ponta a ponta (build →
  `apt install` → app abre → `apt remove`). Funciona.
- **AppImage**: `packaging/build-appimage.sh` — testado de ponta a ponta
  numa sessão Windows, usando um container Docker (`ubuntu:22.04`) para ter
  um ambiente Linux. `appimagetool` baixado de
  `https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage`.
  Dentro de containers sem FUSE, rode o `appimagetool` (e o próprio
  `.AppImage` gerado, para testar) com a flag `--appimage-extract-and-run`
  — não precisa mudar nada no `AppRun` nem no script, é só uma limitação de
  ambiente de build/teste sem FUSE, não do pacote em si. Testado: o
  `.AppImage` gerado sobe o servidor e responde em `http://127.0.0.1:8000`
  (`/` e `/api/settings` retornam 200).
- **Windows `.exe`**: `packaging/windows/transcritor.iss` +
  `packaging/windows/build-windows.ps1` — testado de ponta a ponta numa
  sessão Windows real (Windows 10, Python 3.13, Inno Setup 6.7.3). Corrigido
  `build-windows.ps1` para localizar o `ISCC.exe` também via registro do
  Windows (`HKLM:\...\Uninstall\*` procurando `InstallLocation` de "Inno
  Setup*"), não só em `Program Files (x86)\Inno Setup 6` — necessário
  porque o Inno Setup pode estar instalado em outro drive/pasta (ex.:
  `E:\Programas\Inno Setup 6` nesta máquina). Testado: gerou
  `Transcritor-1.0.0-setup.exe`, instalado silenciosamente
  (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`), o app abriu sozinho (o
  `[Run]` do `.iss` dispara mesmo com essas flags), serviu `/` e
  `/api/settings` em `http://127.0.0.1:8000`, depois desinstalado
  (`unins000.exe /VERYSILENT`) limpando tudo.

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
- **Bug de CRLF ao clonar em Windows**: se o Git local tiver
  `core.autocrlf=true` (comum em Windows), o checkout converte `LF` → `CRLF`
  em todo arquivo de texto — inclusive `.sh`, `.desktop` e `VERSION`, que o
  repositório guarda com `LF`. Isso quebra os scripts de build (`set -euo
  pipefail` falha com "invalid option name" porque o `\r` vira parte da
  própria opção) e pior: `VERSION` (`1.0.0\r\n`) contamina o nome do
  `.AppImage` gerado com um `\r` literal no meio do nome do arquivo
  (`Transcritor-1.0.0<CR>-x86_64.AppImage`), quebrando qualquer ferramenta
  que tente abrir esse caminho depois. Corrigido com `.gitattributes` na
  raiz (`* text=auto eol=lf`, mais `*.ps1`/`*.bat` forçados para `eol=crlf`)
  — já commitado, então clones novos não devem mais sofrer disso. Se
  aparecer de novo (por exemplo, editando esses arquivos a partir do
  Windows com uma ferramenta que não respeita `.gitattributes`), rode
  `sed -i 's/\r$//' <arquivo>` para corrigir na hora.

## Como testar rapidamente depois de mudanças

```bash
cd backend
pip install -r requirements.txt -r requirements-ai.txt   # ai opcional
uvicorn main:app --reload
# abrir http://localhost:8000, testar upload de PDF/EPUB/imagem
```

Para regenerar os pacotes: ver seção "Gerar os pacotes" no `README.md`.
