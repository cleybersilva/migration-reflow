# Casos de uso

## UC-01: Conciliação na tesouraria

- **Objetivo de negócio:** conciliar o lote no sistema de tesouraria.
- **Evidência:** `main.json:1-4` (janela, gravação, digitação, fechamento).

## UC-02: Envio de saldos

- **Objetivo de negócio:** enviar a planilha de saldos ao sistema financeiro.
- **Evidência:** `main.json:5-6` (lê a planilha), `main.json:7` (credencial do cofre),
  `main.json:8` (POST na API).
- **Observação:** UC-02 não depende de UC-01; os dois só rodam no mesmo robô por hábito.
