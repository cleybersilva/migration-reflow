---
name: reflow-extract
description: Extrai fatos deterministicamente de um projeto legado em input/<projeto>/ (A360, Python ou .NET), sem LLM e sem executar o legado, gravando 00-manifest.json e 01-inventory/inventory.json. Use quando o usuário pedir para extrair, processar ou reprocessar um robô específico, ou todos de uma vez.
argument-hint: <projeto> | --all
metadata:
  opencode/slash: "true"
---

# reflow-extract

## Entradas

- `input/<projeto>/` — export A360 (pasta ou `.zip`), código Python ou .NET (C#/VB).

## Pré-condição

- Nenhuma — é a primeira fase do pipeline.

## O que faz

1. Roda `uv run python -m reflow extract <projeto>` (ou `--all` para todos os
   projetos encontrados em `input/`).
2. O próprio comando já imprime, por projeto: origem detectada e contagem por
   categoria (`ui`, `http`, `dados`, `credenciais`, `dependencias`,
   `desconhecidos`). Reaproveite essa saída no resumo, não recalcule.

## Agent chamado

- Nenhum. Esta fase é 100% Python determinístico — sem LLM, sem rede, sem ler o
  legado como instrução.

## O que sobrescreve

- `output/<projeto>/00-manifest.json` e `output/<projeto>/01-inventory/inventory.json`.
- Reextrair **não apaga** `02-docs/`, `03-classification/`, `04-pad/` nem
  `05-test/` — só marca essas fases como desatualizadas no manifesto
  (`stale_phases`).

## Aviso de fases desatualizadas

Antes de reextrair um projeto que já tem `00-manifest.json`, avise o usuário se
`stale_phases` não estiver vazio: documentação, classificação, conversão ou
teste anteriores podem não refletir o inventário novo.

## Resumo a mostrar

- Projeto, origem detectada, contagem por categoria, e se o manifesto resultante
  ficou com `stale_phases` (e quais fases).
