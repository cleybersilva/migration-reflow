<!--
Derivado de http_calls, credentials e dependencies do inventory.json.
Credencial: só a referência (campo reference), nunca o valor do cofre.
-->

# Integrações

## Chamadas HTTP/SOAP

| Operação | Evidência | Observação |
| --- | --- | --- |
| `get` (REST) | `main.json:2` | Chamada a um endpoint externo via protocolo REST, feita a partir da página aberta no navegador (`main.json:1`). |

## Credenciais referenciadas

| Referência | Evidência | Observação |
| --- | --- | --- |
| `main.json:3:credential-vault` | `main.json:3` | Credencial obtida do Credential Vault do A360; apenas a referência ao cofre é registrada, nunca o valor armazenado. |

## Dependência entre bots

| Bot pai | Bot filho | Resolução |
| --- | --- | --- |
| `main.json` | `child.json` | resolvida |

Evidência da dependência: `main.json:4` (`01-inventory/inventory.json`).
