---
mode: agent
description: Extrai fatos deterministicamente de um projeto legado em input/<projeto>/ (A360, Python ou .NET), sem LLM e sem executar o legado, gravando 00-manifest.json e 01-inventory/inventory.json.
---

Leia e siga `.claude/skills/reflow-extract/SKILL.md` (fonte da verdade,
compartilhada entre Claude Code, OpenCode e Copilot) para o projeto:
${input:projeto} (ou `--all` para todos os projetos em `input/`).
