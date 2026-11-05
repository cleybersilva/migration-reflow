# Tabela verdade: A360 → Power Automate Desktop

Toda ação Robin citada aqui precisa existir em [`robin-actions.md`](robin-actions.md), com o
id Robin real (ver ADR-029). O status desta tabela é o do **mapeamento** A360 → PAD
(o comando de origem corresponde mesmo a essa ação?), não o da sintaxe da ação.
Linhas com status `sem equivalente` são comandos A360 sem ação PAD mapeada ainda —
ficam de fora da checagem de existência na whitelist, de propósito.

Esta tabela nasce conservadora, a partir das fixtures sintéticas e dos
`unknown_commands` que a extração encontrar. Ela cresce por curadoria humana (ou,
na Fase 6, pela skill `reflow-truth-table`/agent `reflow-truth-table-curator`) —
nunca promova uma linha para `validado` sem ter rodado a ação de verdade no PAD.

| Pacote A360 | Comando A360 | Ação PAD equivalente | Observações | Status |
| --- | --- | --- | --- | --- |
| Browser | open | `WebAutomation.LaunchEdge.LaunchEdge` | Chrome: irmão `WebAutomation.LaunchChrome.LaunchChrome`, mesmos argumentos; escolher pelo navegador do legado (ADR-029) | não validado |
| Browser | close | `WebAutomation.CloseWebBrowser` | — | não validado |
| Browser | click | `WebAutomation.Click.Click` | exige elemento web gravado no designer (`needs_ui_selector`) | não validado |
| Window | activate | `UIAutomation.FocusWindow.FocusByTitleClass` | pelo título da janela, sem elemento gravado | não validado |
| Window | close | `UIAutomation.CloseWindow.CloseByTitleClass` | — | não validado |
| Recorder | playback | `UIAutomation.Click.Click` | depende do que foi gravado; costuma exigir mais de uma ação PAD (clique, digitação, foco) | não validado |
| MouseKeyboard | click | `UIAutomation.Click.Click` | exige elemento gravado no designer (`needs_ui_selector`) | não validado |
| MouseKeyboard | type | `MouseAndKeyboard.SendKeys.FocusAndSendKeys` | nunca digitar credencial literal | não validado |
| Excel | activate | `UIAutomation.FocusWindow.FocusByTitleClass` | traz a janela do Excel para o primeiro plano | não validado |
| REST | get | `Web.InvokeWebService.InvokeWebService` | `Method: Web.Method.Get` | não validado |
| REST | post | `Web.InvokeWebService.InvokeWebServicePost` | autorização em `CustomHeaders`, a partir de variável | não validado |
| REST | put | `Web.InvokeWebService.InvokeWebServicePut` | — | não validado |
| REST | delete | `Web.InvokeWebService.InvokeWebService` | `Method: Web.Method.Delete` | não validado |
| SOAP | call | `Web.InvokeSoapService.InvokeSoapService` | — | não validado |
| Excel | open | `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess` | Um analista validou a ação PAD para o pacote AA360 "Excel avançado: Abrir" (ver `robin-actions.md`); não confirmado ainda se o pacote simples "Excel" (sem "avançado") desta linha é o mesmo `packageName` real — status não muda até confirmar | não validado |
| Excel | read | `Excel.ReadFromExcel.ReadCells` | atributo `range` (intervalo) → `ReadCells`; célula única → `Excel.ReadFromExcel.ReadCell` (validada pelo analista, mesma ressalva de `packageName`); planilha inteira → `Excel.ReadFromExcel.ReadAllCells` | não validado |
| Excel | write | `Excel.WriteToExcel.WriteCell` | — | não validado |
| Excel | close | `Excel.CloseExcel.Close` | salvar antes: `Excel.CloseExcel.CloseAndSave` | não validado |
| CSV | read | `File.ReadTextFromFile.ReadText` | A ação PAD foi validada para o equivalente AA360 "CSV/TXT: Ler" — mesma ressalva: não confirmado se o `packageName` real desta linha ("CSV") é o testado. Para ler como tabela: `File.ReadFromCSVFile.ReadCSV` | não validado |
| CSV | write | `File.WriteToCSVFile.WriteCSV` | — | não validado |
| Database | connect | `Database.Connect.Connect` | connection string vem de configuração/cofre, nunca literal | não validado |
| Database | query | `Database.ExecuteSqlStatement.Execute` | — | não validado |
| File | read | `File.ReadTextFromFile.ReadText` | Mesma ação validada da linha `CSV \| read` acima; mesma ressalva de `packageName` | não validado |
| File | write | `File.WriteText` | — | não validado |
| CredentialVault | getCredential | `Credentials.GetCredential` | nunca copiar o valor bruto, só a referência ao cofre; sem ação na KB: origem real a decidir (variável de entrada sensível ou CyberArk) | não validado |
| CredentialVault | get | `Credentials.GetCredential` | idem | não validado |
| TaskBot | run | `CALL` | resolução do bot filho depende de `attributes.botName` apontar para um JSON do export | não validado |
| VBScript | open | `Scripting.RunVBScript.RunVBScript` | Ação PAD validada para o equivalente AA360 "VBScript: Abrir" (ver `robin-actions.md`) — mas `packageName`/`commandName` desta linha ("VBScript"/"open") são um palpite baseado no rótulo da UI, nunca confirmados por uma extração real; corrigir assim que um export de verdade citar o nome exato | não validado |
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
