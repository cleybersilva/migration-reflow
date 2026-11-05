# uc-01-excel-vault — teste

Roteiro de teste do flow convertido em
`output/a360-excel-vault/04-pad/uc-01-excel-vault/Main.robin`, cobrindo UC-01
(`02-docs/use-cases.md:3-18`): abrir a planilha, ler o intervalo, obter a credencial e
enviar os dados por HTTP POST autenticado, sem expor o valor da credencial.

**Este teste foi gerado, não executado.** Nenhum cenário abaixo foi rodado no PAD. As
ações do `Main.robin` ao lado estão `[colado KB: PAD 2.73, não rodado nesta instalação]`
(ver `notas-conversao.md`); o resultado real só existe depois que um analista colar o
flow no designer do PAD e executar cada cenário (ver `docs/runbook.md`).

Atualizado em 2026-11-05 para a versão do flow principal com R3-1 (fechamento do Excel
renomeado para `step_07_close_excel_file`), R8-6 (`cfg_rest_auth_prefix` no lugar de
`cfg_rest_auth_scheme`, prefixo e token juntados sem espaço entre eles) e R8-7 (step_01
abre com `ReadOnly: True`).

## Escopo

- Dentro: `main.json:1-4` (escopo aprovado no checkpoint, ADR-028): `Excel/open`,
  `Excel/read`, `REST/post`, `CredentialVault/get` (este último substituído pela entrada
  sensível `in_rest_token`, decisão do analista de 2026-11-05).
- Fora: `CustomPackage/transform` (`main.json:5`) e `Browser/unmappedAction`
  (`main.json:6`), não convertidos (ADR-028).
- `02-docs/business-rules.md` (RN-01) não registra nenhuma condicional. Os cenários
  cobrem o caminho feliz da sequência linear e os modos de falha apontados pela
  auditoria (`04-pad/uc-01-excel-vault/review.md`, R8-4, R8-6 e a conclusão), sem
  inventar regra de negócio sem evidência `arquivo:linha`.
- Numeração (R3-1): step_01 a step_06 seguem a ordem do legado; `step_07_close_excel_file`
  não tem origem no legado e roda logo após a leitura. `step_08_record_test_result` só
  existe neste teste (registro manual do resultado).

## Pré-condições (todos os cenários)

1. Rodar `uv run python -m reflow fix-robin-eol a360-excel-vault` e
   `uv run python -m reflow lint-robin a360-excel-vault` sem achados.
2. No designer, criar a variável de **entrada** `in_rest_token`: tipo texto, marcada como
   **sensível**. O valor é informado só na hora da execução, nunca no `Main.robin`, neste
   README ou na evidência.
3. Preencher as `cfg_` do topo do `Main.robin` com o analista (valores não capturados pela
   extração, `01-inventory/inventory.json:15-49`): `cfg_excel_input_folder`,
   `cfg_excel_file_name` (com extensão, R8-5), `cfg_excel_start_column`,
   `cfg_excel_start_row`, `cfg_excel_end_column`, `cfg_excel_end_row`,
   `cfg_rest_endpoint_url`, `cfg_rest_accept`, `cfg_rest_content_type`,
   `cfg_rest_auth_prefix` (esquema já seguido de um espaço, ou vazia se o destino aceitar
   o token puro, R8-6), e `cfg_test_case_id` com o id do cenário.
4. Endpoint de destino em **homologação**, nunca produção.
5. Decidir antes, com o analista: formato do corpo esperado pelo destino (R8-2), prefixo
   do cabeçalho de autorização (R8-6) e status HTTP que conta como sucesso (R8-4). Sem
   essas decisões, o "resultado esperado" de CT-01 a CT-03 não tem como ser conferido.
6. Evidências (print, status, trecho da resposta sem dado sensível) salvas só em
   `C:\Users\Public\Documents\`.

Atenção: o POST usa `FailOnErrorStatus: False`. Uma resposta 4xx/5xx **não** interrompe o
flow; o flow termina sem erro mesmo sem ter autenticado. Em todo cenário com POST, o
analista confere `out_rest_status_code` e `out_rest_response` no painel de variáveis.

## Cenários

### CT-01: Caminho feliz, leitura do intervalo e POST com o status esperado

- **Passos:**
  1. Executar `step_01_open_excel_file` (origem `Excel/open`, `main.json:1`), que abre o
     arquivo em modo somente leitura (`ReadOnly: True`, R8-7).
  2. Executar `step_02_read_excel_range` (origem `Excel/read`, `main.json:2`).
  3. Executar `step_07_close_excel_file` (sem origem no legado, R8-1 e R3-1).
  4. Executar `step_03_post_data_to_rest_api` (origem `REST/post`, `main.json:3`), com o
     token vindo de `in_rest_token` (origem `CredentialVault/get`, `main.json:4`).
- **Dado de entrada:** arquivo existente na pasta de `cfg_excel_input_folder`, com dados
  no intervalo das `cfg_excel_*`; `cfg_rest_endpoint_url` de homologação acessível;
  `cfg_rest_accept`/`cfg_rest_content_type` no formato confirmado pelo destino;
  `cfg_rest_auth_prefix` com o prefixo confirmado (esquema mais espaço final, ou vazia se
  o destino aceitar token puro); `in_rest_token` válido.
- **Resultado esperado:** o Excel abre sem erro, em modo somente leitura; `out_excel_data`
  traz exatamente as linhas e colunas do intervalo configurado; nenhum processo Excel
  sobra aberto após o `step_07`; `out_rest_status_code` igual ao status de sucesso
  definido pelo analista (faixa 2xx); o destino registra os dados enviados; o valor de
  `in_rest_token` não aparece em nenhuma variável de saída, log ou evidência (UC-01,
  `02-docs/use-cases.md:16-18`).
- **Resultado observado (analista):**

### CT-02: Falha de autenticação, 401 por prefixo ou token errado

- **Passos:**
  1. Executar `step_01`, `step_02` e `step_07` como em CT-01.
  2. Executar `step_03_post_data_to_rest_api` com credencial inválida.
  3. Conferir `out_rest_status_code` no painel de variáveis (o flow não para sozinho).
- **Dado de entrada:** igual a CT-01, exceto por uma das duas variações (rodar as duas):
  (a) `in_rest_token` com um token inválido ou expirado de homologação; (b)
  `cfg_rest_auth_prefix` com esquema errado, ou ausente (vazia), quando o destino exige
  esquema antes do token (R8-6: o cabeçalho junta prefixo e token sem espaço entre eles,
  então prefixo vazio envia o token puro, que esse destino recusa).
- **Resultado esperado:** `out_rest_status_code` igual a `401` (ou o status de
  autenticação negada que o destino documentar); nenhum dado gravado no destino; o flow
  **termina sem erro de ação**, porque `FailOnErrorStatus: False` (R8-4), o que confirma
  que a falha só é visível pela variável de status; nenhum valor de token em
  `out_rest_response`, `out_rest_response_headers` ou evidência.
- **Resultado observado (analista):**

### CT-03: Corpo em formato inesperado pelo destino

- **Passos:**
  1. Executar `step_01`, `step_02` e `step_07` como em CT-01.
  2. Executar `step_03_post_data_to_rest_api` com `RequestBody` igual à DataTable
     `out_excel_data` interpolada como texto (comportamento atual, R8-2).
  3. Conferir `out_rest_status_code` e `out_rest_response`.
- **Dado de entrada:** igual a CT-01, com `cfg_rest_content_type` declarando um formato
  estruturado que o destino valida (o confirmado pelo analista), enquanto o corpo segue
  sendo o texto da DataTable sem serialização.
- **Resultado esperado:** se o destino valida o formato, `out_rest_status_code` na faixa
  4xx de corpo inválido (ex.: `400`, `415` ou `422`) com a mensagem do destino em
  `out_rest_response`, e nenhum registro criado no destino; o flow termina sem erro de
  ação (`FailOnErrorStatus: False`). Se o destino aceitar o corpo (2xx), registrar o
  conteúdo gravado lá: isso decide se a serialização pendente de R8-2 é necessária.
- **Resultado observado (analista):**

### CT-04: Arquivo Excel inexistente

- **Passos:**
  1. Executar `step_01_open_excel_file` com um nome de arquivo que não existe.
- **Dado de entrada:** `cfg_excel_file_name` com um nome inexistente na pasta de
  `cfg_excel_input_folder` (ex.: `$'''arquivo-inexistente.xlsx'''`); demais `cfg_` e
  `in_rest_token` como em CT-01.
- **Resultado esperado:** `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess` falha
  com erro de abertura do documento (`OpenDocumentError`, declarado na KB); o flow para
  nesse passo; `step_02`, `step_07` e `step_03` não executam; **nenhum** POST chega ao
  destino; conferir no Gerenciador de Tarefas se ficou processo Excel aberto e registrar.
- **Resultado observado (analista):**

### CT-05: Intervalo inexistente ou inválido na planilha

- **Passos:**
  1. Executar `step_01_open_excel_file` com o arquivo válido de CT-01.
  2. Executar `step_02_read_excel_range` com um intervalo inválido.
  3. Conferir no Gerenciador de Tarefas se ficou processo Excel aberto.
- **Dado de entrada:** arquivo válido; `cfg_excel_start_column` ou
  `cfg_excel_end_column` com uma coluna que não existe no Excel (ex.: `$'''ZZZZZ'''`,
  além do limite de colunas), ou linha final menor que a inicial.
- **Resultado esperado:** `Excel.ReadFromExcel.ReadCells` falha com erro de leitura
  (`ReadCellsError`, declarado na KB); o flow para nesse passo; `step_03` não executa e
  nenhum POST chega ao destino. Como o flow não tem tratamento de erro, `step_07` também
  não executa: conferir se o processo Excel ficou aberto e registrar (o arquivo foi
  aberto com `ReadOnly: True`, R8-7, então o esperado é que ele continue livre para
  edição por outro usuário mesmo com o processo sobrando).
- **Resultado observado (analista):**

## Tabela de resultados

| Cenário | Passos | Dado de entrada | Resultado esperado | Resultado observado | Status |
| --- | --- | --- | --- | --- | --- |
| CT-01 | step_01 → step_02 → step_07 → step_03 | Arquivo e intervalo válidos, endpoint de homologação, `cfg_rest_auth_prefix` e token válidos | `out_excel_data` com o intervalo; Excel fechado no step_07; `out_rest_status_code` = sucesso definido (2xx); token não exposto | | (a executar no PAD) |
| CT-02 | step_01 → step_02 → step_07 → step_03 | (a) token inválido; (b) `cfg_rest_auth_prefix` errada ou vazia quando o destino exige esquema | `out_rest_status_code` = 401; nada gravado no destino; flow termina sem erro de ação (falha só visível no status) | | (a executar no PAD) |
| CT-03 | step_01 → step_02 → step_07 → step_03 | `cfg_rest_content_type` estruturado com corpo = DataTable como texto | 4xx de corpo inválido (400/415/422) e nada gravado, ou 2xx com conteúdo registrado para decidir R8-2 | | (a executar no PAD) |
| CT-04 | step_01 | `cfg_excel_file_name` inexistente | `OpenDocumentError`; step_02, step_07 e step_03 não executam; nenhum POST | | (a executar no PAD) |
| CT-05 | step_01 → step_02 | Coluna inexistente ou linha final menor que a inicial | `ReadCellsError`; step_07 e step_03 não executam; nenhum POST; registrar se o Excel ficou aberto | | (a executar no PAD) |

As colunas **Resultado observado** e **Status** ficam vazias até a execução real. Só o
analista as preenche (`passou`/`falhou` + evidência em `C:\Users\Public\Documents\`),
depois de colar o `Main.robin` deste teste no designer do PAD e rodar cada cenário de
verdade (ver `docs/runbook.md`). Este documento nunca marca cenário como aprovado.
