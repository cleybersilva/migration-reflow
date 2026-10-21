# Riscos e alertas de portabilidade

| Alerta | Aplica-se? | Evidência | Mitigação sugerida |
| --- | --- | --- | --- |
| A1 — extensão de navegador específica | Pendente de confirmação | `main.json:6` | O comando `Browser/unmappedAction` (`01-inventory/inventory.json:62-69`) está pendente de classificação (ver `process-flow.md`). Não se sabe, a partir do inventário, se envolve extensão de navegador específica. Recomenda-se revisar o comando antes da conversão e, se confirmado, padronizar o ambiente do analista. |
| A2 — coordenadas de tela fixas | Não | — | Nenhuma evidência de uso de coordenadas de tela fixas foi encontrada no inventário (`ui_interactions` vazio, `01-inventory/inventory.json:53`). |
| A3 — versão específica de app desktop | Não | — | Nenhuma evidência de dependência de versão específica de aplicativo desktop foi encontrada no inventário. |
| A4 — credencial via Credential Vault do A360 | Sim | `main.json:4` | O robô obtém uma credencial do Cofre de Credenciais (`CredentialVault`), referência `credential-vault` (`01-inventory/inventory.json:2-13`). Planejar a migração dessa referência para o Credential Manager do PAD antes da conversão. |
| A5 — biblioteca/DLL compartilhada entre projetos | Não | — | O inventário não lista nenhuma dependência (`dependencies` vazio, `01-inventory/inventory.json:34`); não há evidência de biblioteca ou DLL compartilhada com outros projetos. |

<!-- Ver reference/classification-rubric.md para a definição de cada alerta. -->
