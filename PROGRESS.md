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
- **Idioma do conteúdo** (documento/áudio): mais de 20 idiomas
  (`backend/languages.py`), com **detecção automática por padrão** — nunca
  traduz sozinho, só reconhece no idioma original (a menos que o usuário peça
  tradução via pós-processamento). Tesseract é a exceção (não detecta
  sozinho, exige escolha explícita); a UI corrige automaticamente
  incompatibilidades motor/idioma.
- **Idioma da interface**: Português, English, Español — detectado do
  navegador (`navigator.language`), com seletor manual persistido em
  `localStorage`. Ver `frontend/i18n.js`.
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
testadas de ponta a ponta, assim como a instalação automática do Tesseract no
Windows (via `winget`) e o sistema de idiomas (interface + conteúdo) — ver
seções acima e "Decisões técnicas" abaixo.

Lacunas conhecidas e deixadas como estão (avaliadas, não bugs escondidos):

- Idioma da interface tem só 3 opções (pt-BR/en/es); os *nomes* dos idiomas
  de CONTEÚDO no seletor só existem traduzidos pra português/inglês (com a
  interface em espanhol, aparecem em inglês). Mensagens de `system_check.py`
  (dependência do Tesseract) ainda são só em português. Ver "Limitações
  conhecidas" no `README.md`.
- Skills de terceiros que o usuário encontrou via `openskills install`
  (`alper-dev/build-for-good-ux-skill`, `fratilanico/apex-os-bad-boy`,
  `JeremyKalmus/parade`, `juspay/kolu`) foram auditadas com o
  `skill-security-auditor`: só `build-for-good-ux-skill` passou limpo (é uma
  skill de verdade, com `SKILL.md`). As outras três nem são skills — são
  repositórios de aplicações completas sem `SKILL.md`, com dezenas de
  achados CRITICAL/HIGH (uso de `child_process`/`exec`, YAML inseguro etc. —
  esperado em código de aplicação normal, mas não algo pra instalar como
  "skill" do Claude). Nenhuma foi instalada.

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
- **Tesseract automático no Windows via `winget`, não via download direto**:
  a ideia original era baixar o instalador oficial da UB-Mannheim direto do
  site deles (`digi.bib.uni-mannheim.de`), mas esse domínio estava
  inacessível a partir do ambiente de sandbox usado numa sessão anterior.
  Solução mais robusta sugerida pelo usuário: usar
  `winget install -e --id UB-Mannheim.TesseractOCR --silent
  --accept-package-agreements --accept-source-agreements` — o winget baixa
  do GitHub Releases da UB-Mannheim (não do site instável) e foi testado de
  ponta a ponta nesta sessão (instalou, OCR funcionou depois). Ver
  `_install_hint()` em `backend/system_check.py`.
- **PATH desatualizado após instalar (Windows)**: instalar algo (winget,
  qualquer `.exe`) atualiza o PATH do sistema, mas um processo Python já em
  execução não vê essa mudança até reiniciar — isso é uma limitação do SO,
  não tem como "atualizar o PATH" de um processo já rodando a partir de
  dentro dele. Contornado checando diretamente o caminho de instalação
  padrão do Tesseract (`C:\Program Files\Tesseract-OCR\tesseract.exe`)
  quando o PATH não resolve (`find_tesseract()` em `system_check.py`) —
  testado de verdade: funcionou sem reiniciar o app logo após o `winget
  install`.
- **Tessdata gerenciado pelo próprio app, não pelo pacote do sistema**: o
  pacote do winget só vem com inglês (`eng.traineddata`); a pasta de
  instalação do Tesseract (`Program Files`) normalmente não é gravável sem
  admin. Em vez de lutar com isso, o Transcritor baixa os `.traineddata` que
  precisa (de `tessdata_fast` no GitHub) para sua própria pasta de dados
  (`TESSDATA_DIR` em `paths.py`) e aponta o Tesseract pra lá via a variável
  de ambiente `TESSDATA_PREFIX` (não via `--tessdata-dir` no `config` do
  pytesseract — `shlex.split` no Windows mantém aspas como caracteres
  literais no path, quebrando o caminho; `TESSDATA_PREFIX` evita esse
  problema porque o Tesseract lê a env var diretamente, sem parsing de
  aspas). Isso significa que o Transcritor **não usa mais a pasta tessdata
  do sistema** em nenhuma plataforma — funciona igual em Windows/Linux/macOS,
  independente do que o instalador do SO trouxe.
- **`languages.py` como fonte única de idiomas de conteúdo**: antes,
  `ai_providers.py` e `audio_transcriber.py` tinham cada um seu próprio
  mini-dicionário de mapeamento de idioma (Tesseract usa códigos de 3 letras,
  Whisper usa ISO 639-1 de 2 letras). Consolidado numa tabela só
  (`backend/languages.py`) com ~24 idiomas, cada um sabendo seu próprio
  código Tesseract/Whisper/nome — adicionar um idioma novo é só acrescentar
  uma linha lá. Suporte a `"auto"` (detecção automática): válido pra
  `engine="ai"`/`"whisper"` (esses motores detectam sozinhos, então o app só
  omite a instrução de idioma do prompt/parâmetro), mas **inválido pro
  Tesseract** (não detecta sozinho) — validado em `main.py`, `mcp_server.py`
  e auto-corrigido na UI (`app.js` troca de motor ou de idioma sozinho pra
  nunca deixar essa combinação inválida chegar no envio).
- **Prompts de IA reforçam "não traduza"**: como os provedores de IA são
  LLMs de propósito geral, sem a instrução explícita eles poderiam
  "ajudar" traduzindo o texto reconhecido pro idioma da conversa (o usuário
  pediu explicitamente que a transcrição preserve o idioma original, só
  traduzindo se pedido via pós-processamento). `TRANSCRIBE_PROMPT_TEMPLATE`
  e `AUDIO_TRANSCRIBE_PROMPT_TEMPLATE` (`ai_providers.py`) têm essa instrução
  explícita — testado de verdade com detecção automática (`lang=auto`) numa
  imagem em português via IA (OpenAI): o resultado saiu em português, sem
  tradução, mesmo com a conversa em português.
- **i18n da interface é um sistema à parte de `languages.py`**: idioma da
  INTERFACE (botões, rótulos) vive só em `frontend/i18n.js`
  (`TRANSLATIONS`/`t()`/`applyTranslations()`), detecção via
  `navigator.language` com override em `localStorage`, sem nada no backend
  — propositalmente simples (é só um dicionário de strings + um seletor).
  Elementos com estado dinâmico (status de job, status de configuração de
  provedor) **não** usam `data-i18n` direto porque esse atributo é
  sobrescrito goela abaixo pelas funções que renderizam o estado real; em
  vez disso, escutam o evento customizado `i18n:applied` (disparado por
  `applyTranslations()`) pra se re-renderizarem chamando `t()` de novo.
  Cuidado ao adicionar novo texto dinâmico: sempre re-renderizar via esse
  evento, nunca só via `data-i18n` estático.

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

Para testar idiomas: troque o seletor no canto superior direito (idioma da
interface) e confira se todos os textos mudam, inclusive jobs já na lista
(sem precisar recarregar a página); no seletor "Idioma do conteúdo", escolha
um idioma marcado como suporte limitado (ex.: chinês, árabe) com o motor
Tesseract selecionado e confira se aparece o aviso; troque pra "Detectar
automaticamente" e confirme que o motor muda sozinho pra IA (Tesseract não
aceita `auto`).

Para regenerar os pacotes: ver seção "Gerar os pacotes" no `README.md`.
