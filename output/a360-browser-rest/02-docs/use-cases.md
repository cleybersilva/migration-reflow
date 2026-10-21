<!--
Derivado de ui_interactions, http_calls, credentials, dependencies e
data_sources de 01-inventory/inventory.json. Nenhum caso de uso sem evidência
arquivo:linha.
-->

# Casos de uso

## UC-01: Consulta a serviço externo via navegador e REST com credencial do cofre

- **Objetivo de negócio:** Obter informações de um sistema externo acessado
  primeiro por uma página web e depois por uma chamada a um serviço REST,
  autenticando-se com uma credencial guardada no Credential Vault do A360, sem
  expor a credencial no fluxo.
- **Gatilho:** Execução do bot principal (`main.json`).
- **Evidência:** `main.json:1` (abertura de página no navegador), `main.json:2`
  (chamada REST), `main.json:3` (obtenção de credencial do cofre)
  (`01-inventory/inventory.json`).
- **Resultado esperado:** Dados retornados pelo navegador/serviço externo,
  prontos para uso pelo restante do fluxo.

## UC-02: Execução de bot filho para leitura de planilha

- **Objetivo de negócio:** Delegar a um bot filho a leitura de dados de uma
  planilha Excel, mantendo essa responsabilidade separada do fluxo principal.
- **Gatilho:** Chamada do bot principal ao bot filho `child.json` via comando
  `TaskBot.run`.
- **Evidência:** `main.json:4` (chamada ao bot filho), `child.json:1` (leitura
  da planilha) (`01-inventory/inventory.json`).
- **Resultado esperado:** Dados da planilha lidos e disponíveis para o bot
  filho/fluxo que o acionou.
