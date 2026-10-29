---
name: reflow-convert-review
description: Audita semanticamente um Main.robin já convertido e aprovado no lint estrutural, verificando cobertura dos casos de uso, densidade de TODO reflow, convenções de nomenclatura, sinalização de subfluxos comuns catalogados e consistência com notas-conversao.md. Use depois de reflow-convert e antes de reflow-test, para pegar problemas que o lint determinístico não verifica.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-convert-review

## Entradas

- `output/<projeto>/04-pad/<flow>/Main.robin`, `README.md` e
  `notas-conversao.md`.
- `output/<projeto>/02-docs/use-cases.md` e `business-rules.md`.
- `reference/robin-conventions.md`, `reference/robin-actions.md`,
  `reference/subfluxos-comuns.md`.

## Pré-condição

- `04-pad/<flow>/Main.robin` tem que existir **e** já ter passado por
  `uv run python -m reflow lint-robin <projeto>` sem achados. Este agent
  audita o que o lint estrutural não verifica — não substitui o lint.

## O que faz

Chama o agent **reflow-robin-reviewer** para verificar, por flow: cobertura
dos `pad_use_cases` e de `business-rules.md`, densidade de `TODO reflow`,
convenções de nomenclatura (`step_`/`in_`/`out_`/`cfg_`, snake_case),
sinalização correta de subfluxos comuns catalogados em
`reference/subfluxos-comuns.md` (e evidência real de qualquer candidato a
novo subfluxo comum citado nas notas) e consistência entre
`notas-conversao.md` e o conteúdo real do `Main.robin`.
Grava `output/<projeto>/04-pad/<flow>/review.md` com os achados — mesmo
quando não encontra nenhum.

## Agent chamado

- `reflow-robin-reviewer`.

## O que sobrescreve

- Somente `output/<projeto>/04-pad/<flow>/review.md`. Nunca edita
  `Main.robin`, `README.md` ou `notas-conversao.md` — correção é sempre uma
  nova rodada de `reflow-convert`.

## Aviso de fases desatualizadas

Se `reflow-convert` rodar de novo depois (`Main.robin` mudar), `review.md`
fica desatualizado até `reflow-convert-review` rodar outra vez.

## Resumo a mostrar

- Quantos achados, por categoria (cobertura, `TODO reflow`, nomenclatura,
  sinalização de subfluxo comum, consistência de notas), e se o flow está
  pronto para `reflow-test` ou precisa de outra rodada de `reflow-convert`
  primeiro.
