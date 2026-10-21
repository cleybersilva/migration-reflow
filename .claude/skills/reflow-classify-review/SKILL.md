---
name: reflow-classify-review
description: Dá uma segunda opinião independente sobre a classificação PAD/PARTIAL/NOT_PAD já feita por reflow-classify, reaplicando a rubrica do zero e apontando concordância ou divergência antes do checkpoint humano. Use depois de reflow-classify e antes de aprovar a conversão, para reduzir o risco de um veredito errado chegar ao checkpoint sem segunda leitura.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-classify-review

## Entradas

- `output/<projeto>/01-inventory/inventory.json`, `02-docs/` e
  `03-classification/classification.md` (veredito já registrado pelo
  `reflow-classifier`).
- `reference/classification-rubric.md`.

## Pré-condição

- `03-classification/classification.md` tem que existir (rodar
  `reflow-classify` antes). Sem ele, pare e diga para classificar primeiro.

## O que faz

Chama o agent **reflow-classification-reviewer** para reclassificar o
projeto do zero, sem copiar o raciocínio do primeiro veredito, e gravar
`output/<projeto>/03-classification/review.md` com frontmatter:

```yaml
original_verdict: PAD | PARTIAL | NOT_PAD
reviewed_verdict: PAD | PARTIAL | NOT_PAD
agreement: concorda | diverge
```

Isto **não substitui** o checkpoint humano — é informação extra para o
analista decidir com mais segurança. Se `agreement: diverge`, isso **tem**
que aparecer com destaque no checkpoint antes de qualquer "ok".

## Agent chamado

- `reflow-classification-reviewer`.

## O que sobrescreve

- Somente `output/<projeto>/03-classification/review.md`. Nunca toca em
  `classification.md` — esse arquivo continua sendo só do `reflow-classifier`.

## Aviso de fases desatualizadas

Se o projeto for reclassificado depois (`reflow-classify` rodar de novo),
`review.md` fica desatualizado até `reflow-classify-review` rodar outra vez —
avise antes do checkpoint se as datas não baterem.

## Resumo a mostrar

- `original_verdict`, `reviewed_verdict` e `agreement`. Se divergiram, mostre
  o motivo da divergência (qual critério mudou o resultado) em destaque,
  antes de qualquer pedido de aprovação do checkpoint.
