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
