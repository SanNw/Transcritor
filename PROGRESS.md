# Progresso do Transcritor

Este arquivo existe para dar contexto rápido a qualquer sessão do Claude
(ou de outra pessoa) que continue este projeto — o que já foi feito, o que
falta, e decisões importantes tomadas pelo caminho. Atualize-o conforme o
projeto evolui.

## O que o app faz hoje

Aplicativo que converte livros, revistas, PDFs, EPUBs e agora também
áudio/vídeo (digitais, escaneados/fotografados, ou fala gravada) em `.docx`,
com:

- Extração de texto nativo de PDF/EPUB, com OCR automático (página a
  página) para o que estiver escaneado.
- Dois motores de OCR à escolha do usuário: Tesseract local (grátis) ou IA
  (Claude, OpenAI, Gemini — usuário cola a própria chave de API).
- Transcrição de áudio/vídeo (MP3/WAV/FLAC/M4A/MP4/MKV): Whisper local
  (grátis, offline, instalação opcional) ou IA em nuvem (OpenAI/Google — a
  Anthropic Claude não suporta áudio nesta API). Ver `audio_transcriber.py`.
- Pós-processamento opcional por IA: correção gramatical + formatação como
  livro, ou instrução livre (resumir, traduzir, listar personagens etc.),
  com divisão em blocos + síntese final para documentos longos. Funciona
  também em cima de texto transcrito de áudio.
- Download individual ou em lote (`.zip`).
- Quatro formas de usar: navegador (`uvicorn main:app`), app desktop com
  janela própria (`desktop_app.py`, via pywebview), pacotes instaláveis
  (`.deb`, AppImage, instalador Windows), ou como ferramenta MCP direto no
  Claude Desktop/Claude Code (`mcp_server.py`, tool `transcrever`).
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

As três frentes prioritárias (empacotamento, áudio, MCP) estão concluídas e
testadas de ponta a ponta — ver seções acima e "Decisões técnicas" abaixo.

Ideias levantadas mas ainda não implementadas:

- **Instalação automática do Tesseract no Windows**: hoje `system_check.py`
  marca `auto_installable: False` pro Windows (só mostra link + instrução
  manual). Tentei baixar o instalador oficial (UB-Mannheim,
  `digi.bib.uni-mannheim.de`) via `curl` e via `Invoke-WebRequest` do
  PowerShell nesta sessão e o servidor deles estava inacessível a partir
  daqui (conexão recusada nos dois casos) — pode ser só uma restrição deste
  ambiente específico, não necessariamente do usuário final. Não implementei
  às cegas sem conseguir testar; se for retomar, a ideia seria: baixar o
  `.exe` deles (é um instalador Inno Setup, aceita `/VERYSILENT
  /SUPPRESSMSGBOXES /NORESTART` como o nosso próprio instalador) e rodar
  silenciosamente, análogo ao `brew install` já usado no macOS. Precisa
  confirmar antes que esse domínio responde normalmente numa rede comum.

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
- Próximo item combinado com o usuário: revisar o design/UI do app com as
  skills `frontend-design` (as skills `ui-ux-pro-max`/`editorial` que o
  usuário mencionou não estavam disponíveis nesta sessão).

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
- **Áudio não usa `ocr.py`**: um áudio/vídeo não é "página por página" — o
  arquivo inteiro vira um texto único numa chamada só. Por isso é um módulo
  novo (`audio_transcriber.py`), não uma extensão de `extract_pages`. O
  resultado sempre passa por `build_docx_from_text` (fluxo único), nunca por
  `build_docx` (que é por página/capítulo).
- **Anthropic Claude não transcreve áudio**: diferente de imagem (onde os
  três provedores funcionam), a API da Anthropic não tem modalidade de áudio
  hoje. `AIProvider.supports_audio` (`ai_providers.py`) é `False` por padrão
  e só `True` em `OpenAIProvider`/`GoogleProvider`. A validação em
  `main.py` (`/api/transcribe`) e em `mcp_server.py` rejeita
  `ai_provider="anthropic"` para áudio com uma mensagem clara; o frontend
  (`app.js`) troca automaticamente para OpenAI ao detectar isso, então o
  usuário nem chega a ver o erro na prática.
- **Whisper local**: `transcribe_audio_local` (`audio_transcriber.py`) usa o
  pacote `openai-whisper` (modelo `base` por padrão), testado de verdade
  nesta sessão — funciona offline, sem chave de API. Decisão importante: não
  entra em `requirements.txt`/`requirements-ai.txt` nem é embutido nos
  pacotes .exe/.deb/AppImage, porque traz o PyTorch (dependência grande
  demais pro instalador base) — fica em `requirements-whisper.txt`,
  instalação separada e opcional. Os pesos do modelo baixam sozinhos na
  primeira execução e ficam em `~/.cache/whisper` (pasta do usuário), não na
  pasta de instalação do programa — foi um requisito explícito do usuário
  pra não inchar o app. Também exige `ffmpeg` no sistema (checado com
  `shutil.which` antes de tentar usar, com mensagem de erro clara se faltar).
- **Testes de áudio com chave real**: as primeiras tentativas com chaves de
  teste da OpenAI e do Google bateram em erro de cota (429 —
  `insufficient_quota` na OpenAI, `RESOURCE_EXHAUSTED` com `limit: 0` no
  Google, ambos sem faturamento habilitado). Confirmava que a chamada
  chegava certinha na API (não era bug de formatação de request), só
  faltava crédito. Depois que o usuário adicionou US$5 de crédito na OpenAI,
  o teste real funcionou — Whisper (API) transcreveu corretamente um áudio
  de teste gerado via TTS nativo do Windows (`System.Speech` por
  PowerShell, sem precisar de internet pra gerar o áudio de teste).
- **MCP server reaproveita o mesmo `config.json`**: `mcp_server.py` importa
  `settings_store.py` do mesmo jeito que `main.py`, então as chaves de API
  configuradas pela interface web (ou editadas direto no arquivo) valem
  também pro servidor MCP — não tem configuração duplicada. Testado de
  verdade via protocolo MCP real (`mcp.client.stdio`, não só chamando a
  função Python direto): tool `transcrever` funcionando tanto pra áudio
  (motor `whisper` local) quanto pra imagem (motor `ai`/OpenAI), nos dois
  formatos de saída (`text` e `docx`).

## Como testar rapidamente depois de mudanças

```bash
cd backend
pip install -r requirements.txt -r requirements-ai.txt   # ai opcional
uvicorn main:app --reload
# abrir http://localhost:8000, testar upload de PDF/EPUB/imagem/áudio
```

Para o Whisper local: `pip install -r requirements-whisper.txt` (+ `ffmpeg`
no sistema) e escolher motor "whisper" ao enviar um áudio.

Para o servidor MCP: `pip install -r requirements-mcp.txt` e rodar
`python mcp_server.py` (stdio) — ou registrar no Claude Desktop/Code, ver
seção "Servidor MCP" no `README.md`.

Para regenerar os pacotes: ver seção "Gerar os pacotes" no `README.md`.
