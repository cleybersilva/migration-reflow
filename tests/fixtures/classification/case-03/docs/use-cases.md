# Casos de uso

## UC-01: Carga de pedidos

- **Objetivo de negócio:** carregar o arquivo diário de pedidos no banco local.
- **Evidência:** `main.py:8-9` (lê o CSV), `main.py:10-12` (grava no banco).
- **Observação:** roda há anos sem incidente, agendado, sem intervenção humana (informado
  pela área). Nenhuma tela envolvida.
