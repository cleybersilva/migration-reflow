# Integrações

## Chamadas HTTP/SOAP

| Operação | Evidência | Observação |
| --- | --- | --- |
| `REST / post` | `main.json:3` | Envio de dados (atributo `body`) com cabeçalho de autorização (atributo `authorization`) a um sistema externo; o inventário não identifica o sistema de destino além do pacote genérico `REST` (`01-inventory/inventory.json:38-49`) |

## Credenciais referenciadas

| Referência | Evidência | Observação |
| --- | --- | --- |
| `credential-vault` | `main.json:4` | Credencial obtida do Cofre de Credenciais (`CredentialVault`) da Automation 360 via comando `get` (atributo `credential`). O valor da credencial nunca é reproduzido nesta documentação (`01-inventory/inventory.json:2-13`) |

## Dependência entre bots

O inventário não lista nenhuma entrada em `dependencies`
(`01-inventory/inventory.json:34`, array vazio). Nenhuma dependência entre
bot pai e bot filho foi identificada para este projeto.
