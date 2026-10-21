---
name: reflow
description: Orquestra o pipeline completo (extract → document → classify → checkpoint humano → convert → test) para um projeto, ou para todos em input/ quando nenhum nome é dado. Retoma de onde o projeto parou e roda o relatório de lote no final. Use quando o usuário pedir para migrar, processar ou rodar o reflow ponta a ponta.
argument-hint: "[<projeto>] (vazio = todos)"
metadata:
  opencode/slash: "true"
---

# reflow (orquestrador)

## Entradas

- Nome do projeto (opcional). Vazio = processa todos os projetos em `input/`,
  um por vez.

## Pré-condição

- Nenhuma própria — cada fase interna tem a sua. Olhe `00-manifest.json` (se
  existir) para decidir onde retomar: não reexecute uma fase cujo artefato já
  existe e não está em `stale_phases`.

## O que faz, por projeto

1. `reflow-extract` — sempre, a menos que o inventário já exista e esteja em dia.
2. `reflow-document`.
3. `reflow-classify`.
4. **Checkpoint humano**: se `verdict == NOT_PAD`, mostre o motivo e **encerre
   este projeto aqui** (só documentação e classificação, sem conversão). Se
   `verdict` for `PAD` ou `PARTIAL`, mostre veredito/escopo/alertas e peça
   confirmação explícita antes de continuar.
5. `reflow-convert` (só depois do "ok" do checkpoint).
6. `reflow-test`.

Em lote, processe um projeto por vez, do começo ao fim, antes de passar para
o próximo — nunca misture fases de projetos diferentes na mesma resposta.

## Ao final do lote

Rode `uv run python -m reflow report` e mostre `output/_batch-report.md`.

## Agent chamado

- Nenhum diretamente — delega para as skills de fase, que chamam os agents
  `reflow-documenter`, `reflow-classifier`, `reflow-pad-converter` e
  `reflow-pad-tester` (Fase 6).

## O que sobrescreve

- O mesmo que cada fase interna sobrescreve, nada além disso.

## Aviso de fases desatualizadas

- Propague o aviso de cada fase interna; se encontrar `stale_phases` não
  vazio ao retomar, avise antes de seguir.

## Resumo a mostrar

- Por projeto: fase em que parou, veredito (se houve classificação) e se foi
  convertido. No lote: a tabela final de `output/_batch-report.md`.
