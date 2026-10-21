<!--
Template de 02-docs/risks.md. Alertas de portabilidade A1-A5 da
classification-rubric.md, aplicados a este projeto específico.
-->

# Riscos e alertas de portabilidade

| Alerta | Aplica-se? | Evidência | Mitigação sugerida |
| --- | --- | --- | --- |
| A1 — extensão de navegador específica | sim/não | `arquivo:linha` | [padronizar ambiente do analista] |
| A2 — coordenadas de tela fixas | sim/não | `arquivo:linha` | [preferir seletor/elemento a coordenada] |
| A3 — versão específica de app desktop | sim/não | `arquivo:linha` | [documentar versão exigida] |
| A4 — credencial via Credential Vault do A360 | sim/não | `arquivo:linha` | [plano de migração para o Credential Manager do PAD] |
| A5 — biblioteca/DLL compartilhada entre projetos | sim/não | `arquivo:linha` | [mapear os demais projetos que usam a mesma DLL antes de migrar] |

<!-- Ver reference/classification-rubric.md para a definição de cada alerta. -->
