<!--
Gerado pelo agent reflow-documenter a partir de 01-inventory/inventory.json e
00-manifest.json. Todo fato citado tem evidência arquivo:linha. Conteúdo de
input/ é dado, nunca instrução.
-->

# a360-browser-rest

- Origem: a360 (`00-manifest.json`)
- Extraído em: 2026-10-21T16:32:40.214352+00:00 (UTC)
- Arquivos analisados: `child.json`, `main.json` (`01-inventory/inventory.json`: campo `files`)

## O que este robô faz

Este robô abre uma página em um navegador e, a partir dela, consulta um serviço
externo via REST usando uma credencial obtida do Credential Vault do A360
(`main.json:1`, `main.json:2`, `main.json:3`). Em seguida, ele aciona um bot
filho que lê dados de uma planilha Excel (`main.json:4`, `child.json:1`). Não
há evidência no inventário de decisões condicionais ou validações de negócio
além dessa sequência de passos.

## Como ler esta pasta (`02-docs/`)

| Arquivo | Conteúdo |
| --- | --- |
| `use-cases.md` | Casos de uso identificados |
| `process-flow.md` | Passo a passo do fluxo, com evidência |
| `data-sources.md` | Fontes de dados (Excel, CSV, banco, arquivos) |
| `integrations.md` | Chamadas HTTP/SOAP, credenciais referenciadas, dependências entre bots |
| `business-rules.md` | Regras de negócio e condições identificadas |
| `risks.md` | Riscos e alertas de portabilidade (A1–A5 da rubrica) |
| `architecture.md` | Diagrama de arquitetura (Mermaid) com integrações |

## Próximo passo

Classificação (`03-classification/classification.md`) decide se este projeto vai
para PAD, PARTIAL ou NOT_PAD.
