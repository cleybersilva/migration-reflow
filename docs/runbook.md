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

## Reextração invalidou uma fase posterior

Normal — `00-manifest.json` marca as fases seguintes como `stale_phases`
(não apaga nada). Rode a fase de novo para atualizar, ou ignore o aviso se a
mudança no legado não afetar aquela fase.
