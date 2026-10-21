<!--
Template de 02-docs/process-flow.md. Passo a passo em pré-ordem (mesma ordem/linha
usada pelo inventário). Cada passo cita arquivo:linha do inventory.json.
-->

# Fluxo do processo

1. **Passo 1 — <nome>**: [o que acontece] (`arquivo:linha`)
2. **Passo 2 — <nome>**: [o que acontece] (`arquivo:linha`)
3. ...

## Dependências entre bots

[Se houver `dependencies` no inventário: liste bot pai → bot filho, com
`resolution` (resolvida/não resolvida) e `target`.]

## Comandos não reconhecidos (`unknown_commands`)

[Liste aqui qualquer comando que a extração não conseguiu classificar — isso
alimenta `reference/a360-to-pad.md` como `pendente de classificação`, nunca
como ação já mapeada.]
