# Casos de uso

## UC-01: Lançamento de notas no faturamento

- **Objetivo de negócio:** digitar no sistema de faturamento as notas de uma planilha.
- **Evidência:** `main.json:1` (lê a lista de notas), `main.json:2-7` (janela, gravações,
  digitação, fechamento).
- **Observação:** a planilha só fornece a lista de entrada; sem a digitação na tela não
  existe processo. Cerca de 30 notas por dia, sem exigência de tempo real.
