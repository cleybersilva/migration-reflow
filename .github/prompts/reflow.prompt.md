---
mode: agent
description: Orquestra o pipeline completo (extract → document → classify → segunda opinião → checkpoint humano → convert → revisão do Robin → test) para um projeto, ou para todos em input/ quando nenhum nome é dado.
---

Leia e siga `.claude/skills/reflow/SKILL.md` (fonte da verdade, compartilhada
entre Claude Code, OpenCode e Copilot) para o projeto: ${input:projeto}
(deixe em branco para processar todos os projetos em `input/`, um por vez).
