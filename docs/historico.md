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
