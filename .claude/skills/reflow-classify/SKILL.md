---
name: reflow-classify
description: Classifica um projeto já documentado como PAD, PARTIAL ou NOT_PAD aplicando reference/classification-rubric.md, gravando 03-classification/classification.md. Use depois de reflow-document, quando o usuário pedir para decidir se um robô vale a pena ir para o PAD.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-classify

## Entradas

- `output/<projeto>/01-inventory/inventory.json` e `02-docs/`.
- `reference/classification-rubric.md`.

## Pré-condição

- `02-docs/` tem que existir (rodar `reflow-document` antes). Sem ele, pare e
  diga para documentar primeiro.

## O que faz

Chama o agent **reflow-classifier** (criado na Fase 6 — se ainda não existir,
avise em vez de simular) para aplicar a rubrica à risca e gravar
`output/<projeto>/03-classification/classification.md` com frontmatter:

```yaml
verdict: PAD | PARTIAL | NOT_PAD
pad_use_cases:
  - <caso de uso que vai para o PAD>
alerts:
  - <alerta A1-A5 identificado>
```

## Agent chamado

- `reflow-classifier`.

## O que sobrescreve

- Somente `output/<projeto>/03-classification/**`.

## Aviso de fases desatualizadas

Se `04-pad/` ou `05-test/` já existirem, avise que ficam desatualizados quando
o veredito muda — principalmente se um projeto antes `PAD` virar `NOT_PAD` (a
conversão anterior deixa de valer).

## Resumo a mostrar

- Veredito (`PAD`/`PARTIAL`/`NOT_PAD`), os `pad_use_cases` e os `alerts`
  identificados. Se `NOT_PAD`, deixe claro que o projeto encerra aqui — sem
  conversão.
