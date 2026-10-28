# Whitelist de ações Robin

Toda ação Robin usada numa conversão **tem que vir desta lista**. Nenhuma sintaxe é
inventada: o snippet de cada ação só deixa de ser `[não validado]` depois que alguém
monta a ação de verdade no designer do Power Automate Desktop, copia o texto gerado
(Ctrl+C) e substitui o placeholder abaixo por esse texto exato.

Convenções do `Main.robin`: ver [`robin-conventions.md`](robin-conventions.md).

Status possíveis: `[validado PAD: rodou]` (copiado de uma execução real) ou
`[não validado]` (ainda é só um placeholder — nunca usar como se fosse sintaxe real).

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
- Quando usar: abrir uma planilha existente ou criar uma nova (equivalente ao A360 `Excel.open`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `Excel.ReadFromWorksheet`
- Módulo: Excel
- Quando usar: ler um intervalo de células de uma planilha já aberta (equivalente ao A360 `Excel.read`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
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
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## File

### `File.ReadTextFromFile`
- Módulo: File
- Quando usar: ler o conteúdo de um arquivo de texto ou CSV (equivalente ao A360 `CSV.read`/`File.read`).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
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
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Loops

### `Loops.ForEach`
- Módulo: Loops
- Quando usar: iterar sobre uma lista ou tabela de itens.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

### `Loops.LoopWhileCondition`
- Módulo: Loops
- Quando usar: repetir um bloco enquanto uma condição permanecer verdadeira.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Conditionals

### `Conditionals.IfElse`
- Módulo: Conditionals
- Quando usar: ramificar o fluxo conforme uma condição booleana.
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
```

## Web

### `Web.InvokeRestApi`
- Módulo: Web
- Quando usar: chamar um endpoint REST — GET/POST/PUT/DELETE (equivalente ao A360 `REST.*`).
- Status: [não validado]

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

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
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
  [`robin-conventions.md`](robin-conventions.md).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD]
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
  uma chamada de subflow (ver `Flow.RunSubflow` acima).
- Status: [não validado]

```robin
[não validado — TODO reflow: colar aqui o texto copiado do designer do PAD (abertura e fechamento da Região)]
```

## Como promover uma ação para `[validado PAD: rodou]`

1. Monte a ação manualmente no designer do Power Automate Desktop.
2. Rode o flow e confirme que a ação funciona como esperado.
3. Selecione a ação no designer e copie (Ctrl+C).
4. Cole o texto copiado no lugar do placeholder `[não validado — TODO reflow: ...]`.
5. Troque o `Status` da seção para `[validado PAD: rodou]`.
6. Nunca edite à mão uma linha já marcada `[validado PAD: rodou]` sem revisão humana
   (ver [`AGENTS.md`](../AGENTS.md)).
