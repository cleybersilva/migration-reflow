---
name: reflow-convert
description: Converte um projeto classificado como PAD ou PARTIAL em um Main.robin, só com ações da whitelist, e roda o lint-robin. Use depois do checkpoint humano aprovar a conversão — nunca antes, e nunca para um projeto NOT_PAD.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-convert

## Entradas

- `output/<projeto>/01-inventory/inventory.json`, `02-docs/` e
  `03-classification/classification.md`.
- `reference/robin-actions.md` (whitelist), `reference/a360-to-pad.md` (tabela verdade) e
  `reference/subfluxos-comuns.md`, usados pelo gerador e pelo pacote de contexto.

## Pré-condição

- `03-classification/classification.md` tem que existir **e** `verdict` tem
  que ser `PAD` ou `PARTIAL`. Se for `NOT_PAD`, pare — não existe conversão
  para `NOT_PAD`.

## Checkpoint humano (obrigatório, antes de converter)

Mostre o veredito, o escopo que vai para o PAD (`pad_use_cases`) e os `alerts`
da classificação, e peça confirmação explícita antes de gerar qualquer
`Main.robin`. A gravação é feita **por quem decide**, na CLI, nunca editando
o JSON à mão:

```text
uv run python -m reflow checkpoint <projeto> --approve   # ou --reject
uv run python -m reflow checkpoint <projeto> --status    # confirma o que está gravado
```

O comando recusa a gravação se `input/<projeto>/` mudou desde o `extract`,
se ainda não existe `03-classification/` ou se o veredito é `NOT_PAD`.
Sem esse registro aprovado no `00-manifest.json` → `checkpoint`, não
converta.

## O que faz

A conversão não escreve Robin do zero: gera uma base determinística e otimiza (ADR-035).
Depois do checkpoint aprovado:

1. `uv run python -m reflow generate <projeto>` monta, sem LLM, `04-pad/<flow>/Main.robin`,
   `Main.generated.robin` (a base), `generation.json`, `README.md` e `notas-conversao.md`.
   Ação fora da whitelist, comando sem mapeamento e elemento de UI viram `# TODO reflow`.
2. `uv run python -m reflow optimize-needed <projeto>`. Se responder `não`, pule os passos 3 e 5:
   a base fica como resultado (ADR-036). Se responder `sim`, rode
   `uv run python -m reflow context-pack <projeto> reflow-robin-optimizer`, que monta o
   contexto só com os flows que têm recurso aberto.
3. Chame o agent **reflow-robin-optimizer**, indicando esse arquivo. Ele só reorganiza, nomeia,
   liga variáveis e sinaliza subfluxo comum catalogado (`reference/subfluxos-comuns.md`).
   Não trave a migração se ele falhar: a base segue válida.
4. `uv run python -m reflow fix-robin-eol <projeto>`, depois
   `uv run python -m reflow lint-robin <projeto>`.
5. `uv run python -m reflow optimize-check <projeto> --restore`. Se reprovar, o comando devolve
   a base; rode o `fix-robin-eol` e o `lint-robin` de novo e avise o que foi descartado.

## Fechar a fase no manifesto

Ao final depois do `lint-robin` passar, rode `uv run python -m reflow phase-done <projeto> 04-pad`:
tira `04-pad` de `stale_phases` e marca como desatualizadas as fases seguintes
que já existem (foram geradas a partir da versão anterior). O comando recusa
se `input/<projeto>/` mudou desde o `extract` ou se a fase não deixou o
artefato esperado — nesse caso, não feche a fase.

## Agent chamado

- `reflow-robin-optimizer`.

## O que sobrescreve

- Somente `output/<projeto>/04-pad/**`. O `reflow generate` recusa sobrescrever um
  `Main.robin` alterado depois da geração, salvo com `--force`, que só um pedido explícito
  do analista justifica.

## Aviso de fases desatualizadas

Se `05-test/` já existir, avise que o teste gerado anteriormente pode não
corresponder ao `Main.robin` novo — recomende rodar `reflow-test` de novo.

## Resumo a mostrar

- Se a otimização foi aceita ou descartada, flows gerados, quantas ações vieram da whitelist vs. quantas ficaram como
  `TODO reflow`, o resultado do `lint-robin` (passou ou os achados), e
  quantos passos foram sinalizados como subfluxo comum catalogado ou como
  candidato a novo subfluxo comum.

## Próximo passo recomendado

Depois do `lint-robin` passar, rode `reflow-convert-review` para uma
auditoria semântica do `Main.robin` (cobertura de caso de uso, densidade de
`TODO reflow`, nomenclatura) antes de gerar o teste.
