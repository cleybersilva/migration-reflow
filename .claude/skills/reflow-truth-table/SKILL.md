---
name: reflow-truth-table
description: Propõe novas linhas para reference/a360-to-pad.md a partir dos unknown_commands encontrados na extração, sempre como "pendente de classificação" — nunca como ação já validada. Use quando o usuário quiser expandir a tabela verdade A360 a partir de um projeto já extraído.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-truth-table

## Entradas

- `output/<projeto>/01-inventory/inventory.json` → campo `unknown_commands`.
- `reference/a360-to-pad.md` (para não duplicar linha já existente).

## Pré-condição

- `01-inventory/inventory.json` tem que existir.

## O que faz

Chama o agent **reflow-truth-table-curator** (criado na Fase 6 — se ainda não
existir, avise em vez de simular) para, a partir de cada comando em
`unknown_commands`, propor uma linha nova em `reference/a360-to-pad.md` com
status `pendente de classificação` e a coluna "Ação PAD equivalente" vazia
(`—`) — nunca inventar a ação PAD nesta etapa.

## Agent chamado

- `reflow-truth-table-curator`.

## O que sobrescreve

- Somente `reference/a360-to-pad.md`, e só por **adição** de linha nova.
  Nunca edita ou remove uma linha já existente, principalmente as marcadas
  `validado`.

## Aviso de fases desatualizadas

Não aplicável — este comando não gera artefato de fase, só alimenta a
referência compartilhada entre projetos.

## Resumo a mostrar

- Quantas linhas novas foram propostas e quais comandos elas cobrem. Deixe
  claro que toda linha nova continua `pendente de classificação` até alguém
  validar a ação de verdade no PAD (ver `robin-actions.md`).
