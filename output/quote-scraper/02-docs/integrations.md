# Integrações

## Chamadas HTTP/SOAP

| Operação | Evidência | Observação |
| --- | --- | --- |
| `urllib.request.urlopen` | `main.py:8` | Requisição HTTP para o endereço `https://example.invalid/quotes`, citado na mesma linha do código-fonte; não há, no inventário, identificação de qual sistema de negócio está por trás desse endereço |

## Credenciais referenciadas

Nenhuma credencial foi identificada nesta extração — o campo `credentials` do inventário está vazio (`01-inventory/inventory.json:2`).

| Referência | Evidência | Observação |
| --- | --- | --- |
| — | — | Sem credenciais referenciadas no inventário |

## Dependência entre bots

Nenhuma dependência entre bots foi identificada no inventário (sem campos `target`/`resolution`). O bloco `dependencies` do inventário cita apenas dependências de biblioteca Python:

| Bot pai | Bot filho | Resolução |
| --- | --- | --- |
| — | — | Não aplicável — `dependencies` do inventário lista bibliotecas (`urllib.request.urlopen` em `main.py:3` e `csv` em `main.py:4`), não outros bots |
