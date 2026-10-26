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

- **CI continua não existindo** (`.github/workflows`) — fora do escopo
  destas quatro fases de segurança, segue como pendência aberta.
- Não ampliei a leitura A360 para JSON aninhado: decidi avisar em vez de
  inventar cobertura sem fixture real que mostre o formato do export.
- Os tetos de orçamento são **genéricos, não calibrados em robô real**
  (nenhum export verdadeiro passou por aqui ainda); se um export legítimo
  estourar, o ajuste é consciente e documentado, não um chute disfarçado.
- Nada foi validado num PAD real; a whitelist segue 100% `[não validado]`.
