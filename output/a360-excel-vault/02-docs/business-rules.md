# Regras de negócio

## RN-01: Nenhuma regra condicional explícita identificada pela extração

- **Descrição:** A extração determinística registrada em
  `01-inventory/inventory.json` não capturou nenhuma condicional, validação
  ou critério de decisão explícito. As seções `data_sources`
  (`01-inventory/inventory.json:14-33`), `http_calls`
  (`01-inventory/inventory.json:38-49`) e `credentials`
  (`01-inventory/inventory.json:2-13`) descrevem apenas operações sequenciais
  (abrir planilha, ler intervalo, enviar via REST, obter credencial), sem
  lógica condicional associada.
- **Condição:** Não aplicável — nenhuma regra condicional foi encontrada no
  inventário.
- **Evidência:** `01-inventory/inventory.json` (seções `data_sources`,
  `http_calls`, `credentials`; nenhuma condicional presente nos trechos
  citados por `arquivo:linha`).

<!-- TODO reflow -->
**TODO reflow:** Os comandos `CustomPackage/transform` (`main.json:5`) e
`Browser/unmappedAction` (`main.json:6`), listados em `unknown_commands`
(`01-inventory/inventory.json:54-69`), podem eventualmente embutir alguma
regra de negócio ou condição que a extração não conseguiu capturar. Isso não
pode ser confirmado com a evidência disponível — requer revisão humana antes
da classificação. Nenhuma regra foi presumida para esses comandos.
