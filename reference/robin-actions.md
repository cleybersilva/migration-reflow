# Whitelist de ações Robin

Toda ação Robin usada numa conversão **tem que vir desta lista**. Nenhuma sintaxe é
inventada, nem mesmo a que "parece óbvia" (ver [`AGENTS.md`](../AGENTS.md)).

O cabeçalho de cada seção é o **id Robin real**: o `actionId` completo da
[PAD Robin Action KB](vendor/pad-robin-kb/README.md) (`Módulo.Ação.Seletor`) ou a
instrução da linguagem (`SET`, `IF`, `LOOP FOREACH`...). Seletores irmãos da mesma ação
(`Excel.ReadFromExcel.ReadCell` e `.ReadCells`, por exemplo) aceitam argumentos
diferentes: cada um tem a sua seção, e argumento de um nunca vai para o outro.

## Status, do mais fraco para o mais forte

- **`[não validado]`**: nada confirmado. O conteúdo é um placeholder textual
  (`[não validado — TODO reflow: ...]`), nunca sintaxe real.
- **`[proposto — baseado em evidência pública, não testado nesta instalação]`**:
  sintaxe real copiada de um flow PAD público, cruzada com a documentação oficial, sem
  validação sistemática de colagem. Ver ADR-025.
- **`[colado KB: PAD 2.73, não rodado nesta instalação]`**: o exemplo está na KB
  vendorizada e **colou sem erro no PAD Designer 2.73 do autor da KB**, numa validação
  sistemática (ação: `golden_example` do registro; instrução: colagem `clean` do
  `probe-corpus.json`). Prova que o PAD **aceita** a linha, não que ela roda **neste**
  ambiente. Ver ADR-029.
- **`[validado PAD: rodou]`**: alguém montou a ação no designer **deste** PAD, rodou e
  confirmou. É a única barra que conta como validação real.

Detalhe de qualquer ação da KB (parâmetros tipados, valores de enum, seletores irmãos,
erros aceitos em `ON ERROR`): `uv run python -m reflow kb show <actionId>`.

## Como usar um snippet

O snippet é um **template**: copie a linha e troque só os valores, seguindo
`vendor/pad-robin-kb/PAD_Robin_TypeReference.json` e as regras de sintaxe em
[`robin-conventions.md`](robin-conventions.md). Os valores de exemplo (`$'''example'''`,
`ExcelInstance`, `C:\temp\test.xlsx`) nunca vão literais para um `Main.robin`: viram os
nomes e valores do passo (`step_`/`in_`/`out_`/`cfg_`). Uma ação é sempre **uma linha
só**; argumento opcional pode ser omitido, argumento que o seletor não tem nunca entra.

Ações com **`needs_ui_selector`** recebem um elemento gravado no designer
(`appmask['<tela>']['<elemento>']`). O elemento de exemplo da KB não existe no seu
repositório de UI: a conversão deixa `TODO reflow` pedindo a gravação do elemento.

---

## Instruções da linguagem

### `SET`
- Módulo: linguagem (equivale à ação "Set variable")
- Quando usar: criar ou atualizar uma variável do flow.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `A00-control`, `V01-expr-bare` (`probe-corpus.json`). Texto é
  `$'''...'''`, número e booleano são nus, expressão é nua (`SET total TO preco * qtd`),
  e `%...%` só existe **dentro** de string.

```robin
SET cfg_output_folder TO $'''C:\Users\Public\Documents\\'''
```

### `IF`
- Módulo: linguagem (ações "If", "Else if", "Else")
- Quando usar: ramificar o fluxo conforme uma condição.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `C10-elseif`, `C12-isnotempty`. Operadores `=`, `<>`, `>`, `<`,
  `>=`, `<=`, `AND`, `OR`, `NOT(...)` e funções `IsEmpty`, `IsNotEmpty`, `Contains`,
  `StartsWith`, `EndsWith`. Condição que é uma ação (kind `Condition` na KB) é
  `IF (Ação ...) THEN`, e nunca vai num `ELSE IF`.

```robin
IF in_valor_1 = in_valor_2 THEN
ELSE IF IsNotEmpty(in_valor_1) THEN
ELSE
END
```

### `LOOP FOREACH`
- Módulo: linguagem (ação "For each")
- Quando usar: iterar sobre uma lista, data table ou data row.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `L12-foreach-dtrow`, `L13-foreach-literal`.

```robin
LOOP FOREACH step_item_atual IN in_lista_ou_tabela
END
```

### `LOOP FROM`
- Módulo: linguagem (ação "Loop")
- Quando usar: repetir um bloco um número conhecido de vezes.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `L04-from-prop`, `L07-from-var`.

```robin
LOOP step_indice FROM 0 TO in_lista.Count - 1 STEP 1
END
```

### `LOOP WHILE`
- Módulo: linguagem (ação "Loop condition")
- Quando usar: repetir um bloco enquanto uma condição for verdadeira.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `L01-while-parens`, `L02-while-bare`.

```robin
LOOP WHILE (step_tentativa) < (cfg_max_tentativas)
END
```

### `**REGION`
- Módulo: linguagem (ações "Region" / "End region")
- Quando usar: agrupar os passos do mesmo estágio do processo (rótulo = nome do estágio
  em `02-docs/use-cases.md`), destacar um subflow ou um subfluxo comum catalogado.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `E19-region-star` (clean) e `E20-region-word` (rejeitada):
  `REGION` / `END REGION` sem asteriscos derrubam a colagem inteira.

```robin
**REGION Leitura da Base de Entrada
**ENDREGION
```

### `ON ERROR`
- Módulo: linguagem (tratamento de erro de uma ação)
- Quando usar: tratar a falha de uma ação logo depois dela. Só em ação cujo registro na
  KB tem `on_error: true`, e um caso nomeado só com um nome da lista de erros da ação
  (`reflow kb show`). Dentro do tratador só `SET`, `CALL`, `GOTO` e `THROW ERROR`: um
  `IF` ali derruba a colagem. Ordem: `ON ERROR REPEAT` (opcional), casos nomeados, o
  `ON ERROR` genérico por último, um `END` para todos.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `E04-onerror`, `E05-onerror-repeat` e as regras
  `error-handlers` / `on-error-allowed` (`robin-rules.json`).

```robin
File.ReadTextFromFile.ReadText File: cfg_arquivo_entrada Encoding: File.TextFileEncoding.UTF8 Content=> out_conteudo
ON ERROR FileNotFoundError
    SET step_falhou TO True
ON ERROR
    SET step_falhou TO True
END
```

### `BLOCK`
- Módulo: linguagem (ação "On block error")
- Quando usar: proteger um grupo de passos, ou uma ação com `on_error: false`, que não
  aceita `ON ERROR` próprio. O tratador fica logo depois do `BLOCK`, antes dos passos.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- Evidência: colagens `OB1-additem`, `OB2-log`.

```robin
BLOCK EnvioRest
ON BLOCK ERROR
    SET step_falhou TO True
END
END
```

### `CALL`
- Módulo: linguagem (ação "Run subflow")
- Quando usar: acionar outro subflow (equivalente ao A360 `TaskBot.run`). O passo nunca
  fica implícito: nome com sufixo `_subflow_<nome_do_bot_filho>`, comentário citando o
  bot filho (`dependencies` do `inventory.json`) e `**REGION Subflow: <nome>`. Ver
  [`robin-conventions.md`](robin-conventions.md) e [`subfluxos-comuns.md`](subfluxos-comuns.md).
  A definição do subflow (`FUNCTION ... END FUNCTION`) **não** cola: o subflow é criado
  no designer e o corpo dele é colado dentro dele.
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: `CALL CloseChrome` em
  [`AgniusBartninkas/power-automate-desktop-framework`](https://github.com/AgniusBartninkas/power-automate-desktop-framework),
  cruzado com a ação oficial **Run subflow**. A KB cita `CALL` entre as instruções
  permitidas num tratador de erro, mas o corpus não tem colagem própria dele.

```robin
CALL Subflow_NomeDoBotFilho
```

---

## Excel

### `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`
- Módulo: Excel
- Quando usar: abrir uma planilha existente sem processo Excel próprio (A360
  `Excel.open`; na UI do analista, "Excel avançado: Abrir").
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado no designer, rodado e testado neste PAD
  (2026-10-30), com `Visible: True` e `UseMachineLocale: False`.
- ON ERROR: `LaunchExcelError`, `OpenDocumentError`. Irmãos: `.Launch`, `.LaunchAndOpen`,
  `.LaunchUnderExistingProcess`.

Snippet validado pelo analista (inalterado):

```robin
Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess
    Path:              $'''%cfg_pasta_arquivos_entrada%/%cfg_numero_base%.xlsx'''
    Visible:           True
    ReadOnly:          False
    UseMachineLocale:  False
    Instance=>         out_excel_instance
```

**Forma de colagem `[colado KB: PAD 2.73, não rodado nesta instalação]`**: a KB só tem
evidência de ação em **uma linha** (regra `one-per-line`); nenhuma colagem do corpus
quebra argumentos em linhas. `TODO reflow (revisão humana)`: confirmar se a forma em
várias linhas acima é a que foi colada no designer ou só a exibição do guia. Até lá, o
`Main.robin` usa a forma de uma linha, com os mesmos valores. Os argumentos opcionais de
senha do exemplo da KB foram omitidos, como no snippet validado.

```robin
Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''%cfg_pasta_arquivos_entrada%/%cfg_numero_base%.xlsx''' Visible: True ReadOnly: False UseMachineLocale: False Instance=> out_excel_instance
```

### `Excel.ReadFromExcel.ReadCell`
- Módulo: Excel
- Quando usar: ler **uma** célula de uma planilha aberta. Na UI do A360 do analista
  aparece como "Excel avançado: Obter planilha como tabela de dados", mas o código roda
  uma célula só.
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado e rodado neste PAD (2026-10-30).
- ON ERROR: `ReadCellsError`. Irmãos: `.ReadCells` (intervalo), `.ReadAllCells`
  (planilha inteira), `.ReadNamedCell`, `.Read`.

Snippet validado pelo analista (inalterado):

```robin
Excel.ReadFromExcel.ReadCell
    Instance:               out_excel_instance
    StartColumn:            $'''A'''
    StartRow:               1
    GetCellContentsMode:    Excel.GetCellContentsMode.TypedValues
    CellValue=>             out_excel_data
```

**Forma de colagem `[colado KB: PAD 2.73, não rodado nesta instalação]`** (mesma
ressalva de `LaunchAndOpenUnderExistingProcess`):

```robin
Excel.ReadFromExcel.ReadCell Instance: out_excel_instance StartColumn: $'''A''' StartRow: 1 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues CellValue=> out_excel_data
```

### `Excel.ReadFromExcel.ReadCells`
- Módulo: Excel
- Quando usar: ler um **intervalo específico** (A360 `Excel.read` com atributo `range`,
  tipo `A1:B3` → `StartColumn`/`StartRow`/`EndColumn`/`EndRow`). Fecha a lacuna
  deixada pelo ADR-025.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ReadCellsError`.

```robin
Excel.ReadFromExcel.ReadCells Instance: ExcelInstance StartColumn: $'''example''' StartRow: 1 EndColumn: $'''example''' EndRow: 1 FirstLineIsHeader: False GetCellContentsMode: Excel.GetCellContentsMode.TypedValues RangeValue=> ExcelData
```

### `Excel.ReadFromExcel.ReadAllCells`
- Módulo: Excel
- Quando usar: ler todas as células usadas da planilha ativa.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ReadCellsError`.
- Correção (ADR-029): o snippet `proposto` anterior usava `Instance: %var%`. `%...%`
  fora de string derruba a colagem inteira (regra `pct-outside-string`).

```robin
Excel.ReadFromExcel.ReadAllCells Instance: ExcelInstance FirstLineIsHeader: False GetCellContentsMode: Excel.GetCellContentsMode.TypedValues RangeValue=> ExcelData
```

### `Excel.WriteToExcel.WriteCell`
- Módulo: Excel
- Quando usar: escrever um valor numa célula (A360 `Excel.write`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `WriteToExcelError`. Irmãos: `.Write`, `.WriteNamedCell`.

```robin
Excel.WriteToExcel.WriteCell Instance: ExcelInstance Value: $'''sample''' Column: $'''example''' Row: 1
```

### `Excel.CloseExcel.Close`
- Módulo: Excel
- Quando usar: fechar o Excel **sem salvar**.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `CloseExcelError`, `SaveExcelError`.
- Correção (ADR-029): mesmo problema de `Instance: %var%` do snippet `proposto` anterior.

```robin
Excel.CloseExcel.Close Instance: ExcelInstance
```

### `Excel.CloseExcel.CloseAndSave`
- Módulo: Excel
- Quando usar: salvar o documento e fechar o Excel.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `CloseExcelError`, `SaveExcelError`. Irmão: `.CloseAndSaveAs`.

```robin
Excel.CloseExcel.CloseAndSave Instance: ExcelInstance
```

## File

### `File.ReadTextFromFile.ReadText`
- Módulo: File
- Quando usar: ler o conteúdo de um arquivo de texto ou CSV como texto (A360
  `CSV.read`/`File.read`; na UI do analista, "CSV/TXT: Ler").
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado e rodado neste PAD (2026-10-30).
- ON ERROR: `DirectoryNotFoundError`, `FileNotFoundError`, `ReadFromFileError`.

Snippet validado pelo analista (inalterado):

```robin
File.ReadTextFromFile.ReadText
    File:       $'''%cfg_pasta_logs_atividade%/log.txt'''
    Encoding:   File.TextFileEncoding.UTF8
    Content=>   out_file_contents
```

**Forma de colagem `[colado KB: PAD 2.73, não rodado nesta instalação]`** (mesma
ressalva de `LaunchAndOpenUnderExistingProcess`):

```robin
File.ReadTextFromFile.ReadText File: $'''%cfg_pasta_logs_atividade%/log.txt''' Encoding: File.TextFileEncoding.UTF8 Content=> out_file_contents
```

### `File.ReadFromCSVFile.ReadCSV`
- Módulo: File
- Quando usar: ler um CSV como data table, com colunas (alternativa a `ReadText` quando
  o passo seguinte itera linhas).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ReadFromCsvError`.

```robin
File.ReadFromCSVFile.ReadCSV CSVFile: $'''C:\temp\test.csv''' Encoding: File.CSVEncoding.UTF8 TrimFields: True FirstLineContainsColumnNames: False ColumnsSeparator: File.CSVColumnsSeparator.SystemDefault CSVTable=> CSVTable
```

### `File.WriteText`
- Módulo: File
- Quando usar: gravar texto num arquivo (A360 `File.write`). Saída sempre em
  `C:\Users\Public\Documents\`.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `InvalidDirectoryError`, `WriteTextToFileError`.

```robin
File.WriteText File: $'''C:\Users\Public\Documents\saida.txt''' TextToWrite: $'''sample''' AppendNewLine: True IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.Unicode
```

### `File.WriteToCSVFile.WriteCSV`
- Módulo: File
- Quando usar: gravar uma data table ou lista como CSV (A360 `CSV.write`). Saída sempre
  em `C:\Users\Public\Documents\`.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `WriteToCSVError`. Irmão: `.WriteCSVWithCustomSeparator`.

```robin
File.WriteToCSVFile.WriteCSV VariableToWrite: DataTable CSVFile: $'''C:\Users\Public\Documents\saida.csv''' CsvFileEncoding: File.CSVEncoding.UTF8 IncludeColumnNames: False IfFileExists: File.IfFileExists.Overwrite ColumnsSeparator: File.CSVColumnsSeparator.SystemDefault
```

## Web (serviços)

### `Web.InvokeWebService.InvokeWebService`
- Módulo: Web
- Quando usar: chamar um endpoint REST sem corpo (A360 `REST.get` e `REST.delete`; o
  verbo vai em `Method`: `Web.Method.Get`, `Web.Method.Delete`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `DirectoryDoesNotExistError`, `InvalidCustomHeaderError`,
  `InvokeWebServiceError`.
- Substitui `Web.InvokeRestApi`, que **não existe** no PAD (ADR-029).

```robin
Web.InvokeWebService.InvokeWebService Url: $'''example''' Method: Web.Method.Get Accept: $'''application/json''' ContentType: $'''application/json''' ConnectionTimeout: 30 FollowRedirection: True ClearCookies: False FailOnErrorStatus: False EncodeRequestBody: True Encoding: Web.Encoding.AutoDetect AcceptUntrustedCertificates: False TrimRequestBody: True ResponseHeaders=> WebServiceResponseHeaders Response=> WebServiceResponse StatusCode=> StatusCode
```

### `Web.InvokeWebService.InvokeWebServicePost`
- Módulo: Web
- Quando usar: `POST` com corpo (A360 `REST.post`). Cabeçalho de autorização vai em
  `CustomHeaders`, montado a partir de variável, nunca de literal com segredo.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `DirectoryDoesNotExistError`, `InvalidCustomHeaderError`,
  `InvokeWebServiceError`.

```robin
Web.InvokeWebService.InvokeWebServicePost Url: $'''example''' Accept: $'''application/json''' ContentType: $'''application/json''' CustomHeaders: $'''example''' RequestBody: $'''example''' ConnectionTimeout: 30 FollowRedirection: True ClearCookies: False FailOnErrorStatus: False EncodeRequestBody: True Encoding: Web.Encoding.AutoDetect AcceptUntrustedCertificates: False TrimRequestBody: True StatusCode=> StatusCode Response=> WebServiceResponse ResponseHeaders=> WebServiceResponseHeaders
```

### `Web.InvokeWebService.InvokeWebServicePut`
- Módulo: Web
- Quando usar: `PUT` com corpo (A360 `REST.put`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `DirectoryDoesNotExistError`, `InvalidCustomHeaderError`,
  `InvokeWebServiceError`.

```robin
Web.InvokeWebService.InvokeWebServicePut Url: $'''example''' Accept: $'''application/json''' ContentType: $'''application/json''' CustomHeaders: $'''example''' RequestBody: $'''example''' ConnectionTimeout: 30 FollowRedirection: True ClearCookies: False FailOnErrorStatus: False EncodeRequestBody: True Encoding: Web.Encoding.AutoDetect AcceptUntrustedCertificates: False TrimRequestBody: True StatusCode=> StatusCode Response=> WebServiceResponse ResponseHeaders=> WebServiceResponseHeaders
```

### `Web.InvokeSoapService.InvokeSoapService`
- Módulo: Web
- Quando usar: chamar um serviço SOAP legado (A360 `SOAP.call`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `InvalidCustomHeaderError`, `InvokeSoapServiceError`. Irmão:
  `.InvokeSoapServiceUseAuth`.

```robin
Web.InvokeSoapService.InvokeSoapService Endpoint: $'''https://example.com/soap''' RequestBody: $'''example''' ConnectionTimeout: 30 FollowRedirection: True ClearCookies: False FailOnErrorStatus: False Encoding: Web.Encoding.AutoDetect AcceptUntrustedCertificates: False TrimRequestBody: True ResponseHeaders=> SoapServiceResponseHeaders Response=> SoapServiceResponse StatusCode=> StatusCode
```

## WebAutomation (navegador)

### `WebAutomation.LaunchEdge.LaunchEdge`
- Módulo: WebAutomation
- Quando usar: abrir o Edge numa URL (A360 `Browser.open`). Para Chrome, o irmão é
  `WebAutomation.LaunchChrome.LaunchChrome`, com os mesmos argumentos.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `InvalidUrlError`, `LaunchEdgeError`.
- Substitui `Browser.LaunchNewBrowser`, que **não existe** no PAD (ADR-029). Exige a
  extensão do PAD no navegador do ambiente.

```robin
WebAutomation.LaunchEdge.LaunchEdge Url: $'''example''' WindowState: WebAutomation.BrowserWindowState.Normal ClearCache: False ClearCookies: False WaitForPageToLoadTimeout: 60 Timeout: 60 BrowserInstance=> Browser
```

### `WebAutomation.CloseWebBrowser`
- Módulo: WebAutomation
- Quando usar: fechar o navegador aberto pelo flow (A360 `Browser.close`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `CloseWebBrowserError`.

```robin
WebAutomation.CloseWebBrowser BrowserInstance: Browser
```

### `WebAutomation.Click.Click`
- Módulo: WebAutomation
- Quando usar: clicar num elemento da página (A360 `Browser.click`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ClickElementError`, `ElementNotFoundError`.
- `needs_ui_selector`: o `Control` é um elemento web gravado. `TODO reflow` até o
  elemento existir no repositório de UI do flow.

```robin
WebAutomation.Click.Click BrowserInstance: Browser Control: appmask['Web Page \'KB Test Page\'']['Button \'Submit\''] ClickType: WebAutomation.ClickType.LeftClick MouseClick: True OffsetX: 0 OffsetY: 0 MousePositionRelativeToElement: WebAutomation.RectangleEdgePoint.MiddleCenter WaitForPageToLoadTimeout: 60
```

## UIAutomation e teclado (desktop)

### `UIAutomation.FocusWindow.FocusByTitleClass`
- Módulo: UIAutomation
- Quando usar: trazer uma janela para o primeiro plano pelo título, sem elemento
  gravado (A360 `Window.activate`, `Excel.activate`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `FocusWindowError`, `WindowNotFoundError`,
  `WindowOperationInNonInteractiveModeError`. Irmão com elemento gravado: `.Focus`.

```robin
UIAutomation.FocusWindow.FocusByTitleClass Title: $'''example''' Class: $'''example'''
```

### `UIAutomation.CloseWindow.CloseByTitleClass`
- Módulo: UIAutomation
- Quando usar: fechar uma janela pelo título (A360 `Window.close`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `CloseWindowError`, `WindowNotFoundError`,
  `WindowOperationInNonInteractiveModeError`. Irmão com elemento gravado: `.Close`.

```robin
UIAutomation.CloseWindow.CloseByTitleClass Title: $'''example''' Class: $'''example'''
```

### `UIAutomation.Click.Click`
- Módulo: UIAutomation
- Quando usar: clicar num elemento de janela desktop (A360 `MouseKeyboard.click`, parte
  de `Recorder.playback`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ClickFailedError`.
- `needs_ui_selector`: o `Element` é um elemento gravado. `TODO reflow` até o elemento
  existir no repositório de UI do flow.

```robin
UIAutomation.Click.Click Element: appmask['Window \'KB Test Window\'']['Button \'OK\''] ClickType: UIAutomation.ClickType.LeftClick MousePositionRelativeToElement: UIAutomation.RectangleEdgePoint.MiddleCenter OffsetX: 0 OffsetY: 0
```

### `MouseAndKeyboard.SendKeys.FocusAndSendKeys`
- Módulo: MouseAndKeyboard
- Quando usar: digitar texto ou teclas na janela em primeiro plano (A360
  `MouseKeyboard.type`). Nunca digitar credencial literal.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `InvalidKeystrokesError`, `NoActiveApplicationError`, `SendKeystrokesError`,
  `SendKeystrokesInNonInteractiveModeError`, `WindowNotFoundError`.

```robin
MouseAndKeyboard.SendKeys.FocusAndSendKeys TextToSend: $'''texto''' DelayBetweenKeystrokes: 10 SendTextAsHardwareKeys: False
```

## Database

### `Database.Connect.Connect`
- Módulo: Database
- Quando usar: abrir conexão com banco (A360 `Database.connect`). A connection string
  vem de configuração ou do cofre, nunca literal com senha no `Main.robin`.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ConnectToDataSourceError`, `InvalidConnectionStringError`,
  `NativeProviderNotAvailable`. O `Database.Connect` sem seletor foi removido no
  PAD 2.72 (regra `removed-ids`).

```robin
Database.Connect.Connect ConnectionString: cfg_db_connection_string Connection=> SQLConnection
```

### `Database.ExecuteSqlStatement.Execute`
- Módulo: Database
- Quando usar: executar SQL numa conexão aberta (A360 `Database.query`). Apóstrofo
  dentro do SQL é `\'` (regra `escape-apostrophe`).
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- ON ERROR: `ConnectToDataSourceError`, `InvalidConnectionStringError`,
  `NativeProviderNotAvailable`, `SqlStatementError`.

```robin
Database.ExecuteSqlStatement.Execute Connection: SQLConnection Statement: $'''example''' Timeout: 30 Result=> QueryResult
```

### `Database.Close`
- Módulo: Database
- Quando usar: fechar a conexão.
- Status: [colado KB: PAD 2.73, não rodado nesta instalação]
- **Não** aceita `ON ERROR` (`on_error: false`): proteger com `BLOCK` se precisar.

```robin
Database.Close Connection: SQLConnection
```

## Scripting

### `Scripting.RunVBScript.RunVBScript`
- Módulo: Scripting
- Quando usar: rodar um VBScript embutido no flow (A360 "VBScript: Abrir").
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado e rodado neste PAD (2026-10-30). O
  `packageName`/`commandName` A360 de origem ainda não foi confirmado por uma extração
  real (ver `a360-to-pad.md`).
- ON ERROR: `ScriptTimeoutError`. O código vai numa string de várias linhas (regra
  `multiline-strings`); apóstrofo dentro do script é `\'`.

```robin
Scripting.RunVBScript.RunVBScript
    VBScriptCode: $'''
        Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
        Set colPrintJobs = objWMIService.ExecQuery("Select * From win32_PrintJob")

        For Each objPrintJob in colPrintJobs
            objPrintJob.Delete
            WScript.Echo "Trabalho de impressão removido: " & objPrintJob.Name
        Next
    '''
    ScriptOutput=> out_vbscript_output
```

## Credenciais

### `Credentials.GetCredential`
- Módulo: nenhum (nome interno do reflow, **não é** um id Robin)
- Quando usar: obter uma credencial do cofre (A360 `CredentialVault.getCredential`/`get`),
  nunca o valor bruto do A360.
- Status: [não validado]
- A KB não tem ação de cofre de credenciais. As alternativas reais no PAD são uma
  **variável de entrada sensível** do flow (preenchida pelo cloud flow ou pelo Console)
  e, se o ambiente usar CyberArk, `Cyberark.GetPassword.GetPassword`. A escolha é do
  analista e da arquitetura do ambiente: até lá, o passo fica `TODO reflow`.

```robin
[não validado — TODO reflow: decidir com o analista a origem da credencial (variável de entrada sensível ou CyberArk) e colar aqui o texto copiado do designer do PAD]
```

## Como promover uma ação

### Para `[validado PAD: rodou]`

1. Monte a ação no designer do Power Automate Desktop **deste ambiente** (estar na KB
   não dispensa esse passo).
2. Rode o flow e confirme que a ação funciona como esperado.
3. Selecione a ação no designer, copie (Ctrl+C) e cole o texto aqui.
4. Troque o `Status` da seção para `[validado PAD: rodou]` e registre data e variante.
5. Nunca edite à mão uma linha já `[validado PAD: rodou]` sem revisão humana.

### Para `[colado KB: PAD 2.73, não rodado nesta instalação]`

Só com um registro da KB vendorizada: o cabeçalho é o `actionId` exato e o snippet é o
`golden_example` dele, com valores trocados e argumentos opcionais omitidos, nunca
argumento novo. Para uma instrução da linguagem, cite uma colagem `clean` do
`probe-corpus.json`. O teste `tests/unit/test_whitelist.py` reprova cabeçalho de ação
nesse status que não exista na KB.

### Para `[proposto — baseado em evidência pública, não testado nesta instalação]`

Só com evidência real e citável: um flow PAD público, legível como texto, cruzado com a
documentação oficial da ação. Registre a fonte exata. Ver ADR-025.
