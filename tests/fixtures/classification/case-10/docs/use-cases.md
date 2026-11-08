# Casos de uso

## UC-01: Envio de lote

- **Objetivo de negócio:** enviar o lote diário a um serviço interno.
- **Evidência:** `Program.cs:9` (lê o arquivo), `Program.cs:10-11` (POST na API).
- **Observação:** console agendado, estável há anos, sem nenhuma tela (informado pela área).
