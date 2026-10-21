<!--
Template de 02-docs/integrations.md. Deriva de http_calls, credentials e
dependencies do inventory.json. Credencial: só a referência (campo `reference`),
nunca o valor do cofre.
-->

# Integrações

## Chamadas HTTP/SOAP

| Operação | Evidência | Observação |
| --- | --- | --- |
| `<operation>` | `arquivo:linha` | [sistema de destino, se identificável pelo nome do pacote/comando] |

## Credenciais referenciadas

| Referência | Evidência | Observação |
| --- | --- | --- |
| `<reference>` | `arquivo:linha` | Nunca inclua o valor — só a referência ao cofre |

## Dependência entre bots

| Bot pai | Bot filho | Resolução |
| --- | --- | --- |
| `<arquivo>` | `<target>` | resolvida / não resolvida |
