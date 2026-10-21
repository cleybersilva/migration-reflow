# Casos de uso

## UC-01: Envio de dados de planilha Excel para sistema externo autenticado por credencial do cofre

- **Objetivo de negócio:** Permitir que informações mantidas em uma planilha
  Excel sejam lidas e transmitidas a um sistema externo, utilizando uma
  credencial armazenada de forma segura no Cofre de Credenciais da
  Automation 360 para autenticar a transmissão.
- **Gatilho:** Abertura do arquivo Excel de origem, primeira ação registrada
  no fluxo (`01-inventory/inventory.json:15-23`, evidência original em
  `main.json:1`).
- **Evidência:** `main.json:1` (abertura da planilha), `main.json:2` (leitura
  do intervalo de dados), `main.json:3` (envio via chamada HTTP POST),
  `main.json:4` (obtenção da credencial no cofre) — todos citados em
  `01-inventory/inventory.json:15-49` e `01-inventory/inventory.json:2-13`.
- **Resultado esperado:** Os dados lidos da planilha são entregues a um
  sistema externo por meio de uma chamada HTTP autenticada, sem exposição do
  valor da credencial utilizada.

<!--
Nota: os comandos `CustomPackage/transform` (main.json:5) e
`Browser/unmappedAction` (main.json:6), listados em
`01-inventory/inventory.json:54-69`, não geraram um caso de uso porque a
extração não conseguiu classificar sua função de negócio. Ver
`process-flow.md` para o registro dessas pendências — nenhum uso foi
presumido para esses comandos.
-->
