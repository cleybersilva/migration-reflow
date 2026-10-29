---
name: reflow-test
description: Gera um flow de teste (05-test/) com 3 a 5 cenários para o Main.robin já convertido. Use depois de reflow-convert. O teste gerado aqui nunca é um PASS/FAIL real — isso só existe depois do analista rodar o flow de teste de verdade no PAD.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-test

## Entradas

- `output/<projeto>/04-pad/<flow>/Main.robin`.
- `output/<projeto>/02-docs/use-cases.md` e `business-rules.md`.
- `reference/robin-conventions.md`, `reference/robin-actions.md`.

## Pré-condição

- `04-pad/<flow>/Main.robin` tem que existir (rodar `reflow-convert` antes e
  ter passado pelo checkpoint).

## O que faz

Chama o agent **reflow-pad-tester** (criado na Fase 6 — se ainda não existir,
avise em vez de simular) para gerar `output/<projeto>/05-test/test_<flow>/`
com 3 a 5 cenários (`CT-01`, `CT-02`, ...) derivados de `use-cases.md` e
`business-rules.md`, cada um com passos e resultado esperado. Ao final, roda
`uv run python -m reflow fix-robin-eol <projeto>` (o `Main.robin` de teste
precisa de CRLF para colar no PAD, igual ao da conversão — ver
`reference/robin-conventions.md`) e depois `uv run python -m reflow
lint-robin <projeto>`.

## Agent chamado

- `reflow-pad-tester`.

## O que sobrescreve

- Somente `output/<projeto>/05-test/**`.

## Aviso — teste gerado ≠ teste executado

Deixe isto explícito no resumo e no próprio `README.md` do teste: os cenários
aqui são **gerados**, nunca **executados**. Não existe PASS/FAIL real até o
analista colar e rodar o flow de teste no PAD (ver `docs/runbook.md`).

## Resumo a mostrar

- Quantos cenários foram gerados e seus nomes (`CT-01`...), o resultado do
  `lint-robin` (passou ou os achados), e o aviso acima.
