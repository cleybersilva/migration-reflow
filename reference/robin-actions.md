# Whitelist de ações Robin

Toda ação Robin usada numa conversão **tem que vir desta lista**. Nenhuma sintaxe é
inventada — nem mesmo a que "parece óbvia" (ver [`AGENTS.md`](../AGENTS.md)).

Status possíveis, do mais fraco para o mais forte:

- **`[não validado]`** — nada foi tentado ainda. O conteúdo é um placeholder
  textual (`[não validado — TODO reflow: ...]`), nunca sintaxe real — colar
  isso no PAD não cria ação nenhuma.
- **`[proposto — baseado em evidência pública, não testado nesta
  instalação]`** — sintaxe **real** do PAD, copiada de flows públicos reais
  (repositório aberto, não documentação genérica) e cruzada com a
  documentação oficial de parâmetros de cada ação. Ninguém rodou isso
  **neste** PAD ainda. Toda entrada nesse status cita a evidência exata
  (arquivo do repositório + página oficial). Ver [ADR-025](decisions.md)
  para o racional completo e por que isso não é "inventar com mais
  confiança". Colar um snippet `proposto` tem boa chance de virar ação real
  — mas precisa de confirmação antes de qualquer execução em produção.
- **`[validado PAD: rodou]`** — alguém montou a ação de verdade no designer
  **deste** PAD, rodou e confirmou. É a única barra que conta como validação
  real.

Convenções do `Main.robin`: ver [`robin-conventions.md`](robin-conventions.md).

## Browser

### `Browser.LaunchNewBrowser`
- Módulo: Browser
- Quando usar: abrir uma nova janela de navegador para iniciar a automação web (equivalente ao A360 `Browser.open`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `Browser.CloseBrowser`
- Módulo: Browser
- Quando usar: fechar a janela de navegador aberta pelo flow.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `Browser.ClickElement`
- Módulo: Browser
- Quando usar: clicar num elemento da página (botão, link, campo).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## UI

### `UI.ActivateWindow`
- Módulo: UI
- Quando usar: trazer uma janela desktop para o primeiro plano antes de interagir com ela.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `UI.CloseWindow`
- Módulo: UI
- Quando usar: fechar uma janela desktop aberta pelo flow.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `UI.SendKeysOrClick`
- Módulo: UI
- Quando usar: simular tecla ou clique de mouse num elemento (equivalente ao A360 `MouseKeyboard`/`Recorder`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Excel

### `Excel.LaunchExcel`
- Módulo: Excel
- Quando usar: abrir uma planilha existente ou criar uma nova (equivalente
  ao A360 `Excel.open`; na UI do A360 do analista que validou esta ação,
  aparece como "Excel avançado: Abrir").
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado no designer, rodado e testado neste
  PAD (2026-10-30) — variante "abrir documento existente, sem processo
  Excel próprio" (`LaunchAndOpenUnderExistingProcess`), com `Visible: True`
  e `UseMachineLocale: False` além dos parâmetros já documentados por
  evidência pública.

```robin
Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess
    Path:              $'''%cfg_pasta_arquivos_entrada%/%cfg_numero_base%.xlsx'''
    Visible:           True
    ReadOnly:          False
    UseMachineLocale:  False
    Instance=>         out_excel_instance
```

### `Excel.ReadFromWorksheet`
- Módulo: Excel
- Quando usar: ler célula(s) de uma planilha já aberta (equivalente ao A360
  `Excel.read`). Três variantes documentadas, com níveis de confiança
  diferentes — leia a observação de cada uma antes de escolher.
- Status: [validado PAD: rodou]
- **Atenção**: esse status vale só para a variante "célula única"
  (`ReadCell`) logo abaixo — é a única rodada de verdade neste PAD. As
  outras duas variantes (planilha inteira, intervalo específico) têm
  status próprio, mais fraco, citado no início de cada uma.

**Variante validada — célula única (`ReadCell`)**: confirmada pelo
analista, montada e rodada neste PAD (2026-10-30). Na UI do A360 que deu
origem a ela, aparece como "Excel avançado: Obter planilha como tabela de
dados" — mas o código real roda `ReadCell` (uma célula, via
`StartColumn`/`StartRow`), não uma tabela inteira; se o seu caso precisa
mesmo de uma tabela/intervalo, use uma das outras duas variantes abaixo.

```robin
Excel.ReadFromExcel.ReadCell
    Instance:               out_excel_instance
    StartColumn:            $'''A'''
    StartRow:               1
    GetCellContentsMode:    Excel.GetCellContentsMode.TypedValues
    CellValue=>             out_excel_data
```

**Variante `[proposto — baseado em evidência pública, não testado nesta
instalação]` — planilha inteira (`ReadAllCells`)**: evidência de
`src/flows/config-reader-local-connectors/source/read-excel-config.txt` do
repositório
[`AgniusBartninkas/power-automate-desktop-framework`](https://github.com/AgniusBartninkas/power-automate-desktop-framework),
cruzada com a ação oficial **Read from Excel worksheet** em
[`actions-reference/excel`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/excel).

```robin
Excel.ReadFromExcel.ReadAllCells Instance: %out_excel_instance% ReadAsText: False FirstLineIsHeader: True RangeValue=> out_excel_data
```

**Variante `[não validado]` — intervalo específico (ex.: A360 `Excel.read`
com atributo `range`, tipo `A1:B3`)**: a documentação oficial confirma os
parâmetros (`Start column`/`Start row`/`End column`/`End row`), mas o
sufixo exato da sub-ação não tem evidência — nem pública nem validada
ainda.

```robin
[não validado — TODO reflow: confirmar no PAD o nome exato da sub-ação de Excel.ReadFromExcel para intervalo específico (Start column/Start row/End column/End row), depois colar o texto copiado aqui]
```

### `Excel.WriteToWorksheet`
- Módulo: Excel
- Quando usar: escrever um valor numa célula ou intervalo (equivalente ao A360 `Excel.write`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `Excel.CloseExcel`
- Módulo: Excel
- Quando usar: fechar a planilha, com ou sem salvar (equivalente ao A360 `Excel.activate` ao final do flow).
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: `src/flows/excel-closer/source/main.txt` e
  `src/flows/config-reader-local-connectors/source/read-excel-config.txt`
  do repositório
  [`AgniusBartninkas/power-automate-desktop-framework`](https://github.com/AgniusBartninkas/power-automate-desktop-framework),
  cruzado com a ação oficial **Close Excel** em
  [`actions-reference/excel`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/excel).
  Variante confirmada: fechar sem salvar (`Close`, "Do not save document" —
  o default oficial). Para "salvar antes de fechar", a documentação lista
  os parâmetros (`Before closing Excel`, `Document format`, `Document
  path`), mas a sintaxe exata colada não tem evidência direta.

```robin
Excel.CloseExcel.Close Instance: %out_excel_instance%
```

## File

### `File.ReadTextFromFile`
- Módulo: File
- Quando usar: ler o conteúdo de um arquivo de texto ou CSV (equivalente ao A360 `CSV.read`/`File.read`).
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado e rodado neste PAD (2026-10-30),
  equivalente A360 "CSV/TXT: Ler".

```robin
File.ReadTextFromFile.ReadText
    File:       $'''%cfg_pasta_logs_atividade%/log.txt'''
    Encoding:   File.TextFileEncoding.UTF8
    Content=>   out_file_contents
```

### `File.WriteTextToFile`
- Módulo: File
- Quando usar: gravar texto num arquivo novo ou existente (equivalente ao A360 `CSV.write`/`File.write`); saída sempre em `C:\Users\Public\Documents\`.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Variables

### `Variables.SetVariable`
- Módulo: Variables
- Quando usar: criar ou atualizar uma variável do flow (prefixos `step_`/`in_`/`out_`/`cfg_`, ver convenções).
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: múltiplos arquivos do repositório
  [`AgniusBartninkas/power-automate-desktop-framework`](https://github.com/AgniusBartninkas/power-automate-desktop-framework)
  (ex.: `src/flows/browser-closer/source/main.txt`: `SET Output_Status TO
  200`), cruzado com a ação oficial **Set variable** em
  [`actions-reference/variables`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/variables)
  (entrada única `To`, saída = nome da variável). Diferente do padrão
  `Módulo.Ação Param: valor` das outras ações — é uma palavra-chave própria
  da linguagem (`SET`), sem `Result=>`. Texto literal usa `$'''...'''` para
  valores de texto e `%NomeDaVariavel%` para referenciar outra variável
  dentro de uma string.

```robin
SET cfg_output_folder TO $'''C:\Users\Public\Documents\'''
```

## Loops

### `Loops.ForEach`
- Módulo: Loops
- Quando usar: iterar sobre uma lista ou tabela de itens.
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: múltiplos arquivos do mesmo repositório (ex.:
  `src/flows/flow-template-work-queues/source/generate-work-items.txt`:
  `LOOP FOREACH DataRow_CurrentWorkItem IN DataTable_WorkItems`), cruzado
  com a ação oficial **For each** em
  [`actions-reference/loops`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/loops)
  ("Value to iterate" = lista/data table/data row).

```robin
LOOP FOREACH step_item_atual IN in_lista_ou_tabela
    [proposto — corpo do laço: passos reais do flow aqui dentro]
END
```

### `Loops.LoopWhileCondition`
- Módulo: Loops
- Quando usar: repetir um bloco enquanto uma condição permanecer verdadeira.
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: `src/flows/flow-template-work-queues/source/process-work-items.txt`
  do mesmo repositório (`LOOP WHILE (...)`), cruzado com a ação oficial
  **Loop condition** em
  [`actions-reference/loops`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/loops)
  (operador, primeiro e segundo operando).

```robin
LOOP WHILE (in_condicao_operando_1 = in_condicao_operando_2)
    [proposto — corpo do laço: passos reais do flow aqui dentro]
END
```

## Conditionals

### `Conditionals.IfElse`
- Módulo: Conditionals
- Quando usar: ramificar o fluxo conforme uma condição booleana.
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: múltiplos arquivos do repositório
  [`AgniusBartninkas/power-automate-desktop-framework`](https://github.com/AgniusBartninkas/power-automate-desktop-framework)
  (ex.: `src/flows/browser-closer/source/main.txt`:
  `IF IsNotEmpty(Input_BrowserInstance) THEN ... END`, e variantes com
  `ELSE`), cruzado com as ações oficiais **If**/**Else**/**Else if** em
  [`actions-reference/conditionals`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/conditionals)
  (operador, primeiro e segundo operando). A condição pode ser uma
  comparação (`A = B`, `A <> B`, etc.) ou uma função booleana (ex.:
  `IsNotEmpty(X)`, `IsEmpty(X)`).

```robin
IF in_condicao_operando_1 = in_condicao_operando_2 THEN
    [proposto — passos reais do flow se verdadeiro]
ELSE
    [proposto — passos reais do flow se falso; bloco ELSE é opcional]
END
```

## Web

### `Web.InvokeRestApi`
- Módulo: Web
- Quando usar: chamar um endpoint REST — GET/POST/PUT/DELETE (equivalente ao A360 `REST.*`).
- Status: [não validado]
- Observação: a ação oficial equivalente é **Invoke web service**
  (parâmetros `URL`, `Method`, `Custom headers`, `Request body`, saída
  `WebServiceResponse`/`StatusCode` — ver
  [`actions-reference/web`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/web)),
  mas não encontrei um exemplo real de texto copiado citando o nome exato
  do módulo/sub-ação usado no PAD — por isso continua `[não validado]`, sem
  promover por semelhança com as outras ações.

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `Web.InvokeSoapService`
- Módulo: Web
- Quando usar: chamar um serviço SOAP legado (equivalente ao A360 `SOAP.call`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Text

### `Text.Concatenate`
- Módulo: Text
- Quando usar: concatenar textos/variáveis para montar uma string de saída.
- Status: [não validado]
- Observação: o módulo `Text` existe de verdade no PAD (vi `Text.ToNumber`
  e `Text.AppendLine` em flows reais do repositório citado acima), mas não
  encontrei evidência direta da sub-ação `Concatenate` especificamente —
  continua `[não validado]` em vez de assumir o nome por semelhança.

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Scripting

> Também não é um dos nove módulos originais do prompt; entrou pelo mesmo
> caminho de `Credentials`/`Subflows`/`Flow Control` — necessária porque um
> equivalente real apareceu numa conversão.

### `Scripting.RunVBScript`
- Módulo: Scripting
- Quando usar: rodar um script VBScript embutido no flow (equivalente ao
  A360 "VBScript: Abrir").
- Status: [validado PAD: rodou]
- Confirmado pelo analista: montado e rodado neste PAD (2026-10-30).
- **Atenção**: o nome exato do pacote/comando A360 de origem (campos
  `packageName`/`commandName` do export real) ainda não foi confirmado por
  uma extração de verdade — só a sintaxe PAD está validada. Ver
  `reference/a360-to-pad.md` para a entrada correspondente, marcada
  honestamente com essa ressalva.

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

## Credentials

> Não é um dos nove módulos originais do prompt, mas é necessária: toda credencial do
> A360 (`CredentialVault`) precisa de um equivalente PAD antes da conversão.

### `Credentials.GetCredential`
- Módulo: Credentials
- Quando usar: obter uma credencial do cofre do PAD (Credential Manager), nunca o valor bruto do A360 (equivalente ao A360 `CredentialVault.getCredential`/`get`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Subflows

> Também não é um dos nove módulos originais; necessária para dependência entre bots.

### `Flow.RunSubflow`
- Módulo: Subflows
- Quando usar: acionar outro flow/subflow (equivalente ao A360 `TaskBot.run`).
  Todo uso tem que deixar explícito no `Main.robin` que o passo sai do fluxo
  principal para rodar outro bot: nome do passo com sufixo
  `_subflow_<nome_do_bot_filho>`, comentário citando o bot filho (campo
  `target`/`botName` da entrada correspondente em `dependencies` de
  `01-inventory/inventory.json`, e se a `resolution` está `resolvida` ou
  pendente) e, quando possível, o passo envolvido na sua própria
  `FlowControl.Region` rotulada `Subflow: <nome do bot filho>` — nunca deixar
  a chamada implícita dentro de um passo comum. Ver convenção completa em
  [`robin-conventions.md`](robin-conventions.md). Se o bot filho bater com
  um nome da tabela "Subflows padrão já existentes no PAD" em
  [`subfluxos-comuns.md`](subfluxos-comuns.md), seguir a regra extra de lá
  (reaproveitar se ativo; `TODO reflow` citando o substituto se
  descontinuado). Caso análogo, mas para um padrão de passos que se repete
  **entre processos diferentes** (sem chamada explícita no legado): ver
  catálogo próprio, também em [`subfluxos-comuns.md`](subfluxos-comuns.md).
- Status: [proposto — baseado em evidência pública, não testado nesta instalação]
- Evidência: múltiplos arquivos do repositório
  [`AgniusBartninkas/power-automate-desktop-framework`](https://github.com/AgniusBartninkas/power-automate-desktop-framework)
  (ex.: `CALL CloseChrome`, `CALL GetSubflowName`), cruzado com a ação
  oficial **Run subflow** em
  [`actions-reference/flowcontrol`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/flowcontrol)
  (`Subflow name`). **Achado importante**: a sintaxe real não é um padrão
  `Módulo.Ação Param: valor` — é a palavra-chave `CALL` seguida só do nome
  do subflow, sem dois-pontos nem parâmetros nomeados nesse caso estático.
  A variante dinâmica (`Input as expression` habilitado) não tem evidência
  direta.

```robin
CALL <nome_do_bot_filho>
```

## Flow Control

> Também não é um dos nove módulos originais; ação de controle de fluxo do
> designer do Power Automate Desktop, sem efeito de execução — só organiza
> visualmente os passos.

### `FlowControl.Region`
- Módulo: FlowControl
- Quando usar: agrupar, dentro de uma "Região", os passos do mesmo estágio do
  processo (ex.: "Leitura da Base de Entrada e Logs", "Processamento",
  "Gravação de Saída", "Encerramento"). Rótulo da Região = nome do estágio,
  seguindo a mesma divisão usada em `02-docs/use-cases.md`/`architecture.md`.
  Não substitui os comentários `step_`/`in_`/`out_`/`cfg_` já exigidos pelas
  convenções — é só a moldura visual em torno deles. Use também para destacar
  uma chamada de subflow (ver `Flow.RunSubflow` acima) ou um subfluxo comum
  catalogado em [`subfluxos-comuns.md`](subfluxos-comuns.md).
- Status: [não validado]
- Observação: a ação oficial **Region**/**End region** existe de verdade
  (confirmado em
  [`actions-reference/flowcontrol`](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/flowcontrol),
  parâmetro `Name`), mas não encontrei um exemplo real de texto copiado —
  continua `[não validado]` até alguém confirmar a sintaxe exata.

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD (abertura e fechamento da Região)]
```

## Como promover uma ação

### De `[não validado]` ou `[proposto]` para `[validado PAD: rodou]`

1. Monte a ação manualmente no designer do Power Automate Desktop **deste
   ambiente** (ter evidência pública de um `[proposto]` não dispensa esse
   passo — é só um ponto de partida melhor que um placeholder em branco).
2. Rode o flow e confirme que a ação funciona como esperado.
3. Selecione a ação no designer e copie (Ctrl+C).
4. Cole o texto copiado no lugar do conteúdo anterior (placeholder ou
   snippet `proposto`).
5. Troque o `Status` da seção para `[validado PAD: rodou]` e remova a nota
   de "Evidência" (ela passa a ser supérflua — a evidência agora é a
   execução real).
6. Nunca edite à mão uma linha já marcada `[validado PAD: rodou]` sem revisão humana
   (ver [`AGENTS.md`](../AGENTS.md)).

### De `[não validado]` para `[proposto — baseado em evidência pública, não testado nesta instalação]`

Só promova se tiver evidência **real e citável**: um flow PAD real,
público, legível como texto (não um exemplo de blog sem fonte verificável),
cruzado com a documentação oficial de parâmetros da ação. Registre a fonte
exata (arquivo + link) na seção "Evidência" — sem isso, a entrada não é
`proposto`, continua `[não validado]`. Ver [ADR-025](decisions.md) para o
racional completo.
