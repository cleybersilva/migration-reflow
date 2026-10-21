# Tabela verdade: A360 → Power Automate Desktop

Toda ação Robin citada aqui precisa existir em [`robin-actions.md`](robin-actions.md).
Linhas com status `sem equivalente` são comandos A360 sem ação PAD mapeada ainda —
ficam de fora da checagem de existência na whitelist, de propósito.

Esta tabela nasce conservadora, a partir das fixtures sintéticas e dos
`unknown_commands` que a extração encontrar. Ela cresce por curadoria humana (ou,
na Fase 6, pela skill `reflow-truth-table`/agent `reflow-truth-table-curator`) —
nunca promova uma linha para `validado` sem ter rodado a ação de verdade no PAD.

| Pacote A360 | Comando A360 | Ação PAD equivalente | Observações | Status |
| --- | --- | --- | --- | --- |
| Browser | open | `Browser.LaunchNewBrowser` | — | não validado |
| Browser | close | `Browser.CloseBrowser` | — | não validado |
| Browser | click | `Browser.ClickElement` | — | não validado |
| Window | activate | `UI.ActivateWindow` | — | não validado |
| Window | close | `UI.CloseWindow` | — | não validado |
| Recorder | playback | `UI.SendKeysOrClick` | depende do que foi gravado; pode exigir mais de uma ação PAD | não validado |
| MouseKeyboard | click | `UI.SendKeysOrClick` | — | não validado |
| MouseKeyboard | type | `UI.SendKeysOrClick` | — | não validado |
| Excel | activate | `UI.ActivateWindow` | traz a janela do Excel para o primeiro plano | não validado |
| REST | get | `Web.InvokeRestApi` | — | não validado |
| REST | post | `Web.InvokeRestApi` | — | não validado |
| REST | put | `Web.InvokeRestApi` | — | não validado |
| REST | delete | `Web.InvokeRestApi` | — | não validado |
| SOAP | call | `Web.InvokeSoapService` | — | não validado |
| Excel | open | `Excel.LaunchExcel` | — | não validado |
| Excel | read | `Excel.ReadFromWorksheet` | — | não validado |
| Excel | write | `Excel.WriteToWorksheet` | — | não validado |
| CSV | read | `File.ReadTextFromFile` | — | não validado |
| CSV | write | `File.WriteTextToFile` | — | não validado |
| Database | connect | — | nenhum módulo de banco de dados na whitelist ainda; PAD tem ações nativas de SQL a avaliar | sem equivalente |
| Database | query | — | idem | sem equivalente |
| File | read | `File.ReadTextFromFile` | — | não validado |
| File | write | `File.WriteTextToFile` | — | não validado |
| CredentialVault | getCredential | `Credentials.GetCredential` | nunca copiar o valor bruto, só a referência ao cofre | não validado |
| CredentialVault | get | `Credentials.GetCredential` | idem | não validado |
| TaskBot | run | `Flow.RunSubflow` | resolução do bot filho depende de `attributes.botName` apontar para um JSON do export | não validado |
| CustomPackage | transform | — | comando fora do registro; apareceu em `tests/fixtures/a360/excel-vault` como `unknown_commands` | pendente de classificação |
| Browser | unmappedAction | — | comando fora do registro; apareceu em `tests/fixtures/a360/excel-vault` como `unknown_commands` | pendente de classificação |

## Como alimentar esta tabela

1. Rode a extração (`uv run python -m reflow extract <projeto>`) e abra
   `output/<projeto>/01-inventory/inventory.json` → campo `unknown_commands`.
2. Para cada comando desconhecido, adicione uma linha com status `pendente de
   classificação` (nunca invente a ação PAD ainda).
3. Para classificar de verdade: monte a ação equivalente no PAD, confirme que
   funciona, e só então mude o status para `não validado` → `validado` (depois
   de promover também a ação em `robin-actions.md`).
4. Nunca altere uma linha já `validado` sem revisão humana (ver
   [`AGENTS.md`](../AGENTS.md)).
