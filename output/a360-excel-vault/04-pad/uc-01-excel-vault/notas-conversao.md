# Notas de conversão — uc-01-excel-vault

Ações Robin usadas em `Main.robin`, todas da whitelist
`reference/robin-actions.md`, com o id Robin real (ancorado na PAD Robin Action KB
vendorizada, ADR-029). Mapeamento de origem em `reference/a360-to-pad.md`. Escopo
restrito à parte confirmada do fluxo, aprovada no checkpoint (ADR-028,
`docs/decisions.md`): `Excel/open`, `Excel/read`, `REST/post`, `CredentialVault/get`.

Reconvertido em 2026-11-04: a versão anterior não colava no PAD (comentários `//`,
linhas `cfg_x: "..."` e placeholders soltos derrubavam a colagem inteira, 171 achados no
`lint-robin` novo) e usava nomes que não existem no PAD (`Web.InvokeRestApi`,
`FlowControl.Region`).

Corrigido em 2026-11-05 a partir da auditoria semântica
(`04-pad/uc-01-excel-vault/review.md`) e das decisões do analista listadas abaixo, em
duas rodadas (a segunda trata R3-1, R8-6 e R8-7).

- `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess` — step_01_open_excel_file; equivalente a `Excel.open` (`main.json:1`); a ação é `[validado PAD: rodou]` no snippet **multilinha** do analista (2026-10-30), e a forma de **uma linha** usada no `Main.robin` é `[colado KB: PAD 2.73, não rodado nesta instalação]` (R7-1); `Path` sem extensão fixa, a extensão vem em `cfg_excel_file_name` (R8-5); `ReadOnly: True` porque o flow só lê (R8-7: só o valor do argumento muda em relação ao snippet validado, mesmo seletor); ressalva em `reference/a360-to-pad.md` sobre o `packageName` simples "Excel" (sem "avançado") ainda não confirmado como o mesmo pacote AA360 validado.
- `Excel.ReadFromExcel.ReadCells` — step_02_read_excel_range; equivalente a `Excel.read` (`main.json:2`, atributo `range`); seletor de **intervalo** (`StartColumn`/`StartRow`/`EndColumn`/`EndRow`); status `[colado KB: PAD 2.73, não rodado nesta instalação]`. Não usar `ReadCell` (célula única) nem `ReadAllCells` (planilha inteira).
- `Excel.CloseExcel.Close` — step_07_close_excel_file; **sem origem no legado** (não há `Excel/close` em `main.json:1-4`): diferença deliberada em relação ao legado, por decisão do analista (R8-1), logo após a leitura, sem salvar; numerado 07 por não ter origem no legado (R3-1); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Web.InvokeWebService.InvokeWebServicePost` — step_03_post_data_to_rest_api; equivalente a `REST.post` (`main.json:3`, atributos `body` e `authorization`); status `[colado KB: PAD 2.73, não rodado nesta instalação]`; `CustomHeaders` monta `Authorization` juntando `cfg_rest_auth_prefix` (vazia, TODO) e a entrada sensível `in_rest_token`, sem espaço entre as duas expressões (R1-1, R8-6); `Accept`/`ContentType` são obrigatórios no seletor e vêm de `cfg_rest_accept`/`cfg_rest_content_type` vazias com TODO, sem afirmar JSON (R8-2); corpo mantido como `out_excel_data` interpolado, com TODO de formato (R8-2); tratamento de status HTTP em TODO, sem `ON ERROR` (R8-4).
- `**REGION` — organiza os estágios do flow, na ordem "Leitura da Base de Entrada", "Subfluxo comum: Obter credencial do cofre (candidato a reuso)", "Envio de Dados ao Sistema Externo (REST)", "Fora do escopo aprovado (ADR-028)"; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `SET` — configuração `cfg_` no topo; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.

`Credentials.GetCredential` (seção `[não validado]` da whitelist, não é id Robin real)
**não é mais usada** nem como placeholder: o step_04 documenta que a credencial chega por
entrada sensível `in_`, sem ação de cofre.

## Decisões do analista (Cleyber, 2026-11-05)

1. **Credencial**: vem da variável de entrada sensível `in_rest_token`, declarada no
   designer (tipo texto, marcada sensível). Nunca valor no arquivo. O step_04 virou
   comentário de documentação, sem ação de cofre. `cfg_credential_reference` foi
   **removida** (ficaria sem uso); a referência `main.json:4:credential-vault` continua
   só como comentário de rastreio no step_04.
2. **Autenticação do REST**: token no cabeçalho, dentro de `CustomHeaders` da ação POST
   atual (seletor mantido, sem trocar para o irmão com autenticação própria, que não tem
   seção na whitelist; isso também encerra a dúvida de R8-3). Prefixo (esquema antes do
   token) **não confirmado**: fica em `cfg_rest_auth_prefix` vazia com TODO.
   Regiões reordenadas: a credencial (step_04) vem antes do REST (step_03); os nomes
   `step_NN` continuam ligados à ordem do legado (R1-1).
3. **Corpo do POST**: a confirmar com o analista. Corpo mantido, com TODO explícito de
   formato; `Accept`/`ContentType` não podem ser omitidos (obrigatórios na KB,
   `PAD_Robin_ActionKB.json:52835-52847`), então viraram `cfg_` vazias com TODO (R8-2).
4. **Fechar Excel**: sim, `Excel.CloseExcel.Close` logo após a leitura (R8-1).
5. **Numeração do fechamento (R3-1)**: `step_02b_close_excel_instance` renomeado para
   `step_07_close_excel_file`. Os números step_01 a step_06 ficam presos à ordem do
   legado (`main.json:1-6`; 05 e 06 fora do escopo); o fechamento não tem origem no
   legado, então recebe o próximo número livre, mesmo continuando posicionado logo após
   a leitura na Região "Leitura da Base de Entrada".
6. **Prefixo do cabeçalho (R8-6)**: `cfg_rest_auth_scheme` trocada por
   `cfg_rest_auth_prefix` (vazia), que guarda o esquema já com o espaço final. O
   cabeçalho fica `Authorization: %cfg_rest_auth_prefix%%in_rest_token%`, sem espaço
   entre as duas expressões: prefixo vazio = token puro, sem espaço duplo. Preencher com
   o esquema seguido de espaço, ou deixar vazio se o destino aceitar o token sem
   prefixo; confirmar com o analista.
7. **Modo de abertura (R8-7)**: step_01 abre com `ReadOnly: True`, porque o flow só lê.
   Só o valor do argumento muda; o seletor é o mesmo do snippet validado.

## Achados da auditoria tratados

- **R4-1 / R4-2**: seção "Teste" do README separa gerar `05-test/` de executá-lo e troca
  o estado datado dos gates por uma regra (rodar `fix-robin-eol` e `lint-robin` depois de
  qualquer alteração).
- **R1-1**: autenticação por `in_rest_token` em `CustomHeaders`; Região da credencial
  movida para antes do REST, com comentário do motivo no topo e no step_04.
- **R5-1**: comentário do step_04 cita `reference/subfluxos-comuns.md#obter-credencial-do-cofre`
  e as duas evidências (`a360-browser-rest/input/main.json:3`,
  `a360-excel-vault/input/main.json:4`).
- **R7-1**: step_01 descrito como ação validada no snippet multilinha, forma de uma linha
  `[colado KB: PAD 2.73, não rodado nesta instalação]` (Main.robin, notas e README).
- **R8-1**: `Excel.CloseExcel.Close` incluído.
- **R8-2**: `Accept`/`ContentType` em `cfg_` vazias; TODO de formato do corpo.
- **R8-4**: TODO pedindo critério de status HTTP e se a falha interrompe o flow; nenhum
  `ON ERROR` inventado. O TODO agora cita que um 401 por prefixo errado só aparece em
  `out_rest_status_code` (R8-6).
- **R8-5**: `Path` sem `.xlsx` fixo; TODO diz que `cfg_excel_file_name` vai com extensão.
- **R3-1**: passo de fechamento renomeado para `step_07_close_excel_file` (decisão 5),
  com o motivo no comentário do passo, no topo do `Main.robin` e no README.
- **R8-6**: `cfg_rest_auth_prefix` no lugar de `cfg_rest_auth_scheme`, cabeçalho sem
  espaço entre prefixo e token (decisão 6); TODO acima do `SET` atualizado.
- **R8-7**: `ReadOnly: True` no step_01 (decisão 7).

## Fora da whitelist / fora do escopo (não citados acima de propósito)

`CustomPackage.transform` (`main.json:5`) e `Browser.unmappedAction`
(`main.json:6`) **não** foram convertidos e **não** têm entrada na whitelist
`reference/robin-actions.md` nem ação mapeada em `reference/a360-to-pad.md` (lá aparecem
como "pendente de classificação"). Estão fora do checkpoint aprovado (ADR-028) e
aparecem no `Main.robin` só como comentário dentro da Região "Fora do escopo aprovado
(ADR-028)".

## Subfluxo comum sinalizado

O **step_04** corresponde à entrada `obter-credencial-do-cofre`, catalogada (status
`catalogado`) em `reference/subfluxos-comuns.md#obter-credencial-do-cofre`, com as
evidências `a360-browser-rest/input/main.json:3` e `a360-excel-vault/input/main.json:4`
(este passo). Recomendação registrada no catálogo: extrair para um subflow compartilhado
(ex.: `Subflow_ObterCredencialDoCofre`) que recebe a referência da credencial e devolve a
credencial, em vez de repetir o passo isolado a cada conversão. Com a decisão de entrada
sensível, a recomendação continua válida para quando houver cofre no PAD.

Não há dependência `TaskBot.run`/`CALL` neste projeto — `dependencies` está vazio em
`01-inventory/inventory.json:34` — então essa sinalização é exclusivamente do catálogo
de padrões repetidos entre processos. Nenhum candidato a novo subfluxo comum identificado.

## Variáveis de entrada a declarar no designer

- Entrada `in_rest_token`: texto, **sensível**. Token usado no cabeçalho `Authorization` do
  step_03.

## Pendências antes de rodar no designer

- **Valores não capturados** pela extração determinística (`01-inventory/inventory.json`,
  `02-docs/data-sources.md`, `02-docs/integrations.md`): preencher com o analista
  `cfg_excel_input_folder`, `cfg_excel_file_name` (com extensão), `cfg_excel_start_column`,
  `cfg_excel_start_row`, `cfg_excel_end_column`, `cfg_excel_end_row`,
  `cfg_rest_endpoint_url`, `cfg_rest_accept`, `cfg_rest_content_type` e
  `cfg_rest_auth_prefix` (esquema seguido de espaço, ou vazio).
- **Formato do corpo** do POST (R8-2) e eventual serialização da DataTable.
- **Critério de sucesso HTTP** (R8-4), incluindo o 401 por prefixo errado (R8-6).
- Tabela verdade (`reference/a360-to-pad.md`): as linhas "Excel | open" e "Excel | read"
  ainda têm a ressalva do `packageName` simples `Excel` (sem "avançado").
- **A1** (`02-docs/risks.md`): `Browser/unmappedAction` (fora do escopo) pode depender
  de extensão de navegador específica, só relevante se entrar em escopo no futuro.
