# Runbook — operação do dia a dia e troubleshooting

## Preparação

```powershell
uv sync
git config core.hooksPath .githooks
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Se o hook bloquear um commit porque `scan` ou `lint-robin` reprovaram, **não
desabilite o hook** (`--no-verify`) — corrija o achado. Veja os dois achados
mascarados que ele mesmo imprime (`arquivo:linha` + padrão).

## "nenhuma origem suportada (A360, Python, .NET) em ..."

`input/<projeto>/` não tem nenhum `.json`/`.zip` (A360), `.py` (Python) ou
`.cs`/`.vb`/`.dll`/`.exe` (.NET) reconhecível. Confirme que o projeto está em
`input/<nome-minusculo>/` (letras minúsculas, números, hífen ou underscore) e
que o conteúdo foi mesmo copiado para dentro da pasta, não para um nível acima.

## IAra (ou outro provider) indisponível

`reflow extract`, `scan`, `lint-robin` e `report` são Python puro — funcionam
sem nenhum LLM configurado. Só as skills que chamam agent (`reflow-document`,
`reflow-classify`, `reflow-convert`, `reflow-test`, `reflow-truth-table`)
precisam de um provider. Se a IAra estiver fora do ar: confirme
`IARA_BASE_URL`/`IARA_API_KEY`/`IARA_MODEL` no ambiente do processo do
harness (nunca só no `.env` sem o harness carregá-lo), e teste com
`/models` dentro do opencode. Enquanto não resolver, continue trabalhando nas
fases determinísticas (extração, tabela verdade manual, revisão da whitelist).

## Harness `refold` (plano B secundário)

Quando nenhum dos três harnesses estiver disponível (ADR-033):

```powershell
uv run python -m refold check                                   # IARA_* presentes e https
uv run python -m refold run <agent> <projeto> --dry-run         # pré-condições, sem rede
uv run python -m refold run <agent> <projeto>
```

- `variáveis de ambiente ausentes`: exporte `IARA_BASE_URL` (terminando em `/v1`),
  `IARA_API_KEY` e `IARA_MODEL` no processo. `IARA_BASE_URL` em http só vale para loopback.
- `API respondeu 401/403`: o proxy pode exigir o cabeçalho `Authorization` no esquema Bearer; tente
  `REFOLD_AUTH=bearer`. 404 em `/v1/messages` indica que o endpoint não fala o protocolo
  Anthropic Messages (o OpenCode usa `/v1/chat/completions`).
- `checkpoint em formato legado`: quem aprova regrava com
  `reflow checkpoint <projeto> --approve`; o refold não converte sem o hash.
- `o agent não terminou`: estourou o `steps` do agent ou `max_tokens`. Veja o log em
  `.refold-runs/` (turnos e ferramentas, sem conteúdo) e rode de novo; nenhuma fase é
  fechada nesse caso.

## Classificação recusada pelo gate

`reflow classify-check <projeto>` lista cada problema; `phase-done 03-classification` e
`checkpoint --approve` recusam enquanto houver `[erro]` (ADR-034).

- `verdict inválido`: um de `PAD`, `PARTIAL`, `NOT_PAD`, sem aspas nem comentário.
- `evidência ...: nó não existe no inventário`: em A360 a linha é o campo `line` do fato no
  inventário, não a linha física do JSON.
- `desatualizada`: o veredito mudou depois da revisão; rode `reflow-classify-review`.
- `[aviso] DIVERGÊNCIA`: não bloqueia, mas leia o `review.md` antes de aprovar.
- Não edite o artefato à mão para passar: chame o agent de novo apontando o erro.

## Eval da classificação reprovado

Rode depois de mudar a rubrica, um prompt de classificação ou o modelo (skill
`reflow-classify-eval`). Veja os casos em `output/_classification-eval.md`. Não ajuste
rótulo, rubrica ou prompt só para a nota subir: divergência entre rótulo e agents vai para o
analista. `prepare` descarta os vereditos anteriores; `clean` remove `input/eval-*` e
`output/eval-*` (só esses).

## Robin não cola no PAD

O `Main.robin` é texto puro para colar (Ctrl+V) no designer, não um arquivo
para importar. Se o PAD não reconhecer o conteúdo: confirme que nenhuma ação
ficou como `[não validado — TODO reflow: ...]` sem ter sido substituída pelo
snippet real copiado do designer — esse placeholder nunca é Robin válido, de
propósito (ver `reference/robin-actions.md`).

## Uma ação `[não validado]` falhou ao colar/rodar

Esperado — é exatamente o que `[não validado]` significa. Monte a ação
manualmente no designer, confirme que funciona, copie (Ctrl+C) e substitua o
placeholder em `robin-actions.md`; só então mude o status para
`[validado PAD: rodou]`. Nunca promova sem ter rodado de verdade.

## Contexto grande demais / harness se perde no repositório

Rode fase por fase (`/reflow-extract`, depois `/reflow-document`, etc.) em
vez do orquestrador `/reflow` completo, e processe **um projeto por vez** —
nunca misture fases de projetos diferentes na mesma conversa. Se um projeto
tiver muitos arquivos de entrada, extraia-o isoladamente antes de pedir
documentação.

## Deploy do GitHub Pages falhou

O job `deploy (GitHub Pages)` só roda depois de `checks` e `frontend`, em push ou
`workflow_dispatch` na main.

- **Timeout no deploy:** não reexecute só o job (falha com "Multiple artifacts named
  github-pages"). Dispare uma execução nova: `gh workflow run ci.yml --ref main`.
- **HTTP 400 "due to in progress deployment. Please cancel <sha> first":** um deploy
  anterior ainda consta como em andamento do lado do Pages. Consulte o estado com
  `gh api repos/cleybersilva/migration-reflow/pages/deployments/<sha>`; se ainda estiver
  em andamento, cancele com `gh api -X POST .../pages/deployments/<sha>/cancel` (ou espere
  o timeout). Quando aparecer `deployment_cancelled` ou terminal, dispare uma execução
  nova como acima.
- Depois de publicar, ressincronize o painel privado (Artifact): copie o
  `docs/data.json` e regrave o `pipeline.json` com a run verde.

## Reextração invalidou uma fase posterior

Normal — `00-manifest.json` marca as fases já existentes como `stale_phases`
(não apaga nada). Rode a fase de novo (a skill fecha com
`reflow phase-done <projeto> <fase>`, que marca as seguintes já existentes), ou ignore o aviso se a
mudança no legado não afetar aquela fase.
