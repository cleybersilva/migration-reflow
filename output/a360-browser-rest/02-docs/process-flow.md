<!--
Passo a passo em pré-ordem, mesma ordem/linha do inventário. Cada passo cita
arquivo:linha de 01-inventory/inventory.json.
-->

# Fluxo do processo

1. **Passo 1 — Abertura de página no navegador**: o robô abre uma página em um
   navegador, dando início ao fluxo de consulta ao sistema externo
   (`main.json:1`).
2. **Passo 2 — Consulta a serviço externo via REST**: a partir da página
   aberta, o robô realiza uma chamada do tipo GET a um serviço REST externo
   (`main.json:2`).
3. **Passo 3 — Obtenção de credencial no Credential Vault**: o robô recupera
   uma credencial armazenada no Credential Vault do A360 para autenticar a
   consulta (`main.json:3`).
4. **Passo 4 — Execução do bot filho**: o robô principal aciona o bot filho
   `child.json` (`main.json:4`).
5. **Passo 5 — Leitura de planilha pelo bot filho**: o bot filho lê dados de
   uma planilha Excel (`child.json:1`).

## Dependências entre bots

| Bot pai | Bot filho | Resolução | Evidência |
| --- | --- | --- | --- |
| `main.json` | `child.json` | resolvida | `main.json:4` |

## Comandos não reconhecidos (`unknown_commands`)

Não há comandos não reconhecidos registrados no inventário para este projeto
(`unknown_commands` está vazio em `01-inventory/inventory.json`). Não há,
portanto, nenhuma pendência de classificação a reportar aqui.
