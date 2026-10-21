<!--
Alertas de portabilidade A1-A5 da classification-rubric.md, aplicados a este
projeto específico.
-->

# Riscos e alertas de portabilidade

| Alerta | Aplica-se? | Evidência | Mitigação sugerida |
| --- | --- | --- | --- |
| A1 — extensão de navegador específica | sim | `main.json:1` | O comando `Browser.open` indica automação de navegador, que no A360 normalmente depende de uma extensão própria instalada no ambiente do analista; padronizar essa extensão (ou o equivalente no PAD) antes da conversão. |
| A2 — coordenadas de tela fixas | não | — | Não há, no inventário, nenhum comando de clique ou interação por coordenada de tela registrado para este projeto. |
| A3 — versão específica de app desktop | não | — | O único acesso a aplicativo desktop é a leitura de planilha (`child.json:1`), sem versão de aplicativo especificada no inventário. |
| A4 — credencial via Credential Vault do A360 | sim | `main.json:3` | O robô obtém credencial via `CredentialVault.getCredential`; planejar a migração dessa referência para o Credential Manager do PAD antes da conversão. |
| A5 — biblioteca/DLL compartilhada entre projetos | não | — | Este projeto é um fluxo A360 (JSON), sem evidência de biblioteca/DLL compartilhada no inventário. |

<!-- Ver reference/classification-rubric.md para a definição de cada alerta. -->
