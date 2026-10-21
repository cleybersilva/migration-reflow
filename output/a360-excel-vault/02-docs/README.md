# a360-excel-vault

- Origem: a360 (`00-manifest.json`)
- Extraído em: 2026-10-21T16:32:40 UTC (`00-manifest.json:3`)
- Arquivos analisados: `main.json` (`01-inventory/inventory.json:36`)

## O que este robô faz

Este robô abre uma planilha Excel e lê um intervalo de dados dela
(`01-inventory/inventory.json:15-33`). Em seguida, envia esses dados a um
sistema externo por meio de uma chamada HTTP do tipo POST
(`01-inventory/inventory.json:38-49`), autenticando-se com uma credencial
obtida do Cofre de Credenciais da Automation 360
(`01-inventory/inventory.json:2-13`). O fluxo também contém dois comandos que
a extração automática não conseguiu classificar — um do pacote
`CustomPackage` e outro do pacote `Browser` — cujo papel exato no processo de
negócio ainda não pôde ser confirmado e está pendente de revisão humana
(`01-inventory/inventory.json:54-69`).

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

Classificação (`03-classification/classification.md`) decide se este projeto
vai para PAD, PARTIAL ou NOT_PAD. A classificação deve levar em conta que
ainda existem dois comandos (`CustomPackage/transform` e
`Browser/unmappedAction`) pendentes de classificação — ver
`process-flow.md`.
