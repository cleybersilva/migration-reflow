# Casos de uso

## UC-01: Coleta de cotações via web e exportação para CSV

- **Objetivo de negócio:** Obter o conteúdo de uma página de cotações disponível na internet e disponibilizá-lo em um arquivo local para uso posterior pela área de negócio.
- **Gatilho:** Não há evidência, no inventário desta extração, de um agendamento ou evento que inicie o processo automaticamente; o fluxo corresponde à execução da função `collect_quotes` definida em `main.py:7`. Qualquer suposição sobre gatilho (manual, agendado etc.) fica como TODO reflow para confirmação humana.
- **Evidência:** `main.py:8` (requisição HTTP), `main.py:10` (abertura do arquivo de saída), `main.py:11` (gravação do conteúdo no arquivo)
- **Resultado esperado:** Um arquivo `quotes.csv` contendo, em uma linha, o conteúdo retornado pela chamada HTTP (`main.py:10-11`).

<!-- Não foram identificados outros casos de uso no inventário: não há ui_interactions registradas (01-inventory/inventory.json:43). -->
