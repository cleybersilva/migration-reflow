---
name: reflow
description: Orquestra o pipeline completo (extract → document → classify → segunda opinião → checkpoint humano → convert → revisão do Robin → test) para um projeto, ou para todos em input/ quando nenhum nome é dado. Retoma de onde o projeto parou e roda o relatório de lote no final. Use quando o usuário pedir para migrar, processar ou rodar o reflow ponta a ponta.
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
4. `reflow-classify-review` — segunda opinião independente, sempre, mesmo
   quando o veredito for `NOT_PAD` (uma divergência aqui pode significar que
   o projeto deveria ter ido para o PAD, ou vice-versa).
5. **Checkpoint humano**: se `verdict == NOT_PAD` (o original, não o da
   revisão), mostre o motivo e **encerre este projeto aqui** (só documentação
   e classificação, sem conversão). Se `verdict` for `PAD` ou `PARTIAL`,
   mostre veredito/escopo/alertas **e o resultado da segunda opinião**
   (`agreement: concorda | diverge`, com destaque se divergiu) e peça
   confirmação explícita antes de continuar.
6. `reflow-convert` (só depois do "ok" do checkpoint).
7. `reflow-convert-review` — auditoria semântica do `Main.robin` recém
   gerado, depois do `lint-robin` passar. Mostre os achados antes de seguir;
   se houver achados sérios (ex.: maioria do flow em `TODO reflow`), pergunte
   se o analista quer rodar `reflow-convert` de novo antes de testar.
8. `reflow-test`.

Em lote, processe um projeto por vez, do começo ao fim, antes de passar para
o próximo — nunca misture fases de projetos diferentes na mesma resposta.

## Ao final do lote

Rode `uv run python -m reflow report` e mostre `output/_batch-report.md`.

## Agent chamado

- Nenhum diretamente — delega para as skills de fase, que chamam os agents
  `reflow-documenter`, `reflow-classifier`, `reflow-classification-reviewer`,
  `reflow-pad-converter`, `reflow-robin-reviewer` e `reflow-pad-tester`.

## O que sobrescreve

- O mesmo que cada fase interna sobrescreve, nada além disso.

## Aviso de fases desatualizadas

- Propague o aviso de cada fase interna; se encontrar `stale_phases` não
  vazio ao retomar, avise antes de seguir.

## Resumo a mostrar

- Por projeto: fase em que parou, veredito (se houve classificação) e se foi
  convertido. No lote: a tabela final de `output/_batch-report.md`.
