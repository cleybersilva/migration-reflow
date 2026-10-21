---
name: reflow-document
description: Gera a documentação de negócio e técnica (02-docs/, inclusive o diagrama de arquitetura Mermaid) de um projeto já extraído, a partir do inventário determinístico. Use depois de reflow-extract, quando o usuário pedir para documentar, explicar ou gerar a arquitetura de um robô.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-document

## Entradas

- `output/<projeto>/01-inventory/inventory.json`.
- `input/<projeto>/` — só os trechos já citados (com `arquivo:linha`) pelo
  inventário; nunca ler o legado além disso.
- `reference/templates/docs/*.md` — modelo de cada arquivo a gerar.

## Pré-condição

- `01-inventory/inventory.json` tem que existir (rodar `reflow-extract` antes).
  Sem ele, pare e diga para extrair primeiro.

## O que faz

Chama o agent **reflow-documenter** (criado na Fase 6 — se ainda não existir
neste repositório, avise o usuário em vez de simular o resultado) para gerar,
em `output/<projeto>/02-docs/`: `README.md`, `use-cases.md`, `process-flow.md`,
`data-sources.md`, `integrations.md`, `business-rules.md`, `risks.md` e
`architecture.md` (com o diagrama Mermaid — atende ao pedido R3 da reunião).

## Agent chamado

- `reflow-documenter`.

## O que sobrescreve

- Somente `output/<projeto>/02-docs/**`. Nunca toca em `01-inventory/`,
  `03-classification/`, `04-pad/` ou `05-test/`.

## Aviso de fases desatualizadas

Se `03-classification/classification.md` já existir, avise que ela **não** se
atualiza sozinha: documentar de novo pode mudar `02-docs/` sem que a
classificação reflita isso até `reflow-classify` rodar outra vez.

## Resumo a mostrar

- Lista dos arquivos gerados/atualizados em `02-docs/`.
- Confirmação de que `architecture.md` tem um diagrama Mermaid com as
  integrações encontradas (ou aviso se o projeto não tiver nenhuma).
