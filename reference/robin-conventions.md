# Convenções Robin

Duas camadas: a **sintaxe que o PAD aceita** (regras da PAD Robin Action KB vendorizada,
provadas por colagens reais, ver ADR-029) e as **convenções do reflow** por cima dela.
`uv run python -m reflow lint-robin` reprova quem quebrar qualquer uma das duas.

## Método: preencher template, nunca escrever Robin

`reflow generate` aplica este método sem LLM e grava a base; o agent parte dela (ADR-035).

Não escreva Robin "de cabeça". Para cada passo:

1. Ache a ação na tabela verdade ([`a360-to-pad.md`](a360-to-pad.md)) e a seção dela na
   whitelist ([`robin-actions.md`](robin-actions.md)). Cabeçalho = id Robin real.
2. Copie o snippet da seção e troque **só os valores**. Mesmo id, mesmos nomes de
   argumento. Argumento opcional pode sair; argumento que o seletor não tem nunca entra.
3. Faltou um argumento? Ele está num **seletor irmão** (`ReadCell` → `ReadCells`), nunca
   no seletor atual. Os parâmetros tipados, os valores de enum e os irmãos de cada ação
   estão no registro dela em `vendor/pad-robin-kb/PAD_Robin_ActionKB.json` (procure por
   `"actionId": "<id>"`) ou em `uv run python -m reflow kb show <id>`.
4. Formate cada valor pelo tipo, em `vendor/pad-robin-kb/PAD_Robin_TypeReference.json`.

Ação sem seção na whitelist, ou com seção `[não validado]`, vira `# TODO reflow: ...`.
Nunca invente id, seletor, argumento ou valor de enum.

## Sintaxe que cola no PAD

Quase toda violação abaixo é **silenciosa**: o PAD descarta a colagem inteira, o canvas
fica vazio e nenhum erro aparece. Uma linha ruim custa o flow todo.

**Valores**
- Texto é `$'''valor'''` (vazio: `$''''''`). Booleano `True`/`False` e número são nus.
- Variável e expressão são **nuas**: `Instance: out_excel`, `SET total TO preco * qtd`,
  `IF lista.Count = 0 THEN`, `linha['Valor']`.
- **`%...%` só dentro de string**: `$'''Lidos %step_total% registros'''`. Fora dela
  (`Instance: %out_excel%`, `SET x TO %n + 1%`) derruba a colagem.
- Enum é qualificado (`File.TextFileEncoding.UTF8`) e só com valor listado na KB.
- Saída é `Nome=> variavel`.

**Dentro de string**
- `\` escapa o próximo caractere. **Todo apóstrofo é `\'`**: `$'''WHERE nome = \'x\''''`
  (cuidado com SQL, XPath, JavaScript e VBScript).
- Barra **antes de variável ou antes das aspas de fechamento** é dobrada:
  `$'''C:\Users\Public\Documents\\%cfg_nome%'''`, `$'''C:\Temp\\'''`. Nunca `\%`.
- Caminho UNC: `$'''\\\\servidor\pasta'''`. `%` literal: `%%`.
- String pode ter várias linhas.

**Nomes**
- Palavra reservada do PAD nunca é nome de variável nem de propriedade: `From`, `To`,
  `Step`, `End`, `In`, `Then`, `If`, `Else`, `Loop`, `Foreach`, `While`, `Set`, `Wait`,
  `Next`, `Exit`, `Label`, `Goto`, `Call`, `Case`, `Default`, `Switch`, `Block`, `Error`,
  `On`, `Not`, `And`, `Or`, `Mod`, `True`, `False`, `Global`, `Disable`, `Function`,
  `Throw`. Propriedade com esse nome: `Mail['From']`, nunca `Mail.From`.
- Variável começa por letra e precisa ser definida no flow (`SET`, saída de ação ou laço)
  antes do uso. Exceção do reflow: variáveis `in_` são **entradas do flow**, declaradas
  no designer, e o lint as aceita sem `SET`.

**Instruções**
- Uma instrução por linha. Uma ação é **sempre uma linha só**, por mais longa que fique.
- Comentário é `# texto` (ou `/# ... #/`). **`//` não é comentário Robin** e derruba a
  colagem.
- Região é `**REGION Nome` / `**ENDREGION`. `REGION`/`END REGION` derrubam a colagem.
- `ON ERROR` só em ação com `on_error: true` na KB, e caso nomeado só com erro declarado
  por ela. Dentro do tratador, só `SET`/`CALL`/`GOTO`/`THROW ERROR`. Ação sem erro
  (`Database.Close`) é protegida com `BLOCK ... ON BLOCK ERROR`. Fora disso, a execução
  disparada pela nuvem rejeita o flow inteiro ao carregar.
- Nada de `FUNCTION ... END FUNCTION`, `@@` ou `IMPORT` no corpo: o subflow é criado no
  designer e o corpo dele é colado lá dentro.
- Ação com elemento de UI (`needs_ui_selector`) só com elemento gravado no repositório de
  UI do flow. O elemento de exemplo da KB (`KB Test Window`) nunca vai para o flow: até a
  gravação, o passo é `# TODO reflow`.

## Convenções do reflow

- Um `Main.robin` por flow, pronto para colar no PAD, sem configuração externa.
- Quebra de linha **sempre CRLF** (`.gitattributes`: `*.robin text eol=crlf`). Quem gera
  o arquivo não controla a quebra de linha: depois de gerar ou alterar qualquer `.robin`,
  rode `uv run python -m reflow fix-robin-eol <projeto>` antes do `lint-robin`.
- Prefixos `step_`, `in_`, `out_`, `cfg_`; nomes em snake_case minúsculo. Configuração
  fixa é `SET cfg_<nome> TO <valor>` no topo; valor desconhecido fica `$''''''` com um
  `# TODO reflow` acima dizendo o que falta e de onde vem.
- **Pendência é comentário**: `# TODO reflow: <o que falta> (<evidência arquivo:linha>)`.
  Nunca um placeholder solto como `[não validado — ...]`, que não é Robin e derruba a
  colagem.
- Saídas somente em `C:\Users\Public\Documents\`. Segredo nunca é literal no flow:
  vem de entrada sensível `in_` ou do cofre.
- Cada passo tem um comentário acima: nome `step_NN_<verbo>_<objeto>`, origem A360
  (`arquivo:linha`), linha da tabela verdade e **status da ação na whitelist**. Ação
  `proposto` ou `colado KB` nunca é descrita como validada; só `[validado PAD: rodou]` é.
- Documentação do flow deve incluir seção "Teste" e evidências `arquivo:linha`.
- Um `**REGION` por estágio do processo (ex.: "Leitura da Base de Entrada",
  "Processamento", "Gravação de Saída", "Encerramento"), com rótulo igual ao estágio de
  `02-docs/use-cases.md`/`architecture.md`. Região organiza; não substitui os comentários.
- Chamada a outro Task Bot/subflow (A360 `TaskBot.run` → `CALL`) nunca fica implícita:
  passo com sufixo `_subflow_<nome_do_bot_filho>`, comentário citando o bot filho (campo
  `target`/`botName` de `dependencies` em `01-inventory/inventory.json`) e, quando
  possível, `**REGION Subflow: <nome do bot filho>`. Se o nome bater com um subflow
  **ativo** da tabela "Subflows padrão já existentes no PAD" em
  [`subfluxos-comuns.md`](subfluxos-comuns.md), o comentário diz que é subflow padrão já
  disponível: reaproveitar, nunca reimplementar. Se bater com um **descontinuado** (hoje:
  `Log_Splunk`, substituído pelo Datadog), o passo vira `# TODO reflow` citando o
  substituto.
- Subfluxo **comum entre processos** (sequência repetida em mais de um projeto,
  catalogada em [`subfluxos-comuns.md`](subfluxos-comuns.md) com status `catalogado`):
  passo com sufixo `_subfluxo_comum_<slug_do_padrao>`, comentário citando a entrada e a
  recomendação de reuso, e, quando possível,
  `**REGION Subfluxo comum: <nome do padrão> (candidato a reuso)`. Entrada `proposto`
  nunca é sinalizada como `catalogado`.

Whitelist: [`robin-actions.md`](robin-actions.md). Tabela verdade A360 → PAD:
[`a360-to-pad.md`](a360-to-pad.md). Classificação: [`classification-rubric.md`](classification-rubric.md).
Padrões recorrentes: [`subfluxos-comuns.md`](subfluxos-comuns.md). KB vendorizada:
[`vendor/pad-robin-kb/README.md`](vendor/pad-robin-kb/README.md).
