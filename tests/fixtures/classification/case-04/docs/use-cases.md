# Casos de uso

## UC-01: Envio de títulos

- **Objetivo de negócio:** enviar os títulos do dia ao sistema de cobrança.
- **Evidência:** `main.json:1-2` (consulta o banco), `main.json:3` (grava CSV),
  `main.json:4` (credencial do cofre), `main.json:5` (POST na API).
