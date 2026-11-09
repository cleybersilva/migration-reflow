# Decisões de arquitetura

## ADR-001 — Runtime somente stdlib

Python >= 3.12 via uv, sem dependências de runtime ou chamadas de rede. pytest e ruff
são dependências diretas apenas de desenvolvimento; suas transitivas ficam em uv.lock.
A instalação de ferramentas pode precisar de rede; o processamento do legado não.

## ADR-002 — IAra compatível com OpenAI

O endpoint precisa oferecer `/v1/chat/completions`. `IARA_BASE_URL` deve terminar em
`/v1`; `IARA_API_KEY` e `IARA_MODEL` são fornecidos pelo ambiente do processo.
`iara-default` é um alias placeholder; endpoint, compatibilidade e ID real do modelo
permanecem a confirmar. Não selecionar IAra automaticamente enquanto não configurada.

## ADR-003 — OpenCode V2

Ambiente observado: OpenCode 2.0.32. Usar `providers`, `permissions`, `shell` e
`subagent`, em vez dos campos legados do prompt. Usar runtime OpenAI-compatible
nativo do OpenCode. Não usar `doom_loop`: não é ação Core atual do V2.
Fonte: https://opencode.ai/v2/docs/migrate-v1 e guias de providers/permissões.
As permissões completas por agent serão implementadas na Fase 6.

## ADR-004 — Compatibilidade entre harnesses

Skills ficam em `.claude/skills/`, com caminho explícito em `opencode.json` para
descoberta compartilhada. Agents OpenCode são canônicos; espelhos Claude serão
gerados e testados na Fase 6. `AGENTS.md` concentra as regras.

## ADR-005 — Entrada confidencial e evidência mascarada

`input/` fica fora do Git, salvo o exemplo sintético `quote-scraper`.
Os sete materiais preexistentes ficam preservados localmente e ignorados no Git.
Em conflito entre leitura de trechos brutos e inventário mascarado, prevalece a
restrição: agents de negócio só recebem inventário/evidências mascarados.

## ADR-006 — Bloqueio seguro durante a construção

O hook roda scan e validação Robin, mas bloqueia enquanto esses comandos não existem.
Não criar implementações fictícias que retornem sucesso. Não contornar o hook.
O scanner deverá validar conteúdo preparado para commit, não apenas arquivos locais.

## ADR-007 — Robin e checkpoint

Whitelist obrigatória; nenhuma ação presumida validada. Sem snippets reais do PAD,
registrar a pendência sem inventar sintaxe. PAD/PARTIAL requer checkpoint explícito;
NOT_PAD não gera conversão. Testes estáticos não comprovam execução no PAD.

## ADR-008 — Esqueleto incremental

Módulos Python reservados com docstrings; sem comportamento simulado. Referências
e documentos futuros são identificados como pendentes. Nenhum artefato 00–05 é
criado para projeto inexistente; as pastas serão materializadas pelo pipeline.

## ADR-009 — Extração inicial com minimização

Sem exports reais, A360 usa fixtures sintéticas e metadados `packageName`,
`commandName` e nomes dos atributos; valores livres são omitidos, inclusive URLs
e referências brutas do Vault. Uma referência local `arquivo:node:credential-vault`
preserva rastreabilidade sem copiar credenciais. A tabela inicial de comandos
reconhecidos é conservadora e não equivale a uma whitelist Robin.
Python usa AST, resolve aliases de importação e não executa o código. .NET é
explicitamente heurístico. Não declarar cobertura completa de dialetos reais A360.

## ADR-010 — Reextração e manifesto

Cada extração gera hashes SHA256 de todos os arquivos de entrada (ZIP incluído),
data UTC e versão do reflow. Reextração limpa veredito/checkpoint e marca fases
02–05 como desatualizadas; não remove artefatos anteriores. O inventário não tem
timestamp. Projetos inválidos fazem o lote falhar, sem impedir os demais projetos.

## ADR-011 — `opencode.json` e agents: schema V2 real, não o legado

Validado contra o `opencode` 2.0.32 instalado (`opencode debug config`,
`opencode debug agents`, e o `$schema` de `https://opencode.ai/config.json`):
`provider`/`permission` (singular) são campos legados V1; os atuais são
`providers`/`permissions` (plural, `permissions` sempre um array de
`{action, resource, effect}}`), e isso vale tanto no `opencode.json` raiz
quanto no frontmatter de cada `.opencode/agents/*.md`. `doom_loop` não é usado
(ADR-003). Agent markdown **não tem campo `temperature`** —
`additionalProperties: false` no schema rejeitaria/ignoraria silenciosamente.
Corrigido um bug real herdado: a ação `"shell"` não existe; é `"bash"`.

## ADR-012 — Lint Robin nunca interpreta sintaxe Robin

> **Revogado pelo ADR-029 (2026-11-04).** Com a PAD Robin Action KB vendorizada, a sintaxe
> passou a ter fonte verificável, e o `lint-robin` agora a interpreta. Mantido aqui como
> histórico.

`robin/lint.py` não tenta reconhecer qual ação PAD um `Main.robin` usa —
isso exigiria conhecer a sintaxe interna do Robin, que não está validada
(proibido por `AGENTS.md`). Em vez disso, o lint valida a estrutura que o
próprio pipeline controla: `notas-conversao.md` lista as ações usadas (uma
convenção nossa, em Markdown) e é cruzado contra `reference/robin-actions.md`;
`README.md` do flow precisa de um cabeçalho; o texto puro do `.robin` é
varrido para segredo atribuído e caminho absoluto fora de
`C:\Users\Public\Documents\`. Ação fora da whitelist só é pega se estiver
citada em `notas-conversao.md` — por isso todo agent que gera `Main.robin`
é instruído a manter esse arquivo em dia.

## ADR-013 — Relatório de lote nunca presume fase futura

`reflow/report.py` mostra `—` no veredito e `0` em flows/TODO/ações quando a
fase correspondente ainda não rodou para aquele projeto, em vez de omitir a
coluna ou inventar um valor. Isso é consistente com a regra de não declarar
pronto o que não foi feito — o relatório é honesto sobre o que falta, não só
sobre o que já existe.

## ADR-014 — Segunda opinião na classificação (reflow-classification-reviewer)

A classificação é a decisão mais cara do pipeline: ela decide se um projeto
vai para o PAD ou não. Em vez de confiar num único agent, `reflow-classify-review`
roda um segundo agent que reaplica `classification-rubric.md` do zero, sem ver
o raciocínio do primeiro, e grava a própria opinião em
`03-classification/review.md`. Decisões explícitas:

- O reviewer **nunca** sobrescreve `classification.md` — permissão de edição
  restrita ao arquivo `review.md`, não só à pasta da fase (mais estrita que os
  demais agents, que podem escrever em qualquer arquivo da própria subpasta).
- Divergência (`agreement: diverge`) não bloqueia nada sozinha; ela só precisa
  aparecer com destaque no checkpoint humano, que continua sendo quem decide.
- Rodar sempre, mesmo em `NOT_PAD` — um falso negativo (projeto que deveria
  ir para o PAD e foi classificado como `NOT_PAD`) é tão caro quanto um falso
  positivo.
- Custo aceito: uma chamada de LLM a mais por projeto. Troca-se inferência
  extra por robustez na decisão mais cara do pipeline.

## ADR-015 — Revisor semântico do Robin (reflow-robin-reviewer)

`reflow lint-robin` (ADR-012) só valida o que o próprio pipeline controla —
estrutura, não semântica: segredo atribuído, caminho absoluto fora do
permitido, ação citada em `notas-conversao.md` ausente da whitelist, cabeçalho
do `README.md`. Ele não verifica se o `Main.robin` cobre de fato os
`pad_use_cases`, se há `TODO reflow` demais para o flow ser útil, se a
nomenclatura segue `robin-conventions.md`, nem se `notas-conversao.md`
realmente corresponde ao que está no `.robin`. `reflow-convert-review` cobre
exatamente essa lacuna, como um segundo agent depois do lint, nunca no lugar
dele. Mesmas restrições do ADR-014: só grava o próprio `04-pad/<flow>/review.md`,
nunca `Main.robin`/`README.md`/`notas-conversao.md`, e não aprova nem bloqueia
sozinho — só informa o checkpoint humano antes de `reflow-test`.

## ADR-016 — Copilot como terceiro harness espelhado

O usuário pediu explicitamente que toda evolução de skill/agent apareça nos
três harnesses (Claude Code, OpenCode, GitHub Copilot) — nunca só em um.
Antes desta decisão, `.github/` nem existia. Desenho adotado, caso a caso:

- **Instruções de raiz**: `.github/copilot-instructions.md` é um ponteiro
  para `AGENTS.md`, idêntico em espírito ao `CLAUDE.md` — mesma fonte única
  de verdade, três arquivos finos.
- **Skills → prompt files**: `.github/prompts/<nome>.prompt.md`, um por
  skill (mais `reflow-report.prompt.md`, que espelha o command do OpenCode
  que só roda `reflow report`, sem skill dedicada). Escrito **à mão**, não
  gerado — porque o corpo é só um ponteiro de uma linha para
  `.claude/skills/<nome>/SKILL.md` (que o Copilot, em modo agent, consegue
  abrir e seguir), igual ao padrão já usado em `.opencode/commands/*.md`.
  Isso evita duplicar o conteúdo da skill numa terceira cópia.
- **Agents → chat modes**: `.github/chatmodes/<nome>.chatmode.md`, **gerado**
  por `scripts/sync_copilot.py` a partir de `.opencode/agents/` — mesma fonte
  dos espelhos Claude, mesmo motivo (o corpo de um agent é instrução
  completa, não um ponteiro; copiar manualmente divergiria com o tempo).
- **Honestidade sobre o que o Copilot não impõe**: o Copilot Chat não tem
  `permissions`/`tools` com bloqueio por recurso como o OpenCode — um
  chatmode pode, tecnicamente, editar qualquer arquivo se o modelo decidir
  ignorar a instrução. Por isso `render_chatmode()` **sempre** acrescenta um
  aviso explícito disso no fim de cada arquivo gerado — nunca sugerir ao
  usuário que os três harnesses têm o mesmo nível de imposição técnica.
- `tests/unit/test_copilot.py` trava a paridade (todo skill tem prompt, todo
  agent tem chatmode, todo chatmode carrega o aviso) do mesmo jeito que
  `test_sync_agents.py`/`test_skills.py` já travavam Claude/OpenCode — a
  omissão de um dos três harnesses numa mudança futura vira teste vermelho,
  não um lembrete em documentação que alguém pode esquecer de ler.

Não validado: nenhum destes arquivos foi testado dentro do GitHub Copilot de
verdade (a extensão não está disponível neste ambiente) — o formato segue a
documentação pública de customização do Copilot Chat (prompt files, chat
modes), mas, como o `IARA_MODEL` do ADR-002, o comportamento exato só se
confirma com a ferramenta real instalada.

## ADR-017 — Dashboard local de teste honesto, sem dependência de runtime nova

Pedido original do usuário: uma "estrutura robusta de LangChain" e um
dashboard local de teste "como tinha antes" (o projeto irmão
`D:\ENGINEER\VS_Code\reflow\`, que tem um `web/` com exatamente esse
propósito). Análise, apresentada e aceita pelo usuário antes de implementar:
**LangChain foi avaliado e descartado.** O design anterior (worker
PowerShell isolado + `format` JSON Schema nativo do Ollama + validação de
evidência feita à mão) já resolve o mesmo problema com uma fronteira de
segurança **mais forte** — a chamada de rede ao LLM fica fora do processo
Python, nunca dentro dele — e zero dependência pesada nova. Adotar LangChain
aqui significaria puxar uma árvore grande de dependências transitivas só
para reimplementar algo que o Ollama já faz nativamente, e reabriria a
"Fronteira Python × LLM" (ADR-001) para um ganho líquido nulo.

Decisão: portar a estrutura madura como estava, em `dashboard/` (irmão de
`reflow/`, nunca importado por ele):

- `dashboard/pipeline.py` (`DashboardRunner`) reaproveita
  `reflow.cli.extract_to` (extraído de `_extract_one` para ser chamável com
  um diretório de saída arbitrário, sem gravar manifesto — usado também pelo
  CLI real, comportamento idêntico), `reflow.security.masking.mask_data` e
  `reflow.security.scan.scan_bytes` — duas funções pequenas e aditivas que
  não existiam antes desta fase e foram adicionadas ao núcleo (nunca
  alterando as funções já existentes `mask`/`scan_repository`).
- `dashboard/ollama_worker.ps1` é a única chamada de rede ao LLM — um
  subprocesso PowerShell fixo e confiável, nunca dentro do processo Python
  de longa duração do servidor (`dashboard/server.py`).
- `dashboard/server.py` reaproveita o mesmo design do projeto irmão:
  loopback-only, checagem de Host/Origin, token CSRF por sessão (nomeado
  `csrf`, não `token`, para não disparar falso positivo do scanner de
  segredos — `AGENTS.md` nunca permite silenciar com `reflow:allow-secret`
  fora de fixtures/definição do detector), CSP, SSE com cursor por cliente.
- Zero dependência nova em `pyproject.toml`; `dashboard/` em Python usa só
  stdlib, mesma régua do núcleo. `test_runtime_dependencies_are_empty`
  continua validando isso sem nenhuma mudança.
- Mesmo escopo honesto de antes: teste textual isolado em
  `.dashboard-runs/`, nunca escreve em `output/`, nunca fabrica PASS/FAIL,
  Robin aparece como "não aplicável" (este teste não gera flow).

`tests/integration/test_dashboard.py` e `tests/frontend/dashboard.test.cjs`
portam a suíte de regressão do projeto irmão (SSE real, `FakeRunner` sem
rede, isolamento de `output/`, retry de inferência, validação de HTML/CSS).

## ADR-018 — Fase 1 de segurança: mascaramento por chave e scan do índice, não da working tree

Diagnóstico anterior apontou lacunas reais em `security/masking.py` e
`security/scan.py` sem caracterizá-las como vazamento comprovado. Fase 1
corrigiu as que cabiam numa mudança pequena, preservando assinaturas
públicas:

- `mask_data()` agora mascara pelo **nome da chave** (`password`, `token`,
  `api_key`, `authorization`, `connection_string`) mesmo quando chave e
  valor são strings separadas numa estrutura (dict/list aninhados) — antes
  só `mask()` por regex de texto livre era aplicado por string-folha, que
  nunca via a associação chave→valor do JSON.
- `SECRET_ASSIGNMENT_RE` (fonte única em `masking.py`, reusada por
  `scan.py` e `robin/lint.py`) passou a reconhecer chave JSON entre aspas
  seguida de dois-pontos e valor entre aspas, que antes não batia (a aspa
  que fecha a chave vinha antes do `:`). A nova forma exige aspas
  exatamente ao redor da palavra-chave — não um `['"]?` solto — para não
  casar o sufixo de uma chave maior como `X-Reflow-Token` (continha
  "Token" mas não é, ela mesma, uma chave sensível).
- Cabeçalho HTTP de portador (`Authorization` seguido de token `Bearer`):
  `BEARER_TOKEN_RE`, novo e aplicado antes de `SECRET_ASSIGNMENT_RE` em
  `mask_secrets()`, consome o par palavra-chave+token inteiro; antes
  `SECRET_ASSIGNMENT_RE` sozinho capturava a palavra do esquema como se
  fosse o valor e deixava o token real intacto depois dela.
- Excertos de achado (`scan.py`, `robin/lint.py`) agora mascaram **antes**
  de truncar para 120 caracteres, não depois — uma credencial maior que o
  trecho podia ter o corte caindo no meio da chave e escapar do regex de
  máscara.
- `reflow:allow-secret` deixou de silenciar uma linha em qualquer arquivo.
  Só é honrado dentro de `tests/` (fixture/teste sintético) ou nos próprios
  módulos do detector (`reflow/security/scan.py`,
  `reflow/security/masking.py`, onde o padrão cita a própria palavra que
  detecta). Fora disso é ignorado — inclusive para `scan_bytes()` (saída
  isolada de LLM usada pelo `dashboard/`), que nunca poderia confiar no
  próprio conteúdo que está checando para se autoexcluir.
- Novo `scan_staged()` em `security/scan.py`: lê o blob preparado (stage 0,
  via `git show :<path>`) de cada arquivo com `git diff --cached
  --name-only -z`, nunca a working tree. `scan_repository()` (working
  tree) continua existindo sem mudança de comportamento, para os fluxos
  que já dependem dela. O hook (`.githooks/pre-commit`) passou a chamar
  `reflow scan --staged` em vez de `reflow scan`: um segredo preparado
  bloqueia mesmo que a working tree tenha sido editada depois do `git
  add`; um segredo só na working tree (nunca `git add`) não bloqueia mais
  o commit por engano. `_staged_file_names()` usa `-z` (NUL) e
  `_read_staged_blob()` lê por `:<path>` (nunca começa com `-`, então um
  nome de arquivo começando com hífen não é interpretado como opção do
  `git show`) — nenhum nome de arquivo é passado a um shell.
  `StagedScanError` é levantada (nunca `[]` silencioso) se o índice não
  puder ser lido.

**Mudança de comportamento que pode afetar compatibilidade:** dentro de
`scan_staged()` (só o hook de pre-commit), conteúdo preparado que não
decodifica como UTF-8 gera achado `conteudo_nao_utf8` e **bloqueia o
commit** — nunca alega ter inspecionado algo que não leu. Isso é diferente
de `scan_repository()` (working tree), que continua pulando esse conteúdo
em silêncio, comportamento preservado para não quebrar quem já depende
dele. Na prática: comitar ou reescrever um arquivo binário (ex.: a imagem
`diagram - FINAL com AGENTS.jpg` já versionada) agora passa pelo gate sem
problema enquanto ele não for staged de novo; se for re-`git add`-ado, o
hook bloqueia e pede decisão humana em vez de deixar passar sem ter lido.
Repositório hoje não tem nenhum arquivo binário staged, então nada quebra
nesta sessão — mas qualquer fluxo futuro que precise commitar binário
precisará de uma decisão explícita (ex.: hook rodar sem `--staged` para
esse caso, ou uma exceção dedicada) antes de ampliar esse hábito.

Não corrigido nesta fase (ver `AGENTS.md`/Fase 2 e seguintes, propositalmente
fora de escopo): contenção de caminho de entrada/saída, symlink/junction,
`..`, UNC, nomes reservados/ADS em ZIP, limites de lote/bytes/conexão do
dashboard, escrita atômica/lock por projeto, checkpoint vinculado a hash.

## ADR-019 — Fase 2 de segurança: contenção de caminho, ZIP e limites do dashboard

Diagnóstico anterior apontou lacunas em caminho/symlink/ZIP/limites sem
caracterizá-las como exploradas. Fase 2 corrigiu o que cabia numa mudança
pequena, preservando loopback/CSRF/CSP/isolamento das saídas do dashboard:

- Novo `reflow/security/paths.py`: `reject_unsafe_links(root)` recusa o
  projeto **inteiro** (nunca só "poda" a parte insegura) se `root`, ou
  qualquer entrada abaixo dele, for symlink ou junction (`Path.is_symlink()
  or Path.is_junction()` — nenhum dos dois sozinho cobre as duas formas de
  link no Windows). Deliberadamente grosseiro: um projeto com um link
  escondido não é "parcialmente confiável", e podar só o link exigiria
  decidir caso a caso o que mais pode depender dele. `is_unc_path()` é a
  mesma checagem de prefixo UNC (`\\servidor\...` / `//servidor/...`)
  usada tanto aqui quanto em `robin/lint.py`.
- `reflow/cli.py`: `_build_manifest()` (hash SHA256 das entradas) e
  `extract_to()` (ponto de entrada único do CLI real **e** do dashboard,
  via `reflow.cli.extract_to`) chamam `reject_unsafe_links` antes de ler
  qualquer conteúdo — um projeto com link escondido nunca tem conteúdo
  fora do sandbox lido, hasheado ou incluído no inventário.
- `dashboard/pipeline.py`: `DashboardRunner.projects()` agora recusa
  também cada subpasta de projeto (antes só `input/` em si era checado) —
  mas aqui a falha é por projeto, não em lote: um projeto-link some da
  lista, os outros continuam disponíveis (ao contrário de
  `reject_unsafe_links`, que é tudo-ou-nada para um único projeto já
  escolhido).
- `reflow/robin/lint.py`: `_is_allowed_output_path()` resolve `..`
  **textualmente** via `ntpath.normpath` (nunca toca o filesystem — é só o
  texto do `Main.robin` sendo lido) antes de comparar com
  `C:\Users\Public\Documents\`; antes a comparação era por prefixo de
  string bruta, então `...Documents\..\..\Windows\...` passava porque a
  string começava com o prefixo permitido antes do `..` ser interpretado.
  Novo `UNC_PATH_RE` varre caminho UNC separadamente — antes nem era
  reconhecido como "caminho a checar" (a regex de caminho absoluto exigia
  letra de unidade), então um caminho UNC no meio do flow passava
  despercebido, não por estar na lista de permitidos, mas por nunca ter
  sido avaliado.
- `reflow/security/safe_zip.py`: `_is_safe_member()` agora rejeita `:` em
  qualquer posição (cobre letra de unidade E Alternate Data Stream do NTFS,
  tipo `arquivo.txt:oculto`), nome reservado do Windows (`CON`, `PRN`,
  `AUX`, `NUL`, `COM1-9`, `LPT1-9`, com ou sem extensão, por componente de
  caminho) e componente com espaço/ponto final (o Windows ignora na hora de
  criar o arquivo). Novo `_windows_collision_key()` detecta, antes de
  extrair qualquer membro, dois nomes do ZIP que o Windows trataria como o
  mesmo arquivo (case-insensitive ou por espaço/ponto final) — duas
  entradas com o nome exatamente igual continuam permitidas (a segunda
  sobrescreve a primeira, como sempre foi).
- `dashboard/pipeline.py`: `_check_input_budget()` recusa um projeto antes
  de extrair se tiver mais de 500 arquivos, mais de 12 níveis de
  profundidade ou mais de 20 MB — orçamento do teste local isolado, não da
  extração real (`reflow extract`/`--all`, que não tem esse teto).
- `dashboard/server.py`: `Dashboard.MAX_SSE_CLIENTS = 6` limita conexões
  simultâneas a `/api/events`; acima disso, `429` em vez de abrir mais uma
  thread sem limite. Loopback-only, checagem de Host/Origin, CSRF por
  sessão e CSP não foram alterados.

**Mudança de comportamento que pode afetar compatibilidade:**
- Um projeto em `input/<nome>` com qualquer symlink/junction (mesmo em
  subpasta, mesmo não relacionado ao que seria extraído) passa a ser
  recusado por inteiro, tanto por `reflow extract` quanto pelo teste local
  do dashboard. Nenhum projeto hoje em `input/` tem link algum, então nada
  quebra nesta sessão.
- Um `Main.robin` com caminho UNC agora reprova o lint sempre (antes não
  era nem avaliado). Um `Main.robin` com `..` que escapa de
  `C:\Users\Public\Documents\` reprova mesmo que a string comece com o
  prefixo permitido (antes passava).
- Um ZIP com nome reservado do Windows, `:` no nome (ADS/letra de unidade)
  ou colisão case-insensitive agora é recusado por inteiro na validação
  (antes de extrair qualquer membro), em vez de extrair e deixar o Windows
  decidir o que acontece depois.
- Um teste local do dashboard sobre um projeto maior que o orçamento
  (>500 arquivos, >12 níveis, >20 MB) agora é recusado explicitamente em
  vez de rodar (possivelmente lento ou travando num projeto grande demais
  para um "smoke test"). Não afeta `reflow extract`.

Não corrigido nesta fase (Fase 3 e seguintes, propositalmente fora de
escopo): escrita atômica, lock por projeto, checkpoint vinculado a hash,
resiliência de lote, priorização determinística entre JSON/ZIP do A360.

## ADR-020 — Fase 3 de segurança: escrita atômica, lock por projeto e checkpoint vinculado a hash

O diagnóstico de 24/10/2026 apontou três lacunas que não eram vazamento
simulado, e sim integridade de dado (itens 6 e 8): gravação direta sem
atômica, ausência de lock por projeto, e um `checkpoint` que só existia
porque alguém editou o JSON à mão depois de uma aprovação na conversa — a
CLI não tinha nenhum comando para registrar nem para verificar a decisão.
Esta fase fecha as três, sempre dentro da régua do projeto (stdlib, sem
rede, sem LLM, falha restritiva na dúvida).

### 1. `reflow/fs.py` — escrita atômica e lock

- `write_json_atomic()` grava num temporário do mesmo diretório
  (`.<nome>.<pid>.tmp`) e troca com `os.replace` — atômico no Windows e no
  POSIX. Se qualquer etapa falhar, o temporário é removido e o arquivo
  anterior fica íntegro; nunca sobra manifesto pela metade (que, em
  `output/` versionado, viraria commit de arquivo truncado). Substitui o
  `_write_json` antigo de `reflow/cli.py` **e** o duplicado em
  `dashboard/pipeline.py` — uma só implementação, não duas.
- `project_lock(out_dir)` trava um arquivo **irmão** do diretório de saída
  (`output/<nome>.lock`) com lock de 1 byte retido pelo sistema
  operacional (`msvcrt.locking` no Windows, `fcntl.flock` no POSIX). O
  lock é liberado pelo SO se o processo morrer — nenhum lock velho trava o
  projeto para sempre, e nenhum lock precisa de limpeza manual. Acima do
  timeout (10 s), `LockError` e nada é escrito.
- **Reentrante no mesmo processo**: `extract_to()` segura o lock para o
  inventário e `_extract_one()` o segura de novo para o manifesto; a
  segunda chamada só cede a vez em vez de se travar. O dashboard
  reaproveita `extract_to()` e ganha o mesmo proteção sem mudar nada.
- O lock fica **fora** do projeto (`output/<nome>.lock`, não
  `output/<nome>/.lock`) para não criar `output/<nome>/` antes da validação
  — o teste que exige "nenhum output parcial para projeto recusado" seguiu
  passando. `/output/*.lock` entrou no `.gitignore`: é artefato de
  execução, não resultado.

### 2. `reflow checkpoint` — decisão humana amarrada ao hash das entradas

Novo subcomando da CLI (`reflow checkpoint <projeto>` com `--status`
(padrão), `--approve`, `--reject` — mutuamente exclusivos):

- **Antes de qualquer coisa**, recalcula o SHA256 de cada entrada de
  `input/<projeto>/` (mesma rotina do `_build_manifest`, agora fatorada em
  `_current_inputs`) e compara com `manifest.inputs`. Diferiu → código 1 e
  nada gravado: a decisão não pode valer sobre entradas que não foram
  extraídas. `--status` também acusa o manifesto velho.
- `--approve`/`--reject` exigem `03-classification/classification.md`
  (só existe decisão a tomar depois da classificação) e `--approve` é
  recusado com veredito `NOT_PAD` — não há conversão para aprovar.
- O objeto gravado em `manifest.checkpoint` carrega `decision`,
  `recorded_at` (UTC ISO), `inputs_fingerprint` (SHA256 canônico da lista
  de entradas) e `classification_sha256` (a classificação usada na
  decisão). A gravação acontece sob o lock do projeto e de forma atômica.
- Reextração regrava o manifesto inteiro → `checkpoint` volta a `null`.
- Atualização (Fase 32): `--status` passou a distinguir um checkpoint **legado** (gravado
  à mão antes deste ADR, sem `inputs_fingerprint`): mostra a data que houver e avisa que
  não há vínculo de hash, sem regravar nada. Um `inputs_fingerprint` que não confere com
  as entradas atuais agora sai com código 1.
  É o vínculo de hash funcionando nos dois sentidos: decisão velha não
  sobrevive a entrada nova, e decisão nova não é possível sem extração
  nova.
- `report.py` ganhou `read_verdict()` (antes `_read_verdict`, privado) —
  o checkpoint reusa o mesmo leitor de frontmatter do relatório em vez de
  reimplementar.

**O que isto não é:** autenticação forte. O JSON não prova *quem* decidiu,
só *o que* estava na mão e se ainda é o que foi extraído. Continua
sendo o analista humano quem decide no checkpoint (AGENTS.md); o comando
só elimina o caminho fraco de "editar o manifesto à mão" e o risco de uma
aprovação sobreviver a uma reextração.

### Mudança de comportamento que pode afetar compatibilidade

- Dois processos escrevendo o mesmo `output/<projeto>/` ao mesmo tempo
  agora esperam até 10 s e depois falham com `LockError` (exit 1) em vez
  de se intercalar. Nenhum teste existente dependia de escrita concorrente.
- `output/<nome>.lock` passa a aparecer (gitignored). `reflow report` só
  olha diretórios, então não entra na tabela.
- Escrever `00-manifest.json` à mão continua possível, mas
  `reflow checkpoint` passa a recusar gravação quando as entradas mudaram —
  a skill `reflow-convert` foi atualizada para apontar o comando.
- As prévias do dashboard (`.dashboard-runs/`) agora também são gravadas
  de forma atômica — efeito colateral benéfico da fatoração, sem mudança
  de formato.

Não corrigido nesta fase (Fase 4, propositalmente fora de escopo):
resiliência de lote (`extract --all` ainda aborta com exceção fora de
`ValueError`), priorização determinística entre JSON e ZIP no A360,
orçamento de entrada na CLI real (hoje só no dashboard) e CI.

## ADR-021 — Fase 4 de segurança: resiliência de lote, escolha A360 explícita e orçamento de entrada na CLI

Fecha os três itens que o ADR-020 deixou registrados como pendentes.
Mesma régua: stdlib, sem rede, falha restritiva na dúvida, e nenhuma
promessa do que não foi testado.

### 1. Resiliência de lote (`extract --all`)

Antes, só `ValueError` era tratado por projeto: qualquer outra exceção
(JSON inesperado, `AttributeError` em estrutura que não é objeto, disco
cheio, `RecursionError` em árvore profunda, `zipfile.BadZipFile`)
abortava **o lote inteiro** e deixava os projetos seguintes sem serem
tentados — um export estragado no começo do alfabeto travava tudo. Agora
`_extract_all()` captura `Exception` por projeto, reporta
`<nome>: extração abortou de forma inesperada: <repr>` em stderr, segue
em frente e imprime o resumo
`lote: 2/3 projeto(s) extraído(s); falharam: <nomes>`, com exit code 1.

- `KeyboardInterrupt`/`SystemExit` não são `Exception`: interromper o lote
  continua funcionando (não engole Ctrl+C).
- Não está sendo escondido erro nenhum: tudo que falha aparece no stderr,
  é citado no resumo e derruba o exit code.

### 2. Escolha A360 explícita e aviso do que não foi lido

Dois problemas de "silêncio" no `extractors/a360.py`:

- **Vários `.zip` no topo do projeto**: antes pegava `sorted(...)[0]`,
  ou seja, escolhia o export pelo nome em ordem alfabética, sem dizer
  nada — era possível extrair o robô errado e nem perceber. Agora é
  `ValueError` citando todos os nomes e pedindo um export por projeto.
  Restritivo de propósito: não existe critério determinístico honesto para
  saber qual de dois exports é o certo.
- **Arquivo que a extração não lê**: a leitura continua sendo só
  `*.json` **no topo** do diretório (JSON aninhado, `.zip` e o mais
  entram no inventário como arquivo, mas não viram fato). Isso não mudou —
  o que mudou é que agora o extractor imprime em stderr
  `aviso A360: N arquivo(s) fora da leitura em <dir>: <nomes>` (até 5
  nomes). Um inventário que parece completo mas deixou algo de fora é
  pior que um aviso.

Decisão deliberada: **não** ampliamos a leitura para JSON aninhado sem uma
fixture real que mostre como o A360 exporta subpastas — inventaria fato de
arquivo errado com a mesma facilidade. Se um export real mostrar estrutura
aninhada, é isso que muda, com fixture e golden novos.

### 3. Orçamento de entrada na CLI real (`reflow/limits.py`)

O diagnóstico apontava `read_bytes()` sem teto nenhum: extractor e hash do
manifesto liam cada arquivo em memória e somavam tudo, sem limite. Novo
módulo `reflow/limits.py` com `check_input_budget()`:

| Teto | Valor | Por quê |
| --- | --- | --- |
| `MAX_INPUT_FILE_COUNT` | 5000 | export A360 legítimo está muito abaixo |
| `MAX_INPUT_DEPTH` | 30 | profundidade absurda = erro/ataque |
| `MAX_INPUT_TOTAL_BYTES` | 512 MB | `read_bytes` por arquivo somado |
| `MAX_INPUT_FILE_BYTES` | 64 MB | arquivo único já lido inteiro em memória |

- Mede só metadados (`stat`), nunca lê conteúdo; roda **depois** de
  `reject_unsafe_links()` — decide *quanto* ler, não *o que* é seguro.
- Chamado em `extract_to()` (antes de qualquer extração, CLI e dashboard)
  e em `_current_inputs()` (manifesto e `checkpoint`).
- Os valores são lidos dos nomes do módulo em tempo de chamada, então
  teste nenhum precisa criar arquivo de 64 MB para rebaixar o teto.
- O `dashboard/` mantém o orçamento próprio mais apertado (500/12/20 MB,
  ADR-019) porque é smoke test local — roda antes deste aqui. Duas
  camadas, não duplicação de regra.

### Mudança de comportamento que pode afetar compatibilidade

- `extract --all` com projeto quebrado agora **termina** (exit 1, com
  resumo) em vez de levantar traceback no meio — projetos seguintes passam
  a ser extraídos.
- Projeto A360 com dois `.zip` no topo passa a ser recusado em vez de
  extrair o primeiro; com arquivo não-lido no topo, passa a ter aviso em
  stderr (os testes existentes usam fixtures planas, então nada quebrou).
- Projeto acima de 5000 arquivos / 30 níveis / 64 MB por arquivo / 512 MB
  no total é recusado pela CLI (antes era lido inteiro). Os tetos altos de
  propósito: nenhum projeto existente chega perto.

Não corrigido nesta fase (seguem abertos, ver `SECURITY.md`): CI em
`.github/workflows`, POST sem deadline de leitura no dashboard, e tudo que
depende de execução real no PAD.

## ADR-022 — CI versionada: os mesmos gates do hook local, espelhados no GitHub

O diagnóstico de 24/10 apontava que os gates existiam só localmente (hook
`.githooks/pre-commit`, que só roda se alguém lembrar de configurar
`core.hooksPath`). `.github/workflows/ci.yml` espelha essa linha no GitHub.

### O que a CI roda

| Job | Runner | Comandos |
| --- | --- | --- |
| `checks` (matriz: ubuntu-latest + windows-latest × Python 3.12 + 3.14) | Linux e Windows | `uv sync --frozen` → `ruff check .` → `ruff format --check .` → `python -m pytest` (suíte inteira) → `reflow scan` → `reflow lint-robin --all` |
| `frontend` | ubuntu-latest | `node --test tests/frontend/dashboard.test.cjs` |

### Decisões

- **Matriz com os dois sistemas**: Linux cobre o caminho POSIX do lock
  (`fcntl` em `reflow/fs.py`) e Windows é a plataforma-alvo real (PAD,
  `msvcrt.locking`, junction via `mklink /J`). Os testes de link usam o
  helper compartilhado `tests/link_support.py` — junction no Windows,
  **symlink** em POSIX — porque o `cmd /c mklink` embutido em três
  arquivos faria os testes falharem (não pularem) em Linux. Python 3.12 é
  o piso declarado em `requires-python`; 3.14 é o que a máquina de
  desenvolvimento usa.
- **Action `setup-uv` travada no SHA**: `astral-sh/setup-uv` **não
  publica tag major** (`refs/tags/v10` não existe; só `v10.x.y`), então
  `@v10` derruba os jobs no "Set up job" com `Unable to resolve action`.
  O ref é o SHA exato da v10.3.2 com o comentário da versão ao lado —
  tag inexistente não pode ser ref, e SHA travado é também a prática segura
  de supply chain. Antes de usar, os inputs (`python-version`,
  `enable-cache`, `cache-dependency-glob`) foram conferidos no `action.yml`
  daquela tag exata.
- **`scan`, não `scan --staged`**: o `scan_staged()` lê o índice Git
  (`git show :<path>`), que um checkout da CI não tem — rodaria vazio e
  daria falso senso de cobertura. O gate equivalente é o `scan` da working
  tree completa. O `--staged` segue sendo exclusivo do pre-commit local.
- **`uv sync --frozen`**: usa o `uv.lock` como está, sem reescrever nada —
  CI nunca altera artefato versionado. (`--locked` falharia se o lock
  estivesse defasado; escolhido `--frozen` para o CI não depender de
  resolução de rede além da instalação em si.)
- **Permissões mínimas**: `permissions: contents: read`. Nenhum secret é
  usado; nenhuma action de terceiros além das oficiais da GitHub
  (`checkout`, `setup-node`) e da Astral (`setup-uv`) — nada de actions de
  comunidade com permissão de escrita.
- **`fail-fast: false`**: os 4 jobs da matriz rodam todos, mesmo um
  falhando — a matriz serve justamente para comparar comportamento entre
  SO/versão, e falhar no primeiro esconde a comparação.
- **Triggers**: `push` em `main`, `pull_request` e `workflow_dispatch`
  manual. `concurrency` por ref cancelando execução anterior (commit novo
  no PR não precisa das duas rodando).

### A primeira execução real falhou (run 1) e foi corrigida na run 2

Como avisei acima, o workflow só executa de verdade no GitHub — e ele
falhou na run 1 em 8 segundos. O log (`gh run view --log-failed`) deu a
causa exata:

```
##[error]Unable to resolve action `astral-sh/setup-uv@v10`,
         unable to find version `v10`
```

Ação corrigida no commit `f712898`, **antes de qualquer análise de
código**: ref travado no SHA exato da v10.3.2
(`07a047e608db84b3d8c06cd9a7c7dcc9c355c18e`, tag apontando direto para o
commit, portanto seguro de fixar) com o comentário da versão ao lado. Os
inputs usados (`python-version`, `enable-cache`, `cache-dependency-glob`)
foram conferidos no `action.yml` daquela tag exata, em vez de adivinhar
de novo.

Run 2 (`40365830911`): **success**, 5/5 jobs — verde desde 26/10/2026.

### O que a CI **não** é

- Não executa legado, não chama LLM e não tem segredo algum — só os gates
  determinísticos.
- **CI verde não significa nada validado no PAD**: a whitelist de ações
  Robin segue 100% `[não validado]` até alguém rodar um `Main.robin` de
  verdade. Isso continua fora do repositório.
- A suíte roda em Linux, mas o alvo de migração é Windows; a CI cobre
  comportamento do Python, não do Power Automate.

## ADR-023: descarte do corpo antes de rejeitar POST no dashboard

**Data:** 2026-10-26 · **Status:** aceito

### Problema

`test_dashboard.py::test_invalid_origin_...` caía de forma intermitente com
`ConnectionAbortedError` no primeiro request — só em execução de suíte
completa, nunca isolado. Com CI a cada push, isso virava vermelha aleatória.

### Causa raiz

O `http.client` envia cabeçalho e corpo em **dois `send()`** distintos. O
`do_POST` rejeitava (403 sem token, 400 com corpo inválido) escrevendo a
resposta **sem nunca ler o corpo**. Quando o corpo chegava depois de o
handler já ter lido os cabeçalhos, ele respondia e fechava o socket com bytes
não lidos no buffer de recepção — o Winsock responde **RST** a um envio que
bate em socket fechado, e o RST destrói a resposta que já estava em trânsito:

- o cliente via `ConnectionAbortedError` no `getresponse()`;
- o servidor via `WinError 10053` no próprio `wfile.write`.

A carga é o que atrasa o corpo entre os dois `send()` — por isso o flake só
aparecia em suíte completa.

### Evidência da reprodução

Medido com socket bruto, variando o atraso entre o cabeçalho e o corpo, com o
servidor **sem** o fix:

| Atraso do corpo | Resultado (40 tentativas cada) |
| --- | --- |
| 0 ms | FIN 40/40 |
| 2 ms | **RST 40/40** |
| 10 ms | **RST 40/40** |
| 50 ms | **RST 40/40** |

Com o fix: **FIN 40/40 em todos os atrasos**; 400 POSTs sob 22 threads de
carga e 300 POSTs com a suíte completa em paralelo, sem exceção alguma no
servidor.

### Decisão

`Handler._drain_body()` consome o corpo (teto `MAX_BODY_BYTES`, 4096, o mesmo
do corpo aceito; timeout de 1 s) **antes** de escrever a resposta de
rejeição. Chamado nos dois caminhos que respondem sem ler: falha de
token/origin/host e corpo inválido.

- **Teto e timeout são obrigatorios**: um `Content-Length` mentiroso não pode
  prender a thread do handler. Isso **não** resolve a pendência do `POST` sem
  deadline de leitura (ADR-021) — só evita repetir, nesta leitura nova, a
  mesma fraqueza. *Fechada depois no ADR-024.*
- **Corpo acima do teto**: sobra byte no socket mesmo depois do descarte, então
  a conexão é marcada `close_connection = True` — nunca reutilizar. Só atinge
  quem já mentiu no tamanho.
- **Sem corpo não se toca no socket**: o descarte é no-op para requisições
  sem `Content-Length`, então o GET segue intacto.

### Cobertura

A corrida está fixada **deterministicamente** no teste de integração
`test_rejected_post_whose_body_arrives_late_still_gets_its_403`, que envia
cabeçalho, espera 10 ms e só então manda o corpo — sem o fix ele falha com o
mesmo `WinError 10053` do flake original. O call site tem teste com spy, e a
lógica em si tem 5 testes unitários sem rede. O teste de socket bruto com
corpo junto continua cobrindo o caminho normal.

### O que não se fez

Não se mexeu no `Content-Length` mentiroso além do teto, não se adicionou
keep-alive ao dashboard e não se alterou o deadline de leitura do `POST`
(ADR-021 segue aberto) — os três passaram a ser endereçados depois: o prazo
fechou no ADR-024.

## ADR-024: prazo de leitura por requisição no dashboard, usando o hook do stdlib

A pendência mais antiga da lista de segurança (aberta desde o ADR-021, Fase 4)
era o `POST` sem deadline de leitura: `dashboard/server.py` fazia
`self.rfile.read(length)` num socket **bloqueante por padrão**. Um cliente que
mandasse os cabeçalhos com `Content-Length` e nunca mandasse o corpo prendia a
thread do handler para sempre. Como o servidor é um `ThreadingHTTPServer`, cada
conexão dessas vaza uma thread — não trava o dashboard na hora, mas o esgota.

O mesmo valia para quem conectava e nem mandava a linha de requisição: o
`self.rfile.readline()` do `handle_one_request` também bloqueava sem prazo.

### Por que um atributo de classe e não um `settimeout` manual

A investigação mostrou que **o stdlib já tem os dois lados do mecanismo** e que
só faltava ligá-los:

- `socketserver.StreamRequestHandler.setup()` aplica `self.timeout` ao socket
  quando ele não é `None`. `BaseHTTPRequestHandler` herda `timeout = None`,
  ou seja: sem prazo, sempre — é exatamente a lacuna.
- `BaseHTTPRequestHandler.handle_one_request()` já captura `TimeoutError`,
  marca `close_connection` e devolve sem traceback. Não há nada a inventar do
  lado do erro.

Então a peça que faltava é uma linha de classe, não uma implementação própria:
`Handler.timeout = READ_TIMEOUT_SECONDS` (10 s). Ela cobre de uma vez a linha
de requisição, os cabeçalhos e o corpo, porque os três leem do mesmo socket.
10 s é o mesmo número que o código do SSE já usava, e folga de ordens de
grandeza sobre qualquer requisição legítima em loopback.

### O ramo `except TimeoutError` do `do_POST`

Com prazo no socket, um corpo que nunca chega levanta `TimeoutError` lá dentro
— e `TimeoutError` é subclasse de `OSError`, então cairia no
`except (ValueError, OSError)` que respondia **400 "Seleção ou corpo
inválido"**, mentindo sobre o que aconteceu. Verificado: com o `server.py`
anterior e um prazo artificialmente curto, o teste novo recebia
`HTTP/1.0 400 Bad Request`, não um travamento.

O ramo novo vem **antes** do genérico e responde **408 Request Timeout**. Antes
de escrever, ele drena o corpo (`_drain_body`): fechar com o corpo parcial no
buffer de recepção faz o Winsock responder RST, que destrói a resposta que está
a caminho — é a mesma falha medida no ADR-023, aqui em outro caminho. O custo é
até 1 s extra de thread num cliente já morto, o que é irrelevante perto dos 10 s
que ele já gastou.

### O bug que a Fase 18 introduziu e só apareceu agora

O `_drain_body` da Fase 18 terminava com `self.connection.settimeout(None)`
no `finally`. Isso era inofensivo quando nenhum outro prazo existia, mas com
este ADR passa a ser o oposto do objetivo: `None` é **socket bloqueante sem
deadline**, então o descarte anularia o prazo da requisição no meio do caminho
e deixaria a leitura seguinte exatamente como ADR-021 descrevia. Corrigido para
devolver o valor que `gettimeout()` devolveu antes — nunca `None`.

O `_drain_body` também ganhou constante própria (`DRAIN_TIMEOUT_SECONDS`,
igual ao 1 s de antes) e o `settimeout(10)` literal do SSE passou a referenciar
`READ_TIMEOUT_SECONDS`, para não existirem dois "10" soltos.

### Cobertura

Quatro testes novos, todos verificados **falhando sem o fix**:

- `test_post_body_that_never_arrives_gets_408_not_a_hung_thread`: socket bruto
  manda linha, cabeçalhos e token válidos, `Content-Length: 32` e nenhum byte
  de corpo. Sem o ramo novo: 400 (medi). Com ele: 408 e `recv` devolvendo
  `b""` — fechar é o que prova que a thread foi liberada, já que o
  `ThreadingHTTPServer` atende a conexão seguinte em thread nova mesmo com a
  antiga presa.
- `test_idle_connection_is_dropped_by_the_read_deadline`: conexão que não manda
  nada é fechada pelo prazo. O `require` do `Handler.timeout` vem **antes**
  do `monkeypatch`, de propósito: a primeira versão encurtava o prazo primeiro,
  e isso criava o próprio atributo que o stdlib lê — o teste passava sem o fix.
  Medido e corrigido; agora ele falha com `veio None`.
- `test_handler_carries_a_read_deadline_on_every_request` e
  `test_drain_restores_the_deadline_it_found_not_none` (mais as demais do
  descarte, atualizadas): fixam o valor de fábrica e a restauração do prazo,
  sem rede.

`pytest` → **211 passed** (eram 207). `ruff check`/`format --check`,
`reflow scan`, `reflow lint-robin --all` e `node --test` → ok.

### O que não se fez

- **Não se escolheu o prazo por medição**: 10 s é o número que o SSE já usava,
  folgado para loopback, não um valor calibrado. Se um dia o dashboard precisar
  de upload de arquivo grande, isso muda.
- O 408 drena antes de responder, e drenar um cliente morto custa 1 s extra. É
  deliberado: a alternativa é perder a resposta no RST.
- Continua valendo tudo o que depende de execução real no PAD — este ADR não
  toca em Robin.

## ADR-025: terceiro status na whitelist Robin — `[proposto]`, sintaxe real de evidência pública, nunca inventada

Pedido do usuário: o `Main.robin` gerado trazia só placeholders
(`[não validado — TODO reflow: colar aqui o texto copiado do designer do
PAD]`) para toda ação — nunca sintaxe real — e isso fazia qualquer coisa
colada no PAD virar "Ação Desconhecida". Pediu que colar do `Main.robin`
gere ação válida de verdade. Regra do projeto segue de pé: nunca inventar
sintaxe Robin, mesmo que pareça óbvia (`AGENTS.md`).

### Por que não era só "chutar com mais confiança"

A primeira tentativa de resolver isso sem pesquisa real teria sido chutar a
sintaxe copiada do PAD a partir de conhecimento genérico — exatamente o que
`AGENTS.md` proíbe. Antes de escrever qualquer coisa, fiz pesquisa real na
web (pedido explícito do usuário) e encontrei:

1. A documentação oficial da Microsoft confirma que colar/copiar ações como
   texto é um recurso real do Power Automate Desktop, mas avisa que é
   **schema interno versionado** — pode mudar entre versões do PAD. Isso
   confirma que chutar tem risco real, não é só cautela excessiva do
   projeto.
2. Achei um repositório público real
   (`AgniusBartninkas/power-automate-desktop-framework`, licença aberta,
   pasta `src/flows/*/source/*.txt`) com **flows PAD reais, versionados como
   texto puro** — não é documentação, é o conteúdo literal que sai ao copiar
   do designer, usado em produção por outra equipe. O próprio README desse
   repositório confirma o mesmo risco que o item 1: "most actions will still
   be accepted anyway, especially simple actions, such as Set variable, Run
   subflow, etc., while more recent actions or actions with more custom
   attributes may not be allowed."
3. Cruzei a sintaxe desses arquivos reais com a documentação oficial de
   parâmetros de cada ação (Variables, Conditionals, Loops, Flow control,
   Excel) — os nomes de parâmetro batem entre as duas fontes independentes.

### A decisão

`reference/robin-actions.md` ganha um terceiro status, entre os dois que já
existiam:

- `[não validado]` — nada tentado ainda; placeholder genérico continua.
- **`[proposto — baseado em evidência pública, não testado nesta
  instalação]`** (novo) — sintaxe real, copiada de flows PAD públicos
  reais e cruzada com a documentação oficial de parâmetros, mas **ninguém
  rodou isso neste PAD especificamente**. Nunca inventada: toda entrada
  nesse status cita a evidência (arquivo do repositório público + página da
  documentação oficial).
- `[validado PAD: rodou]` — inalterado: só depois de alguém montar a ação
  de verdade no designer local e confirmar que funciona.

Só entraram no novo status as ações com evidência real e direta: variável
(`SET var TO valor`), condicional (`IF cond THEN ... [ELSE ...] END`),
laços (`LOOP FROM n TO m STEP k ... END`, `LOOP FOREACH var IN lista ...
END`, `LOOP WHILE (cond) ... END`), chamada de subflow (`CALL NomeDoSubflow`
— achado importante: **não** é um padrão `Flow.RunSubflow Param: valor`, é
uma palavra-chave própria) e quatro ações de Excel (`LaunchExcel`,
`ReadFromExcel.ReadAllCells`, `SetActiveWorksheet`, `CloseExcel`). Ações sem
evidência direta (Browser.*, UI.*, File.*, Web.InvokeRestApi,
Web.InvokeSoapService, Text.Concatenate, Credentials.GetCredential,
FlowControl.Region) continuam `[não validado]` — nenhuma foi promovida sem
base real, mesmo as mais "óbvias".

### Consequência para a conversão

O `reflow-pad-converter` passa a copiar o snippet **real** de uma entrada
`proposto` (substituindo nome de variável/parâmetro pelos nomes do próprio
flow, convenção `step_`/`in_`/`out_`/`cfg_`) em vez do placeholder — mas o
comentário acima do passo continua avisando que é sintaxe `proposto`, nunca
tratada como certeza. Isso resolve a queixa de formatação (ação deixa de
ser texto solto, vira sintaxe PAD real), mas **não resolve sozinho** o
pedido de puxar o nome exato da variável declarada no A360 — isso segue
bloqueado por um gap separado na extração (nenhum campo de variável de
saída é capturado hoje do A360; ver nota do Basic Memory desta mesma
sessão).

### O que isto não faz

- Não promove nenhuma ação para `[validado PAD: rodou]` — essa barra
  continua exigindo execução real neste ambiente.
- Não cobre as oito ações sem evidência direta listadas acima; permanecem
  honestamente `[não validado]`.
- Não resolve a variante de `Excel.ReadFromExcel` para leitura de um
  **intervalo específico** de células (`range`, caso do A360 `Excel.read`)
  — só tenho evidência direta do sub-nome de ação para "ler tudo"
  (`ReadAllCells`); o sub-nome exato para intervalo fica como lacuna restante.

## ADR-026: CD visual para o GitHub Pages — Actions em vez do modo legado, com painel ao vivo no próprio dashboard

Pedido do usuário: uma pipeline de CI/CD no GitHub Actions para acompanhar
visualmente as etapas de implantação. Confirmado com ele antes de
implementar: este projeto **não tem produção** no sentido tradicional — é
um CLI local (`reflow`) e um dashboard de teste só em loopback
(`dashboard/`, nunca implantado em lugar nenhum). O único "deploy" real
que existe é a publicação do `docs/` (dashboard da memória) no GitHub
Pages. O usuário confirmou esse escopo ("deploy local e não em produção")
e pediu, além da pipeline, um painel visual **dentro do próprio
dashboard**, mostrando o que foi implantado a cada nova funcionalidade.

### O que foi encontrado antes de implementar

`gh api repos/.../pages` mostrou `build_type: "legacy"` — o Pages publicava
direto da branch `main`/`docs` sem nenhuma execução do Actions associada.
Era literalmente impossível acompanhar visualmente esse deploy porque não
existia pipeline nenhuma rodando: o GitHub publicava silenciosamente a
cada push que tocasse `docs/`.

### A decisão

1. **Migrar o Pages do modo legado para o modo Actions**
   (`gh api -X PUT repos/.../pages -f build_type=workflow`) — mesma URL
   pública, só muda o mecanismo de publicação.
2. **Job `deploy` novo em `.github/workflows/ci.yml`**, com
   `needs: [checks, frontend]` e `if: push na main` — nunca roda em pull
   request de fora. Isso faz o Actions desenhar a pipeline inteira num
   grafo visual único: **checks (matriz 2 SO × 2 Python) → frontend →
   deploy**. Grupo de concorrência próprio (`pages`, `cancel-in-progress:
   false`) para nunca cancelar um deploy em andamento — enfileira o
   próximo em vez de derrubar o que está publicando.
3. **Painel "Pipeline do reflow" dentro de `docs/index.html`** — não
   bastava a pipeline existir no Actions, o pedido era vê-la **no próprio
   dashboard**. O painel busca ao vivo, direto do navegador, a API pública
   do GitHub (`api.github.com/repos/.../actions/workflows/ci.yml/runs` +
   `.../jobs`, sem autenticação, só leitura) e desenha os três estágios
   agrupando os jobs da matriz (`checks (ubuntu-latest, py3.12)` etc. viram
   um card `checks` só, com contagem `N/M jobs`). Nunca simula sucesso: se
   a API falhar ou o limite de 60 req/h sem autenticação estourar, mostra o
   erro em texto, com link direto para o Actions.

### Bug real pego no caminho: falso positivo no próprio scanner de segredo

Ao commitar `id-token: write` (permissão OIDC exigida pelo
`actions/deploy-pages`), `reflow scan` reprovou — "token" é palavra
sensível reconhecida por `SECRET_KEY_RE`, e "write" não estava no
vocabulário de valores-placeholder. Isso bloquearia **todo** workflow do
GitHub Actions que use OIDC (um padrão comum e documentado, não um caso
exótico). Corrigido adicionando `read`/`write`/`none` a
`PLACEHOLDER_VALUES` em `reflow/security/masking.py` — vocabulário
fechado e documentado pelo próprio GitHub para o bloco `permissions:`,
nunca um segredo real. Dois testes novos: um confirma que
`id-token: write`/`contents: read`/`pages: write` não reprovam mais o
scan; outro confirma que um valor de token de verdade (`ghp_...`) continua
reprovando — a correção não destampou a detecção real.

### O que esta decisão não fez

- Não criou nenhuma "produção" fictícia — o painel e a pipeline cobrem
  exatamente o único artefato publicado que este projeto tem (`docs/`).
- O painel no dashboard não tem suíte de teste própria — `docs/index.html`
  nunca teve (`tests/frontend/dashboard.test.cjs` cobre `dashboard/app.js`,
  um arquivo diferente); validado manualmente servindo `docs/` localmente
  e conferindo no navegador contra a API real do GitHub Actions.
- A API pública do GitHub tem limite de 60 requisições/hora por IP sem
  autenticação — em uso normal (uma pessoa olhando o dashboard de vez em
  quando) isso nunca é um problema, mas não há cache nem backoff além da
  mensagem de erro explícita.

## ADR-027: primeiras 4 ações promovidas a `[validado PAD: rodou]` + raiz do bug de crase no scanner, corrigida de vez

O usuário colou um "Guia de equivalência" com 4 ações PAD reais (Iniciar
Excel, Ler da Planilha, Ler texto do arquivo, Executar VBScript), cada uma
com o código Robin e o equivalente AA360 de origem. Perguntei antes de
promover qualquer coisa: essas ações foram montadas e **rodadas de
verdade** no designer do PAD, ou é material de referência ainda não
executado aqui? O usuário confirmou: **rodou e validou no PAD** — a barra
mais alta da whitelist (ver ADR-025).

### O que foi promovido

Em `reference/robin-actions.md`, todas de `[não validado]`/`[proposto]`
direto para `[validado PAD: rodou]`, com o snippet real dado pelo
usuário (nomes de variável de exemplo trocados pela convenção `cfg_`/
`in_`/`out_` deste repositório, conforme a regra de
`robin-conventions.md`):

- `Excel.LaunchExcel` — era `[proposto]` (evidência pública), agora
  `[validado PAD: rodou]`.
- `Excel.ReadFromWorksheet` — reestruturado em três variantes com
  confiança diferente, porque o snippet validado (`ReadCell`, célula
  única) não é a mesma sub-ação da variante `[proposto]` já documentada
  (`ReadAllCells`, planilha inteira) nem cobre a lacuna de "intervalo
  específico" que ainda falta. O parser de `robin-actions.md`
  (`_STATUS_LINE_RE`) só aceita um `Status:` por cabeçalho `###`, então o
  status do topo reflete o snippet principal (agora a variante validada),
  e cada variante secundária cita o próprio nível de confiança no corpo.
- `File.ReadTextFromFile` — era `[não validado]`, agora `[validado PAD:
  rodou]`.
- `Scripting.RunVBScript` (módulo novo) — ação que não existia na
  whitelist; A360 "VBScript: Abrir" não tinha equivalente mapeado ainda.

`reference/a360-to-pad.md` ganhou observações nas linhas afetadas, **sem
mudar o status delas** — o `packageName`/`commandName` real do A360 (ex.:
se o pacote é literalmente "Excel" ou "Excel avançado") não foi confirmado
por uma extração de verdade, só o rótulo da UI que o usuário citou. Deixei
essa distinção explícita: a ação PAD está validada, a identificação exata
do campo de origem no export A360 ainda não.

### Bug pego ao escrever a documentação: a terceira vez do mesmo erro

Ao escrever a observação sobre o bug do ADR-026 (`id-token: write`
reprovando o scanner), a prosa em Markdown — `` `id-token: write` (permissão
OIDC) `` — reprovou o próprio `reflow scan`, de novo. A crase de fechamento
do span de código, colada direto em "write" sem espaço, fazia o valor
capturado pela regex ser "write\`" (com a crase), nunca igual a "write"
sozinho — driblando a correção do ADR-026 (que só reconhece o literal
exato "write"). Essa já era a terceira vez no mesmo dia que esse padrão
mordia (comentário de código, nota do Basic Memory, agora a própria
documentação) — sinal de que o problema era a regex, não o texto.

Corrigido na raiz: `SECRET_ASSIGNMENT_RE` em
`reflow/security/masking.py` passou a tratar a crase (`` ` ``) como mais
um caractere de parada do valor, igual já fazia com aspas — crase nunca é
delimitador de string em nenhuma linguagem que o scanner varre (Python,
JSON, YAML, `.env`), então excluí-la do valor nunca perde a detecção de um
segredo real. Dois testes novos provam os dois lados: uma menção em
Markdown como `` `id-token: write` (permissão OIDC) `` não reprova mais, e
um valor de token de verdade citado do mesmo jeito continua reprovando.

### Teste reescrito

`tests/unit/test_whitelist.py::test_no_action_is_presumed_validated_without_a_real_pad_run`
assumia que **nenhuma** ação da whitelist jamais estaria validada — verdade
até este ADR, mas deixou de ser uma invariante válida do projeto a partir
daqui. Substituído por
`test_validated_actions_have_a_real_snippet_not_the_generic_placeholder`,
que verifica uma invariante mais forte e ainda válida: toda ação
`[validado PAD: rodou]` tem, de fato, um snippet real no lugar do
placeholder genérico — pega o caso real de alguém trocar só a linha de
`Status:` sem trocar o conteúdo.

### O que esta decisão não fez

- Não promoveu nenhuma ação por semelhança — só as 4 que o usuário
  confirmou ter rodado.
- Não mudou o status das linhas de `a360-to-pad.md` ligadas a essas ações
  — o lado da identificação do A360 real segue `não validado`,
  deliberadamente, até uma extração real confirmar os nomes de campo.
- Não resolve a lacuna de "intervalo específico" do `Excel.ReadFromWorksheet`
  nem o nome exato do `packageName`/`commandName` do VBScript no A360 —
  seguem abertos, documentados nos próprios arquivos.

## ADR-028: checkpoint de `a360-excel-vault` aprovado só para a parte confirmada (Excel + REST + CredentialVault)

`a360-excel-vault` estava parado em `03-classification` desde a extração
original: veredito `PARTIAL` gravado, mas sem a segunda opinião que o
pipeline (`AGENTS.md`) exige antes do checkpoint humano. Rodei
`reflow-classify-review` (agent `reflow-classification-reviewer`) para
reclassificar o projeto do zero, sem ler `classification.md` antes de
concluir o próprio veredito.

### Resultado da segunda opinião

`output/a360-excel-vault/03-classification/review.md`:
`original_verdict: PARTIAL`, `reviewed_verdict: PARTIAL`,
`agreement: concorda`. A mesma lógica nas duas análises independentes: a
parte confirmada do fluxo (`Excel/open`, `Excel/read`, `REST/post`,
`CredentialVault/get`) não atende nenhum critério C1–C5 (sem
`ui_interactions`) e atende fortemente N1/N4 (já usa API REST existente +
padrão ETL puro) — isoladamente apontaria `NOT_PAD`. Mas os dois comandos
não reconhecidos na extração (`CustomPackage/transform`,
`Browser/unmappedAction`) são incerteza genuína, sem evidência de UI nem de
ETL, o que aciona a regra da rubrica "na dúvida entre `PARTIAL` e
`NOT_PAD`, escolha `PARTIAL`" (`reference/classification-rubric.md:9`).

### Decisão do checkpoint

Classificação com segunda opinião concordante foi para o analista (o
usuário), que decidiu: **aprovar apenas a parte confirmada** do fluxo
(`Excel/open` → `Excel/read` → `REST/post` com `CredentialVault/get`) para
seguir à conversão PAD, pela regra KISS de não fragmentar o projeto em
dois sub-fluxos — mesmo essa parte, isolada, apontando estatisticamente
para `NOT_PAD` por N1/N4. Os dois comandos não reconhecidos
(`CustomPackage/transform`, `Browser/unmappedAction`) **ficam de fora**
da conversão até alguém confirmar, com evidência real (consulta a
`reference/robin-actions.md` ou nova extração), se representam interação
de UI ou só mais uma etapa de transformação/integração.

`reflow checkpoint a360-excel-vault --approve` grava a aprovação no
manifesto (`checkpoint.decision: "approved"`, vinculado por hash a
`classification.md` e às entradas atuais de `input/a360-excel-vault/`,
conforme ADR-020). O CLI atual não tem campo de "escopo parcial" no
manifesto — por isso esse recorte (o que exatamente foi aprovado, e o que
ficou de fora) está registrado aqui e em `docs/historico.md`, não só no
JSON.

### O que esta decisão não fez

- Não aprovou `CustomPackage/transform` nem `Browser/unmappedAction` para
  conversão — seguem fora do escopo do PAD até confirmação real.
- Não alterou `classification.md` nem o veredito `PARTIAL` do projeto —
  só o `checkpoint` no manifesto mudou.
- Não gerou nenhum `Main.robin` ainda — a conversão em si
  (`reflow-pad-converter`) é o próximo passo, de posse desta aprovação.

## ADR-029: PAD Robin Action KB vendorizada como base de sintaxe (fase 1 de 5)

Pedido do usuário: usar a [PAD Robin Action KB](https://github.com/joeG592/pad-robin-action-kb)
(Joe Green, CC BY 4.0) para dar robustez ao reflow. A KB tem 1.086 ações Robin, cada uma com um
exemplo que colou no PAD Designer 2.73 sem erro, parâmetros tipados, seletores irmãos e
`error_handling`, mais 24 regras de sintaxe provadas por 456 colagens de teste.

### O que a KB revelou sobre o estado atual

- O `Main.robin` de `a360-excel-vault` não cola: usa comentários `//` e linhas `cfg_x: "..."`.
  Robin só aceita `#` e `SET x TO ...`, e uma linha inválida faz o PAD descartar a colagem
  inteira, sem erro visível.
- Os snippets `proposto` de `ReadAllCells` e `CloseExcel.Close` usam `Instance: %var%`. A regra
  3 da KB diz que `%...%` fora de string derruba a colagem; o certo é `Instance: var`.
- Sete nomes da whitelist não existem no PAD: `Browser.*`, `UI.*`, `Web.InvokeRestApi`,
  `Text.Concatenate`, `Credentials.GetCredential`, `Flow.RunSubflow` (`CALL`) e
  `FlowControl.Region` (`**REGION`).
- As 4 ações `[validado PAD: rodou]` (ADR-027) batem com a KB.

### Decisões do usuário (2026-11-04)

1. Ação ancorada na KB ganha um **status próprio**, acima de `proposto` e abaixo de
   `[validado PAD: rodou]`: o PAD do autor aceitou a sintaxe, mas ninguém rodou neste ambiente.
2. O **ADR-012 será revogado** na fase 3: `lint-robin` passa a interpretar a sintaxe Robin com
   base nas regras da KB e reprova de forma restritiva (gate de commit).

### Fase 1 (esta): cópia vendorizada com proveniência

- `reference/vendor/pad-robin-kb/`: 6 arquivos do upstream, sem edição (ActionKB,
  TypeReference, `robin-rules.json`, `probe-corpus.json`, `PROMPT.md`, `LICENSE`), mais
  `manifest.json` (repo, tag `v3.8.0`, commit, sha256 de cada arquivo) e `README.md` com a
  atribuição exigida pela CC BY. Edição Power Fx fora: o reflow gera Robin clássico.
- `.gitattributes`: `-text` na pasta, para o checkout não trocar EOL e quebrar o hash.
- `reflow/robin/kb.py`: loader só de JSON e `verify_kb` (arquivo ausente, extra, fora do
  conjunto fechado ou com hash divergente vira achado).
- `reflow kb verify` (gate novo no pre-commit e na CI) e `reflow kb show <actionId>`.

### Isenção estreita no scan, e por quê

O `reflow scan` reprovava 155 linhas da KB: num argumento de senha seguido de um literal
Robin `$'''...'''`, a regex captura só o `$` como valor. Os arquivos vendorizados são pulados **só enquanto o sha256 bater com o manifesto**;
qualquer edição derruba a isenção. O manifesto não consegue isentar arquivo fora de um conjunto
fechado de 6 nomes, e o `manifest.json` e o `README.md` da pasta são sempre varridos. Testes em
`tests/unit/test_kb.py` cobrem os dois lados.

O mesmo achado mostra uma lacuna real: o scan não entendia literais Robin. Ele acusava o `$`
de qualquer literal num argumento de senha e nunca olhava o conteúdo. Corrigido na fase 5
(`is_safe_assignment` em `reflow/security/masking.py`).

### Fases 2 a 5 (concluídas no mesmo dia)

**2. Whitelist e tabela verdade ancoradas na KB.** Cada cabeçalho de `robin-actions.md` passa
a ser o id Robin real (`Módulo.Ação.Seletor` da KB, ou a instrução da linguagem). Novo status
`[colado KB: PAD 2.73, não rodado nesta instalação]`. Os 4 snippets validados pelo analista
ficaram **intactos**; ao lado de cada um entrou a forma de colagem de uma linha. Nenhuma
colagem do corpus quebra argumentos em linhas, então fica um `TODO reflow (revisão humana)`
para confirmar como eles foram colados. Lacunas fechadas: intervalo do Excel
(`ReadCells`), escrita (`WriteCell`, `WriteText`, `WriteCSV`), REST/SOAP, navegador, janela,
banco. `Credentials.GetCredential` segue `[não validado]`: a KB não tem ação de cofre.
Testes novos reprovam cabeçalho de ação ausente da KB, argumento ou saída fora do seletor
e `%` fora de string em qualquer snippet.

**3. `reflow/robin/syntax.py`.** Implementação própria (não é tradução do `check-flows.js`,
cujo código não tem licença declarada) das regras documentadas em `robin-rules.json`.
Contra as 456 colagens do corpus: 107/107 rejeitadas detectadas, 22/27 com erro detectadas,
316/322 limpas aceitas. As 6 restantes reprovam **por política**, mais estrita que o PAD:
segredo literal em argumento de senha e `\%`, que o PAD cola descartando o `%`. Os três
números são testes (`tests/unit/test_robin_syntax.py`). O lint também cruza as ações **usadas
no texto** com a whitelist. Convenção nova: pendência é comentário `# TODO reflow: ...`
(cola como linha de comentário), nunca placeholder solto. Variáveis `in_` são entradas do
flow, declaradas no designer.

**4. Agents.** Conversor vira "preenchedor de template" (método do `PROMPT.md` da KB),
revisor ganha a checagem semântica contra a KB (seletor certo, fechar o que abre,
tratamento de erro só com erros declarados), tester segue as mesmas regras. Fonte em
`.opencode/agents/`, espelhos regenerados por `sync_agents.py` e `sync_copilot.py`.

**5. Reconversão.** Os 3 `Main.robin` versionados (`a360-excel-vault`, `a360-browser-rest`
e o teste dele) tinham 323 achados no lint novo: o PAD descartaria cada um inteiro. Foram
reconvertidos com o mesmo escopo e as mesmas evidências (ADR-028 respeitado) e passam no
gate. No caminho, o scanner ganhou `is_safe_assignment`: lê o literal Robin em vez do `$`,
e trata variável `cfg_`/`in_`/`out_`/`step_` nua como referência.

### O que isto não faz

- Não promove nenhuma ação a `[validado PAD: rodou]`: colar no PAD do autor da KB não é
  rodar neste ambiente.
- Não altera nenhum snippet validado pelo analista.
- Não valida a semântica do flow: um `Main.robin` que passa no lint cola, mas pode não
  fazer o que o legado fazia. Isso continua com o revisor e com o teste real no PAD.
- O lint não cobre a edição Power Fx (`$fx'...'`): o reflow gera Robin clássico.

## ADR-030: decisões do analista no piloto `a360-excel-vault` e detector de segredo lendo `%expressões%`

A auditoria semântica de 2026-11-05 (`output/a360-excel-vault/04-pad/uc-01-excel-vault/review.md`)
apontou que o piloto reconvertido pelo ADR-029 colava no PAD mas enviava o POST sem
autenticação (R1-1, bloqueante) e deixava outras quatro escolhas sem dono. O analista
(Cleyber, 2026-11-05) decidiu:

| Ponto | Decisão | Efeito no `Main.robin` |
| --- | --- | --- |
| Origem da credencial | variável de entrada sensível do flow | `in_rest_token`, declarada no designer; sem ação de cofre |
| Autenticação do REST | token no cabeçalho | `CustomHeaders` monta `Authorization` com `cfg_rest_auth_scheme` (vazia, TODO) e `in_rest_token`; mesma ação `InvokeWebServicePost` |
| Formato do corpo | confirmar com o analista | `Accept`/`ContentType` viram `cfg_` vazias com TODO; nada de `application/json` sem evidência |
| Fechar o Excel | sim | `Excel.CloseExcel.Close` logo após a leitura; diferença deliberada em relação ao legado |

Atualização (Fase 29, R8-6): `cfg_rest_auth_scheme` foi substituída por `cfg_rest_auth_prefix`,
que guarda o esquema já seguido de espaço; o cabeçalho junta prefixo e token sem espaço entre
as expressões, de modo que prefixo vazio envia o token puro.

A Região da credencial passou a vir antes do REST (o legado tinha a ordem inversa). Os nomes
`step_NN` seguem a ordem do legado para manter o rastreio até `main.json`.

### Detector de segredo

O cabeçalho `Authorization: %cfg_rest_auth_scheme% %in_rest_token%` dentro de um literal
Robin reprovava `reflow scan` e `lint-robin`, porque a regex lia `%cfg_rest_auth_scheme%`
como valor. `is_safe_assignment` agora aceita um valor que começa com `%expressão%` **só se**
tudo até o fim do literal (`'''`) ou do span de código Markdown (crase, mesma regra do
ADR-027) for `%expressões%` e espaço. Texto fixo depois da expressão continua sendo achado
(teste em `tests/unit/test_kb.py`).

### O que isto não faz

- Não preenche nenhuma `cfg_` com valor do legado.
- Não decide o esquema de autorização, o formato do corpo nem o critério de status HTTP:
  ficam como `# TODO reflow` até o analista confirmar.
- Não executa nada no PAD. O flow de teste (`05-test/`) foi gerado com 5 cenários e
  resultado vazio.

## ADR-031: decisões do analista em `a360-browser-rest` (UC-01 mantido no PAD)

**Data:** 2026-11-05. **Status:** aceito.

### Contexto

A auditoria da Fase 30 (`output/a360-browser-rest/04-pad/uc-01-browser-rest/review.md`)
deixou quatro pontos para o analista. Um deles (R8-2) podia tirar o UC-01 do PAD:
`03-classification/classification.md:72-74` manda reavaliar para NOT_PAD se a chamada REST
for independente da sessão do navegador.

### Decisões (Cleyber, 2026-11-05)

| Ponto | Decisão | Efeito no `Main.robin` |
| --- | --- | --- |
| R8-2 sessão web | a API é independente da sessão do navegador | UC-01 continua no PAD; `Web.InvokeWebService.InvokeWebService` sem instância de navegador |
| R1-1 credencial | token no cabeçalho, padrão do ADR-030 | entrada sensível `in_rest_token` + `cfg_rest_auth_prefix` vazia com TODO em `CustomHeaders`; Região da credencial antes do REST |
| R8-3 status HTTP | confirmar com o analista | `# TODO reflow`, sem `ON ERROR` inventado |
| R7-1 formato | `cfg_` vazias com TODO | `cfg_rest_accept`/`cfg_rest_content_type` |

Sem decisão pendente, a mesma rodada também fechou R4-1 (README do flow), R4-2 (variáveis sem
consumidor), R5-1 (sinalização do subfluxo comum `obter-credencial-do-cofre`) e R8-1
(`WebAutomation.CloseWebBrowser` no `step_05_close_browser`, próximo número livre depois dos
passos do legado).

### Consequência registrada (R1-2)

Manter o UC-01 no PAD contraria a recomendação de reavaliação da classificação; esta ADR é o
registro do motivo (decisão do analista). Efeito prático: o `step_01` abre uma página que
nenhum passo lê, fiel ao legado, e mantém a exigência A1 (extensão do PAD no navegador).
Se o analista concluir que a página não tem efeito de negócio, o passo pode sair numa rodada
futura, e a reavaliação para NOT_PAD volta à mesa.

### O que isto não faz

- Não preenche `cfg_` nem `in_` com valor do legado.
- Não altera `classification.md` nem o checkpoint; o checkpoint do projeto é legado (sem
  `recorded_at`/fingerprint) e só quem decide pode regravá-lo pela CLI.
- Não executa nada no PAD.

## ADR-032: `stale_phases` passa a ter ciclo de vida (`reflow phase-done`)

**Data:** 2026-11-05. **Status:** aceito.

### Contexto

`stale_phases` só era escrito pelo `extract`, sempre com as quatro fases, e nenhum comando o
limpava. O orquestrador `reflow` usa o campo para decidir onde retomar ("não reexecute uma
fase cujo artefato existe e não está em `stale_phases`"), então lia toda fase como velha. O
manifesto de `a360-browser-rest` tinha sido corrigido à mão em outubro.

### Decisão

- `extract` marca só as fases que já têm pasta em `output/<projeto>/`. Fase que nunca rodou
  é pendente, não desatualizada.
- Novo `reflow phase-done <projeto> <fase>`: tira a fase da lista e acrescenta as fases
  **seguintes que já existem** (foram geradas da versão anterior). Entradas antigas para
  fases inexistentes caem. Recusa se `input/<projeto>/` mudou desde o `extract` (mesma regra
  do checkpoint) ou se a fase não deixou o artefato mínimo (`02-docs/*.md`,
  `03-classification/classification.md`, `*/Main.robin` em `04-pad`/`05-test`).
- As skills `reflow-document`, `reflow-classify`, `reflow-convert` e `reflow-test` chamam o
  comando ao final (os agents não têm shell). As skills são a fonte única dos três harnesses
  (OpenCode e Copilot só apontam para elas), então a paridade vem junto.

### O que isto não faz

- Não decide se o conteúdo da fase está correto: só registra que ela rodou depois do
  `extract` atual. Revisões (`*-review`) não fecham nem abrem fase.
- Não toca no checkpoint.

## ADR-033: harness próprio `refold` (plano B secundário) na API Anthropic Messages

**Data:** 2026-11-06. **Status:** aceito (sem teste contra a IAra real).

### Contexto

O roadmap da reunião de 16/10 pede o agente próprio evoluindo em paralelo como plano B
(pedido 7). O harness antigo se perdia em repositórios grandes por falta de gestão de
contexto, e o risco principal continua sendo perder o Claude Code no ambiente do banco.
O usuário escolheu o protocolo Anthropic Messages (`POST {IARA_BASE_URL}/messages`),
coerente com o proxy que hoje aponta o Claude Code para a IAra.

### Decisão

- Pacote `refold/` na raiz, irmão de `reflow/` e nunca importado por ele: o núcleo continua
  sem rede e sem LLM (ADR-001). `refold` importa do `reflow` só funções determinísticas
  (máscara, scan, contenção de caminho, CLI de `phase-done`/`lint-robin`). Zero dependência
  nova: HTTP por `urllib` da stdlib.
- Configuração só por ambiente, mesmos nomes do OpenCode: `IARA_BASE_URL` (https; http só
  em loopback), `IARA_API_KEY`, `IARA_MODEL`; opcionais `REFOLD_AUTH` (`x-api-key` ou
  `bearer`) e `REFOLD_MAX_TOKENS`. A chave nunca aparece em `repr`, log ou mensagem de erro.
- Prompts: lidos de `.opencode/agents/*.md`, a mesma fonte que gera Claude e Copilot. O
  refold não tem cópia própria, então a paridade vem de graça. `steps` do agent vira o
  limite de turnos; permissão `allow` diferente de `edit` faz o refold recusar o agent.
- Ferramentas do modelo: `read_file`, `list_files`, `grep`, `write_file`. Leitura só em
  `output/<projeto>/`, `input/<projeto>/` e `reference/`, sem `.env`, `..`, caminho
  absoluto, UNC ou symlink/junction, e todo texto lido passa por `mask()` antes de ir ao
  modelo. Escrita só nos globs `edit: allow` do agent com o `*` de `output/*/` preso ao
  projeto, e o conteúdo passa pelo mesmo `scan_bytes` do pre-commit (achado = recusa).
- Contexto: resultado de ferramenta cortado em 20 mil caracteres (leitura em blocos de 400
  linhas com `offset`); acima de 400 mil caracteres de conversa, os resultados mais antigos
  viram um aviso curto.
- Contrato das skills aplicado em Python (`refold/pipeline.py`), já que o modelo não tem
  shell: pré-condição por agent; entrada alterada desde o `extract` bloqueia qualquer
  agent; o conversor exige checkpoint `approved` **com** `inputs_fingerprint` conferindo
  (checkpoint legado é recusado). Ao terminar: `fix-robin-eol` e `lint-robin` para quem
  gera Robin, depois `phase-done`. Agent que não terminou ou não gravou nada não fecha fase.
- Log por execução em `.refold-runs/` (fora do Git): turnos, ferramenta, caminho, tamanho e
  tokens, nunca conteúdo.

### O que isto não faz

- Não foi testado contra a IAra nem contra a API Anthropic: os testes usam transporte e
  modelo falsos. O formato exato aceito pelo proxy da IAra só se confirma lá dentro.
- Não orquestra o pipeline inteiro (o papel da skill `reflow`): roda um agent por vez.
- Não substitui o checkpoint humano nem grava PASS/FAIL.

## ADR-034: harness de classificação (gate determinístico e golden set)

**Data:** 2026-11-08. **Status:** aceito (medido só no Claude Code, rótulos sem revisão humana).

### Contexto

O veredito decide se um robô vai ou não para o PAD, e até aqui nada conferia a saída do
`reflow-classifier`: `phase-done` só olhava a existência do arquivo, e `checkpoint --approve`
aceitava um stub. Em particular, `report.read_verdict` lê as aspas junto, então
`verdict: "NOT_PAD"` passava pelo bloqueio de `NOT_PAD`. Também não havia como medir se uma
mudança de rubrica, prompt ou modelo piora a classificação.

### Decisão

- `reflow/classification.py` (stdlib, sem LLM): gate de contrato, evidência e coerência com o
  inventário. Erro bloqueia; aviso informa. Fica dentro de `phase-done 03-classification` e
  `checkpoint --approve`, por onde todo harness já passa, sem depender de a skill lembrar.
  `classify-check --all` entra no pre-commit e na CI.
- Evidência em A360 é conferida contra os fatos do inventário, porque a linha é o índice do
  nó. Legado real não é versionado: sem o arquivo local, vale a presença em `files`.
- Divergência do revisor nunca bloqueia (ADR-014): vira aviso visível no `--approve`. Revisão
  de outro veredito bloqueia, porque não é segunda opinião sobre o que está sendo aprovado.
- `reflow/classification_eval.py`: `prepare`/`score`/`clean` sobre
  `tests/fixtures/classification/`. O Python não chama LLM; qualquer harness roda os agents
  entre `prepare` e `score`. Rótulo cego: `expected.json` nunca é copiado, os nomes são
  neutros e um teste falha se o material do caso vazar o rótulo.
- Critério de aprovação: 90% dos casos corretos e nenhum erro crítico (`PAD` x `NOT_PAD`).
  Caso correto exige veredito, alertas obrigatórios e gate. O limite de 90% é um valor inicial,
  não calibrado.
- `refold classify <projeto>|--eval`: classificador e revisor em execuções isoladas; gate
  reprovado para antes do revisor. Skill `reflow-classify-eval` nos três harnesses.

### Ajuste feito depois de ver o resultado

Na primeira medição, 4 dos 10 casos reprovaram com vereditos certos porque o gate não resolvia
`inventory.json:N` sem a pasta. Era falso positivo do gate (a mesma forma curta já valia para
`risks.md:N`): `01-inventory/` entrou na busca, mantendo a checagem de limite de linha, com
teste próprio. Os classificadores não foram rodados de novo; rótulos, rubrica e prompts não
mudaram.

### O que isto não faz

- Não prova acerto em robô real. Os casos, os rótulos e os documentos foram escritos pelo mesmo
  autor do harness e ainda precisam de revisão de um analista. Os `02-docs/` dos casos trazem
  fatos de contexto (API existente, SaaS) que um documentador real, limitado ao inventário,
  raramente tem: em produção esses critérios tendem a ficar "sem evidência".
- O gate prova que a citação existe, não que sustenta a afirmação. Continuações sem arquivo
  (`:51-58`) não são conferidas.
- O revisor lê o veredito original por contrato, então os 10/10 de concordância não são
  evidência independente de acerto.
- `refold classify` só foi testado com modelo falso. A IAra não foi medida.

### Adendo (Fase 37): casos difíceis e revisão dos rótulos

- Rótulo é hipótese até um analista confirmar. `reviewed_at` no `expected.json` registra isso e o
  relatório sempre mostra quantos foram revisados, para a nota não parecer mais forte do que é.
- A rubrica não foi mudada ao surgirem duas lacunas (efeito de `N3` sozinho e desempate KISS com
  quase nenhuma evidência). Mudar a regra e o rótulo para o eval concordar anularia a medição; a
  decisão é do analista e, se mudar a rubrica, entra em ADR próprio com nova medição.
- Os casos 11 a 16 foram medidos à parte, porque prompts e rubrica não mudaram. Qualquer mudança
  neles exige rodar os 16 casos.

## ADR-035: migrador que otimiza código gerado, orçamento em dólar e complexidade P/M/G

**Contexto.** O conversor escrevia o Robin do zero no LLM, explorando `reference/` turno a turno.
Medido no mesmo robô sintético, só essa etapa custou US$ 0,997 a preço de Opus 5.5 com cache
(US$ 2,89 sem cache), o orçamento inteiro pedido para a migração. Além disso, faltava estimar o
porte do robô.

**Decisão.**

- `reflow generate` monta a base sem LLM, a partir de inventário, tabela verdade e
  `golden_example` da KB. Toda ação passa pela whitelist; o resto vira `# TODO reflow` com evidência.
  O inventário não guarda valores, então texto vira `cfg_` vazia, e nome vindo do legado é
  sanitizado antes de entrar no flow.
- `reflow-robin-optimizer` substitui `reflow-pad-converter` e só melhora a base. O gate
  `reflow optimize-check` reprova passo, ação ou evidência removidos e `cfg_` com valor que a base
  não tinha. Reprovou: a base volta.
- `reflow context-pack` entrega a cada agent só o necessário, com máscara de segredo e PII.
- `refold migrate` impõe o teto a partir do `usage` da API e grava `output/<projeto>/cost.json`.
  Cotas: documentação 0,20, classificação 0,15, revisão 0,10, otimização 0,25, revisão do Robin 0,10,
  teste 0,20; a sobra passa adiante. Opcional que não cabe é pulado, e a base continua valendo.
  Modelo sem preço é recusado: sem preço não há orçamento.
- `reflow complexity` calcula P/M/G: a pior dimensão vence. Só A360 tem confiança alta.

**Consequências.**

- Teto de custo só existe no `refold`. Claude Code, OpenCode e Copilot ganham gerador, pacote e
  gate, mas não teto.
- Os limites de P/M/G são proposta, sem calibração com robôs reais.
- O prompt e a rubrica da classificação não mudaram, então a medição do golden set continua válida
  pelo caminho antigo. O caminho com pacote de contexto (`refold migrate`) não foi medido no eval.
- Medido depois: no Claude Code, a meta de US$ 1 não é atingida (ver `docs/historico.md`, Fase 38).
  O contexto fixo do harness pesa mais que o tamanho do robô.
- A cota de 0,25 do otimizador é menor que os US$ 0,43 medidos no Claude Code, que tem contexto fixo e
  releitura que o `refold` não tem. Se a IAra custar parecido, a otimização depende da sobra dos
  estágios anteriores ou é descartada. Calibrar com a primeira medição real.

