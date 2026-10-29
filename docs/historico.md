# Histórico detalhado

Registro de tudo que foi construído neste repositório, fase por fase, com as
decisões tomadas e por quê. `AGENTS.md` continua a fonte das regras; isto
aqui é o relato do que já foi feito em cima dessas regras — para alguém que
não acompanhou a sessão entender o estado atual sem precisar reconstruir o
raciocínio.

## Antes da Fase 0 — auditoria e separação de projetos

O repositório começou como um esqueleto (Fase 2 de um pipeline de migração
A360/Python/.NET → Power Automate Desktop): só extração determinística
básica, sem skills, agents ou referências completas. Uma auditoria
read-only confirmou isso e identificou um problema real: o pacote Python
`reflow/` tinha sido removido do working tree (o usuário havia "tirado a
pasta reflow que estava sobrescrevendo o novo projeto"), deixando os testes
quebrados (`ModuleNotFoundError`).

Investigação revelou a causa: existe um projeto irmão, muito mais maduro,
em `D:\ENGINEER\VS_Code\reflow\` (git próprio, `.venv` próprio). Em algum
momento esse projeto foi copiado inteiro para dentro de
`migration-reflow/reflow/`, criando um aninhamento (um repositório git
dentro de outro). Confirmado via `diff -rq` que a cópia aninhada era
idêntica ao original preservado — removida com segurança.

Em seguida, reconstruí um pacote `reflow/` **próprio e mínimo** (não copiado
do projeto irmão), guiado só pelos testes existentes e pelo schema já
presente em `output/*/01-inventory/inventory.json` de uma extração anterior
(19/10). A extração real sobre os projetos verdadeiros reproduziu saída
**byte-idêntica** à antiga — confirmando que a reconstrução foi fiel.

Nessa mesma rodada, implementei `reflow scan` e `reflow lint-robin` de
verdade (antes eram stubs que sempre falhavam) para destravar o hook de
pre-commit, e criei o primeiro commit, com remoto configurado para
`https://github.com/cleybersilva/migration-reflow`.

## Fase 0 — descoberta

Antes de executar o prompt detalhado de evolução (skills, agents, segurança
completa, documentação), fiz o levantamento do que já existia vs. o que a
especificação da "fase final" pedia, e levantei um conflito real:
`opencode.json` novo (do prompt) usava campos legados do OpenCode V1
(`provider`/`permission`, singular) e citava `doom_loop`; o repositório já
tinha decidido usar o schema V2 nativo (`providers`/`permissions`, plural,
sem `doom_loop` — `ADR-003`), com um teste automatizado garantindo isso.
Decisão: manter o V2 nativo, traduzindo o conteúdo do prompt para esse
formato.

## Fase 1 — esqueleto e configuração

Resultado: **nada precisou mudar**. `pyproject.toml`, `.gitignore`,
`.gitattributes`, `.env.example`, `opencode.json`, `AGENTS.md`, o hook de
pre-commit e o `git init`/commit já atendiam a especificação da Fase 1
integralmente, graças ao trabalho da rodada anterior.

## Fase 2 — extração determinística (ampliação)

- `reflow/extractors/base.py`: `Protocol Extractor` (contrato comum).
- `reflow/patterns.py`: centraliza os padrões de classificação — registro
  A360 (`packageName`/`commandName` → categoria), operações HTTP/dados do
  Python, marcadores HTTP/IO do .NET. Único lugar a auditar quando a tabela
  verdade precisar crescer.
- Registro A360 ampliado de 8 para 25 entradas (Window, Recorder,
  MouseKeyboard, SOAP, CSV, Database, File, além do que já existia),
  mantendo o comportamento conservador: comando fora disso cai em
  `unknown_commands`.
- CLI: `lint-robin` ganhou argumento posicional `<projeto>` (escopa a busca
  a `output/<projeto>/`); `extract` passou a imprimir contagem por
  categoria por projeto.
- Extração real sobre os 3 projetos verdadeiros: saída idêntica à anterior
  (só o timestamp do manifesto mudou) — confirma que a refatoração não
  alterou comportamento.

## Fase 3 — camada de segurança

- `reflow/security/masking.py` (novo): `mask_secrets()` (redige o valor
  atribuído a uma chave sensível, mantém a chave), `mask_pii()` (CPF, CNPJ,
  e-mail, telefone, agência/conta), `is_placeholder_value()` (distingue
  fixture sintética de segredo real).
- `security/scan.py` refatorado para importar os padrões de `masking.py`
  (fonte única) e **mascarar todo achado antes de reportá-lo** — o próprio
  scanner nunca ecoa um segredo real no terminal.
- `security/safe_zip.py` ganhou limite de **quantidade** de arquivos (zip
  bomb por excesso de arquivos pequenos), além dos limites de tamanho que
  já existiam.
- `SECURITY.md` reescrito com a tabela completa de 11 ameaças → controle →
  onde está → como testar.
- Teste de aceite real: criei um arquivo com um token falso, dei `git add`,
  rodei o hook — bloqueou de verdade, achado já mascarado
  (`API_KEY="***"`). Removido depois.
- Dois bugs de auto-referência descobertos e corrigidos: o próprio código
  do scanner (que contém o nome do cliente dentro do regex que o detecta)
  <!-- reflow:allow-secret --> e os próprios testes (que escrevem segredos
  falsos como fixture) se autodenunciavam. Resolvido com um marcador
  explícito `# reflow:allow-secret`, documentado no próprio módulo.

## Fase 4 — referências editáveis

- `reference/classification-rubric.md`: C1–C5 (UI), N1–N5 (não-UI), A1–A5
  (alertas de portabilidade), regra de decisão PAD/PARTIAL/NOT_PAD, KISS
  ("na dúvida, PAD"), e a regra explícita "nuvem/API já disponível → avaliar
  NOT_PAD".
- `reference/robin-actions.md`: whitelist por módulo (Browser, UI, Excel,
  File, Variables, Loops, Conditionals, Web, Text, + Credentials e Subflows,
  que precisei adicionar porque a tabela verdade dependia deles). Toda ação
  nasceu `[não validado]` — snippet é um placeholder `TODO reflow`
  explícito, nunca sintaxe inventada (regra do `AGENTS.md`/ADR-007).
- `reference/a360-to-pad.md`: tabela verdade com as 25 entradas do registro
  A360 mapeadas, mais os 2 comandos desconhecidos das fixtures como
  "pendente de classificação".
- `reflow/robin/` virou um pacote (`__init__.py`, `lint.py`, `whitelist.py`)
  no lugar do `reflow/robin.py` plano — `whitelist.py` lê os dois arquivos
  acima com um parser de linha simples (não é um parser de Markdown geral).
- Teste de coerência: toda ação citada na tabela verdade existe na
  whitelist (exceto as marcadas "sem equivalente"), e nenhuma ação está
  presumida validada sem evidência real.

## Fase 5 — skills

7 skills em `.claude/skills/`: `reflow` (orquestradora), `reflow-extract`,
`reflow-document`, `reflow-classify`, `reflow-convert`, `reflow-test`,
`reflow-truth-table`. Cada uma documenta entradas, pré-condição, agent
chamado, o que sobrescreve, aviso de fase desatualizada e o resumo a
mostrar. `reflow-convert` tem o checkpoint humano explícito. Confirmado ao
vivo: assim que os arquivos foram escritos, o próprio Claude Code desta
sessão passou a listá-las como skills disponíveis.

## Fase 6 — agents e permissões

Validei contra o `opencode` 2.0.32 **instalado de verdade**
(`opencode debug config`, `opencode debug agents`), não só contra a
especificação do prompt — e encontrei divergências reais:

- O `opencode.json` herdado usava `"action": "shell"`, que não existe no
  schema; a ação correta é `"bash"`. Corrigido.
- O frontmatter de agent do prompt usava `permission:` (singular, objeto
  aninhado) e `temperature:` — ambos são formato legado/inexistente no
  schema real (`additionalProperties: false` rejeitaria `temperature`). O
  formato correto é `permissions:` (array de `{action, resource, effect}`),
  igual ao `opencode.json` raiz.

Criados 5 agents em `.opencode/agents/` (`reflow-documenter`,
`reflow-classifier`, `reflow-pad-converter`, `reflow-pad-tester`,
`reflow-truth-table-curator`), cada um com permissão mínima real: `edit`
negado por padrão, liberado só na própria subpasta de saída;
`bash`/`webfetch`/`websearch`/`external_directory`/`task` sempre negados.
`scripts/sync_agents.py` gera os espelhos em `.claude/agents/*.md`
(frontmatter Claude Code: `name`, `description`, `tools: Read, Grep, Glob,
Write`) a partir dos de OpenCode (fonte da verdade). Confirmado via
`opencode debug agents` que os 5 agents carregam sem erro de schema.

## Fase 7 — commands

8 commands em `.opencode/commands/`: um wrapper fino por skill de fase
(carrega a skill, repassa `$ARGUMENTS` como nome do projeto) + `reflow-report`
(injeta `!`uv run python -m reflow report`` via sintaxe real do OpenCode,
confirmada na documentação oficial).

## Fase 8 — testes e quality gates

- `robin/lint.py` deixou de só checar se a whitelist existe — passou a
  validar de verdade, **sem nunca interpretar a sintaxe interna do Robin**
  (que não está validada): cruza `notas-conversao.md` (convenção nossa, em
  Markdown, listando as ações usadas) contra a whitelist; exige que o
  `README.md` do flow comece com um cabeçalho; varre o `Main.robin` por
  segredo atribuído e por caminho absoluto fora de
  `C:\Users\Public\Documents\`.
- `reflow/report.py` extraído do `cli.py`: tabela por projeto com Veredito,
  Flows, TODO reflow, Ações não validadas, Desconhecidos — mostrando `—`/`0`
  honestamente quando a fase ainda não rodou, nunca presumindo.
- Testes de regressão (golden files, com `--update-golden` explícito para
  regravar de propósito) e de integração (CLI ponta a ponta sobre as
  fixtures) criados do zero.
- Dois bugs reais pegos pelos testes novos: um `\\` duplicado no prefixo de
  caminho permitido do lint, e um teste meu próprio usando uma palavra-chave
  colada com `_` que não batia a borda de palavra do regex de segredo.

## Fase 9 — documentação completa

`README.md`, `docs/architecture.md` e `docs/runbook.md` reescritos por
completo cobrindo todas as seções pedidas (arquitetura, pré-requisitos,
instalação, uso, saídas, do flow pro PAD, tabela verdade/whitelist,
segurança, plano B, como estender, testes, troubleshooting, glossário,
roadmap). `docs/decisions.md` ganhou 3 ADRs novos documentando as correções
reais da Fase 6 e a abordagem do lint na Fase 8. Todo link do README foi
conferido contra o disco; todo comando citado foi executado de verdade
nesta sessão (exceto `/connect`/`/models`, que são comandos interativos de
dentro da TUI do OpenCode — documentados, não executáveis via shell).

## Fase 10 — validação ponta a ponta (de verdade, não simulada)

Com os 5 agents já carregados nesta própria sessão do Claude Code, invoquei
cada um deles de verdade (não descrevi o que eles fariam — rodei e esperei
o resultado):

1. `reflow-documenter` em paralelo para `quote-scraper` e
   `a360-browser-rest` → `02-docs/` completo para os dois, cada fato com
   evidência `arquivo:linha` tirada do inventário real.
2. `reflow-classifier` em paralelo para os dois:
   - `quote-scraper` → **`NOT_PAD`** (0 de 5 critérios de UI atendidos; é
     ETL puro já estável em Python — exatamente o caso que a regra da
     reunião pede para não migrar). Encerrou aí, sem `04-pad`/`05-test`.
   - `a360-browser-rest` → **`PARTIAL`** (UC-01: navegador + REST +
     credencial, vai para o PAD; UC-02: bot filho fazendo ETL puro de
     Excel, fica fora, critério N4). Alertas A1 (extensão de navegador) e
     A4 (migração de credencial) identificados. O classificador registrou
     uma dúvida real — se a chamada REST depende da sessão do navegador —
     como TODO reflow, e escolheu `PARTIAL` em vez de `NOT_PAD` pela regra
     de desempate da rubrica.
3. **Checkpoint humano**: apresentei veredito, escopo e alertas dos dois
   projetos e esperei aprovação explícita do usuário antes de converter
   qualquer coisa. Aprovado, e a decisão foi registrada em
   `output/a360-browser-rest/00-manifest.json` → `checkpoint` (escopo:
   só UC-01).
4. `reflow-pad-converter` para `a360-browser-rest`, escopo UC-01 apenas →
   `04-pad/uc-01-browser-rest/Main.robin` com as 3 ações mapeadas pela
   tabela verdade (`Browser.LaunchNewBrowser`, `Web.InvokeRestApi`,
   `Credentials.GetCredential`), todas `[não validado]` com o placeholder
   `TODO reflow` exato de `robin-actions.md` — nenhuma sintaxe inventada.
5. `reflow-pad-tester` → `05-test/test_uc-01-browser-rest/` com 4 cenários
   (`CT-01` a `CT-04`): caminho feliz, credencial ausente, URL inacessível,
   erro 4xx/5xx — tabela de resultado só com `(a executar no PAD)`, nunca
   PASS/FAIL fabricado.
6. `uv run python -m reflow lint-robin a360-browser-rest` — **passou de
   verdade**; confirmei por chamada direta ao módulo que os dois
   `Main.robin` (conversão e teste) foram mesmo inspecionados, 0 achados.
7. `uv run python -m reflow scan` rodado depois de cada etapa (documentar,
   classificar, converter, testar) — sempre limpo, nenhum segredo entrou em
   nenhum arquivo gerado por agent.
8. `uv run python -m reflow report` — relatório de lote final mostrando os
   3 projetos reais, incluindo `a360-excel-vault` intocado de propósito
   (`—` no veredito, honesto sobre o que não foi processado nesta rodada).

`uv run pytest` (79/79), `ruff check`/`format` e o hook de pre-commit
continuaram verdes em cada checkpoint desta fase.

## Commits e push

Dois commits enviados para `https://github.com/cleybersilva/migration-reflow`:

1. `9b49f98` — esqueleto inicial (extração, scan/lint mínimos, docs).
2. `8bf4538` — Fases 2–10 completas: 109 arquivos, 4172 inserções — todo o
   pipeline, skills/agents reais, e a primeira conversão ponta a ponta
   (`a360-browser-rest`, UC-01).

## O que ainda não está pronto (seja honesto sobre isso)

- **Nenhuma ação da whitelist foi validada num PAD real.** Tudo que existe
  é `[não validado]` com placeholder `TODO reflow` — porque este ambiente
  não tem acesso a uma instalação real do Power Automate Desktop. Montar a
  ação no designer, confirmar que funciona e colar o texto real é trabalho
  que só um analista humano, com o PAD aberto, pode fazer.
- O `checkpoint` em `00-manifest.json` só existe porque eu editei o campo à
  mão depois da aprovação na conversa — não há ainda um comando de CLI que
  grave isso automaticamente a partir de uma resposta de chat.
- A dúvida sobre `Browser.open`/`REST.get` dependerem ou não da mesma sessão
  de navegador continua aberta — é uma pergunta sobre o comportamento real
  do A360, que é sintético aqui (fixture de teste, não um robô real).
- `a360-excel-vault` e exports A360 reais (fora das fixtures sintéticas)
  ainda não passaram pelo pipeline.
- UC-02 (bot filho lendo Excel) não teve uma alternativa de arquitetura
  avaliada em detalhe ainda.

## Fase 11 — segunda opinião e auditoria semântica (dois agents novos)

Depois de modernizar o `README.md` (header, badges, autor), o usuário pediu
uma avaliação honesta de quais agents/skills a mais trariam robustez e
eficiência reais ao pipeline, e autorizou implementar os que fizessem
sentido. Levantamento (AGENTS.md, `docs/architecture.md`,
`docs/decisions.md`, as 7 skills e os 5 agents existentes, `report.py`,
`inventory.py`, `cli.py`, e os testes que travam a convenção de
skills/agents) apontou uma lacuna real: cada fase do pipeline tem um único
agent decidindo sozinho, sem segunda leitura, e `reflow lint-robin`
(ADR-012) só valida estrutura — nunca semântica.

Apresentei 4 candidatos ao usuário (segunda opinião na classificação,
revisor semântico do Robin, triagem de lote determinística, resumo
executivo multi-projeto) e ele escolheu os dois primeiros:

1. **`reflow-classification-reviewer`** (agent) + **`reflow-classify-review`**
   (skill) — reclassifica um projeto do zero, sem ver o raciocínio do
   `reflow-classifier`, e grava `03-classification/review.md` com
   `original_verdict`/`reviewed_verdict`/`agreement`. Permissão de edição
   restrita ao próprio `review.md` (mais estrita que os demais agents, que
   podem escrever em qualquer arquivo da subpasta de fase) — nunca pode
   sobrescrever `classification.md`.
2. **`reflow-robin-reviewer`** (agent) + **`reflow-convert-review`** (skill)
   — audita um `Main.robin` já aprovado no lint estrutural: cobertura de
   caso de uso, densidade de `TODO reflow`, convenções de nomenclatura e
   consistência entre `notas-conversao.md` e o flow de fato (o que o lint
   determinístico não verifica). Grava `04-pad/<flow>/review.md`, nunca o
   `Main.robin`.

Documentado em `AGENTS.md` (pipeline alvo), `docs/architecture.md` (diagrama,
componentes, fluxo de dados), `docs/decisions.md` (ADR-014 e ADR-015), e no
orquestrador `/reflow` (novos passos 4 e 7 na sequência). Os dois novos
agents canônicos ficam em `.opencode/agents/`, espelhados em `.claude/agents/`
via `scripts/sync_agents.py`; as duas skills em `.claude/skills/`; os dois
commands finos em `.opencode/commands/`. Nenhum teste precisou mudar — os
parametrizados sobre `_skill_dirs()`/`_source_agents()` já cobrem qualquer
skill/agent novo automaticamente, e os testes de "pelo menos N" (sete skills,
cinco agents) continuam passando por serem checagens de subconjunto.

**Validação real, não simulada**: antes de considerar a fase pronta, invoquei
as duas skills novas de verdade contra `a360-browser-rest` (que já tinha
`classification.md` e `04-pad/uc-01-browser-rest/Main.robin` prontos da Fase
10) — segui eu mesmo as instruções de cada agent, como fiz na Fase 10:

- `reflow-classify-review` → reclassifiquei UC-01/UC-02 do zero a partir do
  inventário e de `02-docs/`, cheguei a `reviewed_verdict: PARTIAL` pelo
  mesmo caminho da rubrica (regra de desempate explícita, não cópia do
  primeiro veredito), `agreement: concorda`, e registrei uma nota adicional
  sobre o alerta A3 que o veredito original não tinha levantado (Excel
  tipicamente depende de instalação local, mesmo sem UI explícita) —
  gravado em `output/a360-browser-rest/03-classification/review.md`.
- `reflow-convert-review` → rodei `uv run python -m reflow lint-robin
  a360-browser-rest` antes (passou, 0 achados) e então auditei
  `uc-01-browser-rest/Main.robin`: cobertura completa de UC-01, nomenclatura
  100% dentro de `robin-conventions.md`, `notas-conversao.md` consistente com
  o flow — nenhum achado bloqueante, só uma nota informativa sobre os 3
  passos ainda `[não validado]` (esperado, consistente com o que
  `historico.md` já registrava sobre nenhuma ação ter sido validada num PAD
  real) — gravado em
  `output/a360-browser-rest/04-pad/uc-01-browser-rest/review.md`.

`uv run pytest`, `ruff check`/`format --check` e o hook de pre-commit
(`scan` + `lint-robin`) continuaram verdes depois desta fase.

### O que esta fase não fez

- Não implementei os outros dois candidatos (triagem de lote determinística,
  resumo executivo multi-projeto) — ficam como ideia registrada, não como
  trabalho pendente assumido.
- Não rodei estes dois agents novos contra nenhum outro projeto além de
  `a360-browser-rest`; `quote-scraper` (NOT_PAD, sem `04-pad/`) não se
  aplica ao `reflow-convert-review`, e não repeti o `reflow-classify-review`
  nele nesta sessão.
- Os dois agents de revisão continuam sem ter sido chamados de dentro do
  próprio orquestrador `/reflow` em uma execução de lote real — só foram
  invocados isoladamente, via skill, para validar que funcionam.

## Fase 12 — Copilot como terceiro harness espelhado

Ao revisar a Fase 11, o usuário perguntou se tudo tinha sido aplicado também
ao opencode, e deixou uma regra permanente: **Claude Code, opencode e
GitHub Copilot têm que evoluir juntos** — o que for feito num tem que ser
feito nos outros dois, sempre, incluindo criar todas as skills e agents
também para o Copilot. Antes desta fase, `.github/` nem existia neste
repositório.

Conferência do lado opencode primeiro (o que o usuário pediu para checar):
7 agents em `.opencode/agents/` e 9 commands em `.opencode/commands/` já
batiam 1:1 com as 7 skills/2 revisões da Fase 11 — só achei uma divergência
real, a description de `.opencode/commands/reflow.md` ainda citava a
sequência antiga do orquestrador (sem os passos de revisão), corrigida nesta
fase.

Desenho para o Copilot, caso a caso (detalhado em `docs/decisions.md`
ADR-016):

1. `.github/copilot-instructions.md` — ponteiro para `AGENTS.md`, igual ao
   `CLAUDE.md`.
2. `.github/prompts/<nome>.prompt.md` — um por skill (9) mais
   `reflow-report.prompt.md` (CLI, sem skill dedicada) = 10 arquivos.
   Escritos à mão, como ponteiro de uma linha para a `SKILL.md`
   correspondente — o Copilot, em modo agent, abre e segue o arquivo
   apontado, então não há necessidade de duplicar o conteúdo da skill.
3. `.github/chatmodes/<nome>.chatmode.md` — 7 arquivos, **gerados** por
   `scripts/sync_copilot.py` (script novo) a partir de `.opencode/agents/`,
   mesma fonte dos espelhos Claude. Cada chatmode gerado ganha um aviso
   automático no rodapé: o Copilot Chat não tem motor de permissão por
   recurso como o OpenCode, então a restrição de escopo ali é só instrução —
   nunca prometer ao usuário uma garantia técnica que esse harness não tem.
4. `tests/unit/test_copilot.py` (novo, 26 casos): toda skill tem prompt,
   todo agent tem chatmode, todo chatmode mirrora byte a byte o agent
   OpenCode de origem, todo chatmode carrega o aviso de permissão.
5. `AGENTS.md` ganhou a regra permanente dos três harnesses nas Convenções;
   `README.md` (seção "Plano B" renomeada para os três, pré-requisitos,
   "Como estender") e `docs/architecture.md` (diagrama, fronteiras de
   confiança) atualizados para citar o Copilot onde fazia sentido.

`uv run pytest` → 111/111 (85 anteriores + 26 novos), `ruff check`/`format`
limpos.

### O que esta fase não fez (honestidade)

- **Nenhum destes arquivos foi testado dentro do GitHub Copilot de
  verdade** — a extensão não está disponível neste ambiente. O formato
  (`mode: agent`, `${input:variável}` em prompt files; `description`/`tools`
  em chat modes) segue a documentação pública de customização do Copilot
  Chat, mas, como o `IARA_MODEL` do ADR-002, só se confirma com a ferramenta
  real instalada — mesmo princípio de honestidade já aplicado ao longo deste
  histórico.
- Não criei testes de integração que simulem o Copilot executando um
  prompt/chatmode — só testes estruturais (frontmatter, paridade, conteúdo).

## Fase 13 — dashboard local portado, LangChain avaliado e descartado

O usuário pediu uma "estrutura robusta de LangChain" e um dashboard de
teste "como tinha antes", com a ressalva explícita: se LangChain não
agregasse valor real, era para portar a estrutura madura sem ele. Antes de
escrever qualquer código, entrei em modo de planejamento (o pedido envolvia
decisão arquitetural real e múltiplos arquivos) e investiguei o "antes":
o projeto irmão `D:\ENGINEER\VS_Code\reflow\` (`web/server.py`,
`web/pipeline.py`, `web/ollama_worker.ps1`, `web/app.js`,
`docs/dashboard.md`, testes em `tests/integration/test_dashboard.py` e
`tests/frontend/dashboard.test.cjs`).

Achado decisivo: o worker PowerShell isolado já resolve o mesmo problema
(prévia JSON estruturada, retry com dica, validação de evidência) com uma
fronteira de segurança **mais forte** que LangChain traria — a chamada de
rede ao LLM fica fora do processo Python, nunca dentro dele — e zero
dependência pesada. Apresentei essa análise ao usuário antes de implementar
(via `ExitPlanMode`), ele confirmou: sem LangChain, portar a estrutura
madura como estava.

O que foi feito:

1. Duas funções pequenas e aditivas no núcleo, nunca alterando o que já
   existia: `reflow/security/scan.py` ganhou `scan_bytes()` (reaproveita o
   `_scan_line()` já existente para bytes arbitrários, não só arquivos do
   repositório) e `reflow/security/masking.py` ganhou `mask_data()`
   (mascara recursivamente toda string-folha de um dict/list, reaproveitando
   `mask()`). `reflow/cli.py` ganhou `extract_to(project_dir, out_dir)`,
   fatorado de `_extract_one` sem mudar nenhum comportamento observável
   (confirmado pelos 111 testes existentes passando antes e depois do
   refactor).
2. `dashboard/` novo (irmão de `reflow/`, nunca importado por ele):
   `pipeline.py` (`DashboardRunner`, porta `LocalRunner` quase literalmente),
   `ollama_worker.ps1` (porta verbatim — prompt, JSON Schema, sanitização de
   erro, idênticos), `server.py` (porta `web/server.py`: loopback-only,
   CSRF, CSP, SSE com cursor por cliente), `index.html`/`app.js`/
   `favicon.svg` (mesmo comportamento, mesmos ids que `app.js` espera),
   `style.css` (**redesenho visual completo** — tema escuro moderno, grade
   de passos, métricas e progresso redesenhados, CSS puro sem CDN) e
   `README.md` (escopo honesto, igual ao `docs/dashboard.md` original).
3. Durante o port, o `reflow scan` pegou um falso positivo real: a palavra
   "token" (CSRF) bate no regex de segredo atribuído
   (`reflow/security/masking.py` → `SECRET_KEY_RE`). `AGENTS.md`/`scan.py`
   proíbem explicitamente usar `reflow:allow-secret` fora de fixtures/
   definição do detector — por isso renomeei a variável para `csrf` (nome
   aliás mais preciso) em vez de silenciar o scanner.
4. `tests/integration/test_dashboard.py` (8 testes) e
   `tests/frontend/dashboard.test.cjs` (3 testes) portam a suíte de
   regressão do projeto irmão. Precisei convertê-los do `assert` nu do
   projeto irmão para o helper `require(condition, message)` que todo outro
   teste deste repositório usa — o `pyproject.toml` daqui, ao contrário do
   irmão, não isenta `tests/**` da regra `S101` do ruff, e eu quase deixei
   passar essa inconsistência até o `ruff check` apontar 58 ocorrências.
5. `AGENTS.md`, `docs/decisions.md` (ADR-017), `docs/architecture.md` e
   `README.md` documentam o dashboard como ramo opcional, fora da pipeline
   orientada a harness, com a exceção estreita e documentada à "Fronteira
   Python × LLM".

`uv run pytest` → 124/124 (116 anteriores + 8 do dashboard),
`node --test tests/frontend/dashboard.test.cjs` → 3/3, `ruff check`/`format`
e `reflow scan`/`lint-robin` limpos.

### O que esta fase não fez (honestidade)

- **Nenhuma execução real contra Ollama/PowerShell 7 de verdade** —
  confirmei só com `FakeRunner` (sem rede) nos testes automatizados; não
  tenho Ollama instalado neste ambiente para rodar
  `uv run python dashboard/server.py` ponta a ponta e ver a prévia real na
  tela. O manual de verificação ficou documentado (`dashboard/README.md`),
  não executado.
- Não portei `reflow/agent_profiles.py`, `reflow/state.py` nem
  `scripts/orchestrate_llm.py` do projeto irmão (o driver headless do
  `opencode` CLI) — ficam fora de escopo desta fase, que tratou só do
  dashboard de teste textual, não de disparar a pipeline real.

## Fase 14 — segurança: mascaramento/scan (Fase 1) e contenção de caminho, ZIP e limites (Fase 2)

A análise de automação e cibersegurança de 24/10/2026 apontou 11 lacunas
reais sem caracterizar nenhuma delas como vazamento já explorado. O usuário
pediu para evoluir por fases pequenas, com aprovação entre cada uma. Esta
etapa fecha as duas primeiras — ADR-018 e ADR-019 em
[`docs/decisions.md`](decisions.md) documentam cada mudança e o que ela
quebra de propósito.

### Fase 1 — mascaramento por chave e scan do índice

1. `mask_data()` (`reflow/security/masking.py`) passou a mascarar pelo
   **nome da chave** (`password`, `token`, `api_key`, `authorization`,
   `connection_string`) em estrutura aninhada: antes só a regex de texto
   livre era aplicada por string-folha, que nunca via a associação
   chave→valor do JSON.
2. `SECRET_ASSIGNMENT_RE` — fonte única em `masking.py`, reusada por
   `scan.py` e `robin/lint.py` — reconhece chave JSON entre aspas seguida
   de `:` e valor entre aspas (antes a aspa que fechava a chave vinha antes
   do `:` e não casava). Aspas exatamente ao redor da palavra-chave, para
   não casar o sufixo de uma chave maior.
3. Novo `BEARER_TOKEN_RE`, aplicado antes de `SECRET_ASSIGNMENT_RE`, consome
   o par `Authorization` + token `Bearer` inteiro — antes o regex capturava
   a palavra do esquema como se fosse o valor e o token real seguia
   intacto.
4. Excertos de achado (`scan.py`, `robin/lint.py`) são mascarados **antes**
   de truncar em 120 caracteres: uma credencial maior que o trecho podia ter
   o corte caindo no meio da chave e escapar.
5. `reflow:allow-secret` deixou de silenciar qualquer arquivo: só vale em
   `tests/` ou nos próprios módulos do detector. Ignorado fora disso —
   inclusive em `scan_bytes()` (saída isolada de LLM do dashboard), que
   nunca pode se autoexcluir pelo conteúdo que está checando.
6. Novo `scan_staged()` em `reflow/security/scan.py` lê o blob preparado
   (stage 0, `git show :<path>`) de cada arquivo listado por
   `git diff --cached --name-only -z` — nunca a working tree. O hook
   `.githooks/pre-commit` passou a rodar `reflow scan --staged`;
   `StagedScanError` é levantada em vez de voltar `[]` silencioso.

### Fase 2 — contenção de caminho, ZIP e limites do dashboard

1. Novo `reflow/security/paths.py`: `reject_unsafe_links(root)` recusa o
   projeto **inteiro** se `root` ou qualquer entrada abaixo dele for
   symlink ou junction (`is_symlink() or is_junction()` — no Windows nenhum
   dos dois sozinho cobre as duas formas). Deliberadamente grosseiro, ver
   ADR-019.
2. `reflow/cli.py`: `_build_manifest()` e `extract_to()` chamam
   `reject_unsafe_links` antes de ler qualquer conteúdo — um projeto com
   link escondido nunca tem conteúdo fora do sandbox lido ou hasheado.
   `dashboard/pipeline.py` aplica o mesmo critério por subpasta, mas
   falha por projeto (um link some da lista, os outros seguem).
3. `reflow/robin/lint.py`: `_is_allowed_output_path()` resolve `..` com
   `ntpath.normpath` **texto** (nunca toca o filesystem) antes de comparar
   com `C:\Users\Public\Documents\` — antes era prefixo de string bruta,
   então `...\Documents\..\..\Windows\...` passava. Novo `UNC_PATH_RE`
   varre caminho UNC, que antes nem era avaliado.
4. `reflow/security/safe_zip.py`: `_is_safe_member()` rejeita `:` em
   qualquer posição (letra de unidade e Alternate Data Stream), nome
   reservado do Windows (`CON`/`PRN`/`AUX`/`NUL`/`COM1-9`/`LPT1-9`, com ou
   sem extensão), componente com espaço/ponto final, e
   `_windows_collision_key()` detecta dois nomes que o Windows trataria
   como o mesmo arquivo — tudo **antes** de extrair qualquer membro.
5. `dashboard/pipeline.py`: `_check_input_budget()` recusa o projeto se
   passar de 500 arquivos, 12 níveis ou 20 MB. `dashboard/server.py`:
   `Dashboard.MAX_SSE_CLIENTS = 6` devolve `429` acima do teto. Os
   controles que já existiam (loopback, Host/Origin, CSRF, CSP, isolamento
   de `output/`) não foram tocados.

### Verificação

`uv run -- python -m pytest -q` → **179 passed** (162 da Fase 13 + 17 novos),
`ruff check .` e `ruff format --check .` limpos (147 arquivos),
`reflow scan`, `reflow scan --staged` e `reflow lint-robin` todos `ok`.
Também foi a primeira vez que `scan --staged` rodou de verdade no ambiente.

### O que esta fase não fez (honestidade)

- **Fase 3 e 4 seguem abertas**: escrita atômica, lock por projeto,
  checkpoint vinculado a hash com comando de CLI, resiliência de lote e
  priorização determinística A360 (JSON/ZIP). O `checkpoint` em
  `00-manifest.json` continua sempre `null` (`reflow/cli.py:62`).
- Orçamento de entrada e teto de conexões SSE existem só no `dashboard/`;
  `reflow extract` / `--all` (a CLI real) não têm esse teto.
- Nenhum cenário foi validado contra segredo ou ZIP real de terceiros —
  todos os testes novos usam dados sintéticos gerados no próprio teste.
- Nada disto muda o fato de que **nenhuma ação da whitelist foi validada
  num PAD de verdade**; isso continua fora deste repositório.

## Fase 15 — segurança: escrita atômica, lock por projeto e checkpoint vinculado a hash

Seguindo a régua de fases pequenas com aprovação entre cada uma, esta etapa
fecha o item 3 do plano (`SECURITY.md` → "Fase 3"), documentado no
ADR-020 em [`docs/decisions.md`](decisions.md). Eram três lacunas do
diagnóstico de 24/10/2026: gravação direta sem atômica (item 8), ausência
de lock por projeto (item 8) e um `checkpoint` que só existia porque o
campo foi editado à mão depois de uma aprovação na conversa, sem nenhum
comando para registrar ou verificar (item 6).

### 1. `reflow/fs.py` — módulo novo

- `write_json_atomic()`: grava no temporário `.<nome>.<pid>.tmp` do mesmo
  diretório e troca com `os.replace` (atômico no Windows e no POSIX); em
  falha, remove o temporário e preserva o arquivo anterior. Substituiu o
  `_write_json` de `reflow/cli.py` e a cópia duplicada em
  `dashboard/pipeline.py` — uma implementação só.
- `project_lock()`: lock de 1 byte num arquivo irmão do diretório de saída
  (`output/<nome>.lock`), retido pelo SO (`msvcrt.locking`/`fcntl.flock`),
  portanto liberado sozinho se o processo morrer. Timeout de 10 s →
  `LockError`. **Reentrante no mesmo processo**: `extract_to()` segura para
  o inventário e `_extract_one()` de novo para o manifesto, sem deadlock.
- `/output/*.lock` no `.gitignore` — artefato de execução, não resultado.
- O lock ficou fora do projeto de propósito: dentro dele, o teste
  "nenhum output parcial para projeto recusado" (junction) teria passado a
  falhar, porque `output/<projeto>/` nasceria antes da validação.

### 2. `reflow checkpoint` — subcomando novo na CLI

- `--status` (padrão), `--approve` e `--reject`, mutuamente exclusivos.
- Antes de decidir qualquer coisa, **recalcula** o SHA256 de
  `input/<projeto>/` (rotina fatorada em `_current_inputs()`, a mesma do
  `_build_manifest`) e compara com `manifest.inputs`; diferente → código 1
  e nada gravado. `--status` também acusa manifesto velho.
- `--approve`/`--reject` exigem `03-classification/classification.md`;
  `--approve` é recusado com veredito `NOT_PAD`.
- Objeto gravado: `decision`, `recorded_at`, `inputs_fingerprint`
  (SHA256 canônico da lista de entradas) e `classification_sha256` — sob
  lock e de forma atômica.
- Reextração regrava o manifesto → `checkpoint` volta a `null`: decisão
  velha não sobrevive a entrada nova.
- `report.py` ganhou `read_verdict()` (era `_read_verdict`, privado) — o
  checkpoint reusa o leitor de frontmatter do relatório em vez de
  reimplementar.

### 3. Documentação e skill atualizadas

`SECURITY.md` (três linhas novas na tabela de ameaças, seção própria sobre
`reflow checkpoint` e "o que ainda não está pronto" corrigido),
`docs/decisions.md` (ADR-020), `docs/architecture.md` (nó `fs.py` no
diagrama, comando no nó do checkpoint), `README.md` (uso, saídas, tabela de
fases, segurança), `AGENTS.md` (linha do checkpoint na tabela da pipeline e
lista de comandos — que também corrigia o texto desatualizado dizendo que
scan/lint-robin estavam indisponíveis, quando já são gates de verdade) e a
skill `.claude/skills/reflow-convert/SKILL.md` (o checkpoint agora se grava
pela CLI, não editando JSON à mão).

### Verificação

`uv run -- python -m pytest -q` → **189 passed** (179 da Fase 14 + 10
novos: 3 em `tests/unit/test_fs.py`, 7 em
`tests/integration/test_checkpoint.py`), `ruff check .`,
`ruff format --check .` (150 arquivos), `reflow scan`,
`reflow scan --staged` e `reflow lint-robin` todos `ok`.

Numa das execuções a suíte falhou em
`tests/integration/test_dashboard.py::test_invalid_origin_...` com
`ConnectionAbortedError` do servidor de teste — **flake de carga**: passou
rodando o arquivo sozinho (9/9) e na re-execução da suíte completa
(189/189). Fica registrado aqui em vez de varrer para debaixo do tapete;
se repetir, merece investigação própria.
*(Resolvido na Fase 18: a causa raiz era o `POST` rejeitado respondendo sem
consumir o corpo, e o RST do Winsock destruindo a resposta em trânsito.)*

### O que esta fase não fez (honestidade)

- **Fase 4 segue aberta**: resiliência de lote (`extract --all` ainda
  aborta com exceção fora de `ValueError`), priorização determinística
  A360 entre JSON e ZIP, orçamento de entrada na CLI real (hoje só no
  dashboard) e CI em `.github/workflows`.
- O checkpoint é rastreabilidade determinística, **não autenticação**: o
  JSON não prova *quem* decidiu, só o que estava na mão e se ainda é o
  que foi extraído.
- Nenhuma sessão real do agent `reflow-convert` rodou seguindo a skill com
  o comando novo — a conversão do `a360-browser-rest` (Fase 10) foi feita
  antes dele existir.
- Nada foi validado num PAD real; a whitelist segue 100% `[não validado]`.

## Fase 16 — segurança: resiliência de lote, escolha A360 explícita e orçamento de entrada na CLI

Fechou os três itens que o ADR-020 deixou registrados como pendentes —
mantida a régua de fases pequenas com aprovação entre cada uma. Tudo
documentado no ADR-021 em [`docs/decisions.md`](decisions.md).

### 1. `extract --all` não é mais derrubado por um projeto estragado

`_extract_all()` capturava só o retorno de `_extract_one()`, mas esse
método tratava **só** `ValueError`: qualquer outra exceção (JSON cujo
top-level é lista, `AttributeError` na estrutura, `RecursionError` em
árvore profunda, `zipfile.BadZipFile`, disco cheio) abortava o lote
inteiro e nem tentava os projetos seguintes. Agora é `except Exception`
por projeto — reporta `<nome>: extração abortou de forma inesperada:
<repr>` em stderr, continua, imprime `lote: N/M projeto(s) extraído(s);
falharam: <nomes>` e sai com código 1. `KeyboardInterrupt` e
`SystemExit` não são `Exception`, então Ctrl+C continua interrompendo.

### 2. A360: escolha explícita e aviso do que não foi lido

- Vários `.zip` no topo do projeto: antes `sorted(...)[0]`, ou seja,
  escolha silenciosa em ordem alfabética — dava para extrair o robô errado
  sem perceber. Agora `ValueError` citando todos os nomes, pedindo um
  export por projeto.
- JSON aninhado, `.zip` e o mais nunca foram lidos (leitura continua só
  `*.json` no topo — decisão mantida e agora escrita no ADR-021: sem
  fixture real de subpasta, ampliar inventaria fato de arquivo errado).
  O que mudou: o extractor agora avisa em stderr
  `aviso A360: N arquivo(s) fora da leitura em <dir>: <nomes>` — até 5
  nomes.

### 3. `reflow/limits.py` — orçamento da extração real

Novo módulo com `check_input_budget()`: 5000 arquivos, 30 níveis,
64 MB por arquivo e 512 MB no total, medidos só com `stat` (nunca lendo
conteúdo) e **depois** de `reject_unsafe_links()`. Chamado em
`extract_to()` (antes de extrair, CLI e dashboard) e em
`_current_inputs()` (manifesto e `checkpoint`). Valores lidos dos nomes do
módulo em tempo de chamada — o teste rebaixa o teto com `monkeypatch` em
vez de criar arquivo de 64 MB. O `dashboard/` seguiu com o orçamento
próprio mais apertado (500/12/20 MB, ADR-019): duas camadas, não
duplicação.

### Verificação

`uv run -- python -m pytest -q` → **199 passed** (189 da Fase 15 + 10
novos: 5 em `tests/unit/test_limits.py`, 3 de A360 em
`tests/unit/test_extractors.py`, 2 de integração lote/orçamento em
`tests/integration/test_cli_end_to_end.py`), `ruff check .`,
`ruff format --check .` (152 arquivos), `reflow scan`,
`reflow scan --staged` e `reflow lint-robin` todos `ok`.

### O que esta fase não fez (honestidade)

- **CI continua não existindo** (nesta fase) — fora do escopo destas quatro
  fases de segurança; é fechada na Fase 17.
- Não ampliei a leitura A360 para JSON aninhado: decidi avisar em vez de
  inventar cobertura sem fixture real que mostre o formato do export.
- Os tetos de orçamento são **genéricos, não calibrados em robô real**
  (nenhum export verdadeiro passou por aqui ainda); se um export legítimo
  estourar, o ajuste é consciente e documentado, não um chute disfarçado.
- Nada foi validado num PAD real; a whitelist segue 100% `[não validado]`.

## Fase 17 — CI versionada em `.github/workflows/ci.yml`

Fecha a última pendência de infra do diagnóstico de 24/10: os gates (pytest,
ruff, scan, lint-robin) existiam só localmente, e só rodavam se alguém
configurasse `git config core.hooksPath .githooks`. Documentado no ADR-022
em [`docs/decisions.md`](decisions.md).

### O que foi criado

`.github/workflows/ci.yml` com dois jobs:

- **`checks`** — matriz 2×2: `ubuntu-latest` + `windows-latest` × Python
  3.12 + 3.14. Passos: `uv sync --frozen` → `ruff check .` →
  `ruff format --check .` → `python -m pytest` (suíte inteira, que já
  inclui a paridade dos três harnesses — `test_copilot.py`,
  `test_sync_agents.py`, `test_skills.py`, `test_commands.py`) →
  `reflow scan` → `reflow lint-robin --all`.
- **`frontend`** — `ubuntu-latest`, Node 24:
  `node --test tests/frontend/dashboard.test.cjs`.

Gatilhos: `push` em `main`, `pull_request` e `workflow_dispatch` manual.
`permissions: contents: read` (nenhum secret), `fail-fast: false` (os quatro
jobs da matriz rodam todos, para comparar SO/versão), `concurrency` por ref
cancelando a execução anterior.

### Decisões que merecem registro (ADR-022)

- **`reflow scan`, não `scan --staged`**: o `--staged` lê o índice Git
  (`git show :<path>`), que não existe num checkout da CI — rodaria vazio e
  daria falso senso de cobertura. O `--staged` segue local, no hook.
- **`uv sync --frozen`**: usa o lock como está, sem reescrever; CI nunca
  altera artefato versionado.
- **Linux na matriz** cobre o caminho POSIX do `fcntl` do `reflow/fs.py`;
  Windows é o alvo real (PAD, `msvcrt.locking`, junction via `mklink /J`).
  Os testes de link ganharam o helper compartilhado
  `tests/link_support.py`: junction no Windows, **symlink** em POSIX —
  antes, o `cmd /c mklink` embutido em três arquivos de teste faria os
  testes **falharem** (não pulassem) no Linux, porque `cmd` não existe lá.

### Verificação

- YAML validado com `pyyaml` (carga efêmera via `uv run --with pyyaml`, sem
  tocar no projeto/lock): `on` com `push`/`pull_request`/`workflow_dispatch`,
  jobs `checks` e `frontend`, matriz 2×2, 8 + 3 steps.
- Todos os comandos da CI foram executados localmente antes do primeiro
  commit: `uv sync --frozen` → ok; `ruff check`/`format --check` → ok;
  `pytest` → **199 passed**; `reflow scan` e `reflow lint-robin --all` →
  ok; `node --test tests/frontend/dashboard.test.cjs` (Node v24.15.0) →
  **3/3**.
- Badge de CI adicionada no topo do README, apontando para o workflow.

### A primeira execução real falhou — e foi corrigida (run 1 → run 2)

Como eu mesmo avisei antes de empurrar, o workflow só roda de verdade no
GitHub. Ele falhou na **run 1** em 8 segundos, e o diagnóstico saiu do log:

```
##[error]Unable to resolve action `astral-sh/setup-uv@v10`,
         unable to find version `v10`
```

A action **não publica tag major** — só releases `v10.x.y`, sem `refs/tags/v10`.
Os 4 jobs de `checks` morreram no step 1 (o job `frontend` passou, porque
`checkout@v7`/`setup-node@v7` existem). Correção (commit `f712898`):

1. `astral-sh/setup-uv` travado no **SHA exato** da v10.3.2
   (`07a047e608db84b3d8c06cd9a7c7dcc9c355c18e`) com o comentário da versão
   ao lado — tag major inexistente não pode ser o ref, e SHA travado é
   também a prática segura de supply chain.
2. Antes de re-empurrar, conferi no `action.yml` daquela tag exata que os
   inputs usados (`python-version`, `enable-cache`, `cache-dependency-glob`)
   existem de fato — em vez de adivinhar de novo.
3. Refactor dos três arquivos que criavam junction com `cmd /c mklink`
   embutido (`test_security_paths.py`, `test_dashboard_pipeline.py`,
   `test_cli_end_to_end.py`) para `tests/link_support.py`, que usa symlink
   em POSIX. Sem isso, os jobs de Linux teriam **falhado** logo depois — a
   matriz cumpriu o papel de pegar isso, mesmo que só na segunda rodada.

**Run 2** (`40365830911`) — `success`, 5/5 jobs:

| Job | Resultado | Duração |
| --- | --- | --- |
| checks (windows-latest, py3.14) | ✅ | 39 s |
| checks (windows-latest, py3.12) | ✅ | 33 s |
| checks (ubuntu-latest, py3.14) | ✅ | 20 s |
| checks (ubuntu-latest, py3.12) | ✅ | 19 s |
| frontend (dashboard) | ✅ | 7 s |

### O que esta fase não fez (honestidade)

- ~~**A CI pode ficar vermelha por um flake conhecido do dashboard**~~ —
  resolvido na Fase 18: a causa raiz era o `POST` rejeitado respondendo sem
  consumir o corpo; o RST do Winsock destruía a resposta em trânsito. O
  detalhe está no ADR-023.
- CI verde **não** significa nada validado no PAD: a whitelist segue 100%
  `[não validado]`, e a CI não executa legado, não chama LLM e não tem
  segredo algum — só os gates determinísticos.
- A suíte roda em Linux, mas o alvo de migração é Windows; a CI cobre
  comportamento do Python, não do Power Automate.
- Continua aberto o deadline de leitura do `POST` no dashboard.
  *Resolvido na Fase 19 (ADR-024).*

## Fase 18 — Corrigido o flake do dashboard: rejeição de POST respondia com RST

Peguei a pendência que eu mesmo deixei escrita na Fase 17: o flake de
`test_dashboard.py::test_invalid_origin_...`, que caía com
`ConnectionAbortedError` em execução de suíte completa. Documentado no ADR-023
em [`docs/decisions.md`](decisions.md).

### A causa raiz

O `http.client` envia cabeçalho e corpo em **dois `send()`**. O `do_POST` do
dashboard rejeitava (403 sem token, 400 com corpo inválido) escrevendo a
resposta **sem nunca ler o corpo**. Se o corpo chegava depois de o handler já
ter lido os cabeçalhos, ele respondia e fechava o socket com bytes não lidos —
o Winsock responde **RST** a um envio que bate em socket fechado, e o RST
destrói a resposta que já estava em trânsito. O cliente via
`ConnectionAbortedError` no `getresponse()`; o servidor via `WinError 10053`
no próprio `wfile.write`. A carga é o que atrasa o corpo entre os dois
`send()`, por isso só aparecia em suíte completa.

### Como eu sei que essa é a causa (e não chute)

Reproduzi a corrida de forma **determinística** com socket bruto, variando o
atraso entre cabeçalho e corpo, com o servidor **sem** o fix:

| Atraso do corpo | Resultado (40 tentativas cada) |
| --- | --- |
| 0 ms | FIN 40/40 |
| 2 ms | **RST 40/40** |
| 10 ms | **RST 40/40** |
| 50 ms | **RST 40/40** |

Com o fix: FIN 40/40 em todos os atrasos; 400 POSTs sob 22 threads de carga e
300 POSTs com a suíte completa em paralelo, sem exceção alguma no servidor.

### O que mudou

- `dashboard/server.py`: `Handler._drain_body()` consome o corpo (teto
  `MAX_BODY_BYTES` = 4096, timeout de 1 s) antes de responder a rejeição, nos
  dois caminhos que respondem sem ler. Acima do teto, a conexão é marcada
  para fechar e nunca reutilizar; sem corpo, o descarte não toca no socket.
- `tests/unit/test_dashboard_server.py` (novo): 5 testes da lógica, sem rede.
- `tests/integration/test_dashboard.py`: +3 testes — a regressão com corpo
  atrasado (falha com o mesmo `WinError 10053` sem o fix), spy no call site e
  o caminho normal de socket.

### Verificação

`ruff check`/`format --check` → ok; `pytest` → **207 passed** (eram 199);
`reflow scan`, `reflow lint-robin --all` → ok; `node --test` frontend → 3/3.

### O que esta fase não fez (honestidade)

- O teste de socket bruto com corpo junto **não** pega a corrida sozinho —
  dentro do teto, o `readline` do handler engole corpo e cabeçalho juntos e a
  janela não se abre. Ele continua ali como teste do caminho normal; quem
  fixa a regressão é o teste com corpo atrasado.
- O teto e o timeout do descarte são arbitrários (4096 e 1 s), calibrados no
  que o dashboard aceita hoje, não em carga real de navegador.
- **A pendência do `POST` sem deadline de leitura (ADR-021) segue aberta**:
  o descarte novo só cobre o caminho de rejeição e não resolve o caso geral.
  *Resolvida na Fase 19 (ADR-024): toda requisição passou a ter prazo.*

## Fase 19 — Prazo de leitura por requisição no dashboard (fecha a pendência do ADR-021)

Fechei a última pendência de segurança que eu mesmo tinha registrado: o `POST`
sem deadline de leitura, aberto desde o ADR-021 (Fase 4) e repetido nas listas
da Fase 17 e da Fase 18. Documentado no ADR-024 em
[`docs/decisions.md`](decisions.md).

### O que estava aberto

`dashboard/server.py` fazia `self.rfile.read(length)` num socket **bloqueante
por padrão**. Um cliente que mandasse os cabeçalhos com `Content-Length` e nunca
mandasse o corpo prendia a thread do handler para sempre — e como o servidor é
`ThreadingHTTPServer`, cada conexão dessas vaza uma thread. O mesmo valia para
quem conectava e nem mandava a linha de requisição: o `readline()` do
`handle_one_request` também bloqueava sem prazo.

### A peça que faltava

Investiguei o stdlib antes de implementar, e os dois lados do mecanismo já
existiam: `StreamRequestHandler.setup()` aplica `self.timeout` ao socket quando
ele não é `None`, e `handle_one_request()` já captura `TimeoutError` fechando a
conexão sem traceback. `BaseHTTPRequestHandler` herda `timeout = None` — ou
seja, sem prazo, sempre. A correção é uma linha de classe
(`Handler.timeout = READ_TIMEOUT_SECONDS`, 10 s), não uma implementação própria.

### O que mudou

- `dashboard/server.py`: `Handler.timeout` ligado (10 s, cobrindo linha,
  cabeçalhos e corpo); `do_POST` ganhou ramo `except TimeoutError` **antes** do
  `except (ValueError, OSError)`, respondendo 408 e drenando o corpo antes; o
  `_drain_body` passou a devolver o prazo que encontrou em vez de
  `settimeout(None)`; constantes `READ_TIMEOUT_SECONDS` e
  `DRAIN_TIMEOUT_SECONDS`, com o literal `10` do SSE apontando para a primeira.
- `tests/unit/test_dashboard_server.py`: teste novo do valor de fábrica e teste
  novo de restauração do prazo; asserções do descarte atualizadas para o prazo
  devolvido (não `None`).
- `tests/integration/test_dashboard.py`: +2 testes de socket bruto — corpo que
  nunca chega e conexão ociosa.
- `SECURITY.md`: a pendência saiu da lista do "que ainda não está pronto".

### Verificação

`ruff check`/`format --check` → ok; `pytest` → **211 passed** (eram 207);
`reflow scan`, `reflow lint-robin --all` → ok; `node --test` frontend → 3/3.

Cada teste novo foi conferido **falhando sem o fix**, e um deles falhou pela
razão errada na primeira versão — vale registrar:

- O teste de corpo que nunca chega, com o `server.py` anterior, recebia
  `400 Bad Request` em vez de travar: com um prazo artificial no socket, o
  `TimeoutError` caía no `except (ValueError, OSError)` e virava "corpo
  inválido". É a mentira que o ramo novo corrige.
- O teste de conexão ociosa **passava sem o fix**, e eu peguei isso conferindo:
  ele encurtava o prazo via `monkeypatch`, e isso criava o próprio atributo
  `timeout` que o stdlib lê — o teste entregava de bandeja a proteção que
  deveria provar. Movido o `require` do `Handler.timeout` para **antes** do
  `monkeypatch`, ele agora falha com `veio None` quando o prazo não está ligado.

### O que esta fase não fez (honestidade)

- O prazo de 10 s não foi calibrado por medição: é o número que o SSE já usava,
  folgado para loopback. Não é o resultado de carga real.
- Drenar antes do 408 custa até 1 s extra de thread num cliente que já gastou
  10 s. Decisão deliberada — a alternativa é perder a resposta no RST (ADR-023).
- Nada disto toca Robin: as ações seguem 100% `[não validado]`.

## Fase 20 — Catálogo de subfluxos comuns entre processos

Pedido do usuário: alguns subfluxos se repetem em processos diferentes (não
só chamadas explícitas de bot a bot, já cobertas pela convenção
`TaskBot.run` → `Flow.RunSubflow`), e isso precisa ficar bem mapeado e
sinalizado de forma explícita e profissional no `Main.robin` sempre que
aparecer, para orientar reuso futuro em vez de remontar o mesmo trecho do
zero em cada conversão.

### O que mudou

- `reference/subfluxos-comuns.md` (novo): catálogo de padrões de passos que
  se repetem **entre projetos diferentes**, com status `catalogado`
  (evidência real de dois ou mais projetos) ou `proposto` (hipótese, sem
  evidência ainda). Hoje tem uma entrada `catalogado` com evidência real —
  `obter-credencial-do-cofre` (`CredentialVault.getCredential` →
  `Credentials.GetCredential`), observada em `a360-browser-rest/main.json:3`
  e `a360-excel-vault/main.json:4` — e duas entradas `proposto` (tratamento
  de erro padrão, notificação de falha por e-mail) registradas como
  hipóteses de padrões típicos de RPA, sem evidência nos três projetos de
  exemplo ainda, para não inventar fato onde não há `arquivo:linha`.
- `reference/robin-conventions.md` e `reference/robin-actions.md`: nova
  regra de sinalização (sufixo `_subfluxo_comum_<slug>`, comentário citando
  a entrada catalogada, `FlowControl.Region` rotulada "Subfluxo comum: ...
  (candidato a reuso)"), espelhando o padrão já usado para dependência entre
  bots, mas para o caso sem chamada explícita no legado.
- `.opencode/agents/reflow-pad-converter.md`: instrução para conferir cada
  trecho do flow contra o catálogo na hora de converter, sinalizar entradas
  `catalogado` e registrar candidatos novos (com evidência real) em
  `notas-conversao.md` — nunca editar o catálogo nem promover `proposto`
  para `catalogado` sozinho (permissão de escrita do agent continua restrita
  a `output/*/04-pad/**`).
- `.opencode/agents/reflow-robin-reviewer.md`: quinto item de auditoria,
  conferindo a sinalização completa de subfluxo comum e a evidência real de
  qualquer candidato citado nas notas.
- `.claude/skills/reflow-convert/SKILL.md` e
  `.claude/skills/reflow-convert-review/SKILL.md`: entradas, "o que faz" e
  resumo atualizados para citar o catálogo novo.
- Paridade entre harnesses: `scripts/sync_agents.py` e
  `scripts/sync_copilot.py` rodados depois da mudança nos agents canônicos,
  regenerando os sete espelhos em `.claude/agents/` e os sete
  `.github/chatmodes/*.chatmode.md`; descrição do
  `.github/prompts/reflow-convert-review.prompt.md` também atualizada —
  Claude Code, OpenCode e Copilot seguem a mesma regra na mesma rodada.

### O que esta fase não fez (honestidade)

- Nenhum `Main.robin` já gerado (ex.: `a360-browser-rest`) foi reconvertido
  retroativamente com a nova sinalização — essa conversão tinha só 3 passos
  numa única Região implícita; aplicar a convenção nela é trabalho da
  próxima rodada de `reflow-convert`, não desta fase.
- O catálogo nasce pequeno de propósito: uma entrada com evidência real e
  duas hipóteses sem evidência, em vez de inventar um catálogo "completo" de
  padrões RPA genéricos sem `arquivo:linha` — contraria diretamente a regra
  de `AGENTS.md` de nunca inventar fato ou evidência.
- Nenhum gate determinístico (`reflow lint-robin`) passou a validar a
  sinalização de subfluxo comum — como a convenção equivalente de
  `Flow.RunSubflow`, ela continua sendo responsabilidade do agent de
  conversão e do agent de revisão semântica, nunca do lint estrutural.

## Fase 21 — Lista de subflows padrão do PAD, chamados pelo nome do bot filho

Continuação direta da Fase 20. O usuário informou que, na operação real, um
conjunto fixo de bots/subflows aparece repetidamente sendo chamado pelo
nome em vários processos — e que todos já têm equivalente disponível no
PAD: `MapearFileServer`, `DesmapearFileServer`, `ConsultarCredencialProducao`,
`AcessoPainelServico`, `KillProcessByName` e `Log_Splunk` (este último
descontinuado, substituído pelo Datadog como ferramenta padrão e oficial de
observabilidade do banco). Pediu que o `Main.robin`, ao identificar esses
casos, já marque que deve usar o subflow equivalente já disponível no PAD.

### Por que isto é diferente da Fase 20

A Fase 20 cobre um padrão de **ações que se repetem sem chamada explícita**
no legado (evidência extraída comparando `arquivo:linha` de dois ou mais
projetos). Esta lista é o oposto: são **nomes de bot já chamados
diretamente** pelo legado (`TaskBot.run` com `target`/`botName` igual a um
destes), e a evidência é **confirmação direta do usuário/analista**, não
extração de `input/<projeto>/` — nenhum dos três projetos de exemplo chama
algum destes hoje. Por isso a lista entrou como uma seção própria em
`reference/subfluxos-comuns.md`, com a fonte da evidência registrada
explicitamente, em vez de ser misturada ao catálogo da Fase 20 (que exige
`arquivo:linha` de inventário real).

### O que mudou

- `reference/subfluxos-comuns.md`: nova seção "Subflows padrão já
  existentes no PAD (chamados pelo nome do bot filho)" com uma tabela de 6
  linhas (nome, situação `ativo`/`descontinuado`, observação) e regras
  próprias para o converter e o revisor.
- `reference/robin-conventions.md` e `reference/robin-actions.md`: a regra
  já existente de marcação de `TaskBot.run`/`Flow.RunSubflow` ganhou um
  parágrafo extra — se o bot filho bater com um nome **ativo** dessa tabela,
  o comentário do passo diz que é subflow padrão já disponível (reaproveitar,
  nunca reimplementar); se bater com `Log_Splunk` (ou outro nome marcado
  **descontinuado** no futuro), o passo vira `TODO reflow` citando o
  substituto, nunca aponta para o nome antigo como válido.
- `.opencode/agents/reflow-pad-converter.md`: instrução para cruzar toda
  dependência de bot contra essa tabela e aplicar a marcação extra.
- `.opencode/agents/reflow-robin-reviewer.md`: sexto item de auditoria,
  conferindo essa marcação extra (subflow padrão vs. descontinuado).
- Paridade entre harnesses: `scripts/sync_agents.py` e
  `scripts/sync_copilot.py` rodados depois da mudança, regenerando os 7
  espelhos `.claude/agents/` e os 7 `.github/chatmodes/*.chatmode.md`.

### Verificação

`ruff check`/`format --check` → ok; `pytest` → **225 passed**; `reflow
scan`, `reflow lint-robin --all` → ok.

### O que esta fase não fez (honestidade)

- Não sei o nome exato do subflow Datadog que substitui `Log_Splunk` — a
  regra manda o converter gerar `TODO reflow` pedindo esse nome ao analista,
  nunca inventá-lo.
- A lista é mantida manualmente (edição humana direta no arquivo); o
  `reflow-pad-converter` nunca adiciona, remove ou muda a `Situação` de uma
  linha sozinho — mesma cautela da Fase 20 para o catálogo baseado em
  evidência.
- Nenhum export A360 real ainda cita um destes seis nomes para validar a
  marcação de ponta a ponta — fica para quando um export real chegar.

## Fase 22 — Bug real: `Main.robin` com LF puro em vez de CRLF (não colava no PAD)

O usuário reportou que, nas duas últimas conversões testadas, o `Main.robin`
"veio formatado estranho" e nenhuma linha conseguia ser copiada e colada no
PAD sem erro — nem as declarações de variável (`cfg_`/`in_`/`out_`), nem um
bloco `IF`...`END`. Pedido: corrigir de forma definitiva.

### Diagnóstico

Investiguei os dois `Main.robin` já commitados
(`output/a360-browser-rest/04-pad/.../Main.robin` e o de `05-test/`) byte a
byte. `.gitattributes` declara `*.robin text eol=crlf` (CRLF obrigatório,
porque o PAD roda no Windows), mas `git ls-files --eol` mostrou
`i/lf w/lf attr/text eol=crlf` nos dois — ou seja, tanto o índice quanto a
working tree estavam em **LF puro**, nunca renormalizados depois que a
regra `eol=crlf` entrou no `.gitattributes`. Confirmei a causa raiz: o
`Main.robin` é escrito por um agent de LLM (`reflow-pad-converter`/
`reflow-pad-tester`) através de uma ferramenta de escrita de arquivo que não
expõe controle sobre o byte de quebra de linha — testei diretamente e ela
grava `\n` cru, nunca `os.linesep`, em qualquer SO. Um arquivo LF puro é a
causa clássica do bug do Bloco de Notas do Windows (e de controles de texto
parecidos): as linhas aparentam estar juntas ou se comportam de forma
inconsistente ao selecionar/colar — bate com "a formatação veio estranha" e
"não consegui copiar nenhum dos exemplos".

Também expliquei ao usuário a segunda causa, não um bug: hoje **toda** ação
da whitelist (`reference/robin-actions.md`) ainda está `[não validado]` —
o placeholder entre colchetes é texto explicativo, nunca sintaxe real do
PAD, porque `AGENTS.md` proíbe inventar sintaxe Robin mesmo que pareça
óbvia. Para um `Variables.SetVariable`/`Conditionals.IfElse` colarem como
ação real, alguém precisa montar a ação de verdade no designer, copiar
(Ctrl+C) e colar no lugar do placeholder — processo já documentado em
`robin-actions.md`/`README.md`, não alterado nesta fase.

### O que mudou

- `reflow/robin/lint.py`: `_check_robin_eol()` — novo achado
  `eol_lf_sem_cr` quando um `Main.robin` tem qualquer linha terminada em
  `\n` sem `\r` antes (opera em bytes crus, nunca em texto já traduzido por
  leitura universal de quebra de linha, que apagaria o problema);
  `normalize_robin_eol(path)` e `fix_robin_eol(root, project=None)` —
  normalizam para CRLF, byte a byte, sem depender de tradução de quebra de
  linha do SO. `_lint_one()` passou a ler bytes crus e decodificar, em vez
  de `read_text()` (que já fazia a tradução universal).
- `reflow/cli.py`: novo subcomando `fix-robin-eol [<projeto>|--all]`.
- `reflow/robin/__init__.py`: exporta `fix_robin_eol`.
- `AGENTS.md`, `README.md`: comando novo documentado; passo explícito de
  "rode `fix-robin-eol` antes de colar" na seção "Do flow para o PAD".
- `reference/robin-conventions.md`: convenção nova — CRLF sempre, com o
  porquê e o comando que corrige.
- `.claude/skills/reflow-convert/SKILL.md` e
  `.claude/skills/reflow-test/SKILL.md`: `fix-robin-eol` roda depois do
  agent escrever o `Main.robin` e antes do `lint-robin` — `reflow-test` não
  rodava `lint-robin` nenhuma vez antes desta fase, passou a rodar.
- `output/a360-browser-rest/04-pad/uc-01-browser-rest/Main.robin` e
  `output/a360-browser-rest/05-test/test_uc-01-browser-rest/Main.robin`:
  normalizados para CRLF com o comando novo (só quebra de linha mudou,
  nenhum caractere de conteúdo).
- `tests/unit/test_lint_robin.py` (+9 testes: achado novo, mistura de EOL,
  `normalize_robin_eol` idempotente/sem duplicar `\r`, `fix_robin_eol` em
  lote) e `tests/integration/test_cli_end_to_end.py` (+1 teste de ponta a
  ponta via CLI: LF puro reprova o lint, `fix-robin-eol` corrige, lint passa
  depois).

### Verificação

`ruff check`/`format --check` → ok; `pytest` → **234 passed** (eram 225, +9
novos); `reflow scan`, `reflow lint-robin --all` → ok, inclusive contra os
dois `Main.robin` já normalizados.

### O que esta fase não fez (honestidade)

- **Não inventei sintaxe real do PAD para nenhuma ação.** O bug corrigido é
  só de quebra de linha — ele garante que o *placeholder* (ou, no futuro,
  o snippet real já validado) chegue inteiro e colável no PAD. Fazer uma
  linha de `Variables.SetVariable` virar de fato uma ação "Definir
  Variável" ao colar exige a sintaxe real do PAD, que só entra em
  `robin-actions.md` pelo processo já existente (montar no designer, copiar
  com Ctrl+C, colar no lugar do placeholder) — pedi ao usuário o texto real
  copiado do PAD para `Variables.SetVariable` e `Conditionals.IfElse` em vez
  de arriscar uma sintaxe "óbvia", mas possivelmente errada.
- A normalização dos dois `Main.robin` já commitados foi manual (rodei o
  comando eu mesmo); nenhuma migração automática varre `output/` inteiro
  sozinha fora de uma chamada explícita a `fix-robin-eol`.
- `reflow lint-robin` continua sem interpretar a sintaxe interna do Robin
  (ver docstring do módulo) — o achado novo é puramente sobre bytes de
  quebra de linha, nunca sobre se o conteúdo colado é uma ação válida do
  PAD.
