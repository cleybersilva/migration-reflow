# uc-01-excel-vault

Flow Robin convertido a partir do projeto A360 `a360-excel-vault`, escopo
**somente a parte confirmada** do fluxo aprovada no checkpoint humano —
`Excel/open` → `Excel/read` → `REST/post` (autenticado pela credencial de
`CredentialVault/get`) — conforme `01-inventory/inventory.json:2-49`,
`02-docs/use-cases.md` (UC-01) e `02-docs/process-flow.md` (passos 1–4).

Os dois comandos não reconhecidos pela extração — `CustomPackage/transform`
(`main.json:5`) e `Browser/unmappedAction` (`main.json:6`), registrados em
`01-inventory/inventory.json:54-69` — **não fazem parte deste flow**:
ficaram explicitamente fora do escopo aprovado no checkpoint, conforme
**ADR-028** (`docs/decisions.md`) e o veredito `PARTIAL` em
`output/a360-excel-vault/03-classification/classification.md`. Eles
aparecem em `Main.robin` só como comentário `# TODO reflow` dentro da Região
"Fora do escopo aprovado (ADR-028)".

## Origem

- Projeto: `a360-excel-vault` (origem A360, `00-manifest.json`).
- Caso de uso: `UC-01` — "Envio de dados de planilha Excel para sistema
  externo autenticado por credencial do cofre" (`02-docs/use-cases.md`),
  restrito à parte confirmada do fluxo.
- Classificação: `PARTIAL` (`03-classification/classification.md`), com
  segunda opinião concordante (`03-classification/review.md`).
- Checkpoint humano: aprovado, registrado em
  `output/a360-excel-vault/00-manifest.json` → `checkpoint`
  (`decision: "approved"`, `recorded_at: 2026-10-31T01:55:17Z`). Escopo
  exato da aprovação documentado em **ADR-028** (`docs/decisions.md`).

## Entrada do flow (declarar no designer)

- `in_rest_token`: texto, marcada como **sensível**. Token de autenticação usado no
  cabeçalho `Authorization` do step_03 (decisão do analista, 2026-11-05). Nunca valor
  no arquivo.

## Passo a passo convertido

Reconvertido em 2026-11-04 (ADR-029) e corrigido em 2026-11-05 a partir da auditoria
semântica (`review.md`) e das decisões do analista (ver `notas-conversao.md`).

1. **step_01_open_excel_file**: abre a planilha (`main.json:1`, `Excel.open` →
   `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`). A ação é `[validado PAD:
   rodou]` no snippet multilinha do analista; a forma de uma linha usada aqui é
   `[colado KB: PAD 2.73, não rodado nesta instalação]`. O caminho não acrescenta
   extensão: `cfg_excel_file_name` vai com a extensão.
2. **step_02_read_excel_range**: lê o intervalo (`main.json:2`, `Excel.read` →
   `Excel.ReadFromExcel.ReadCells`, `[colado KB: PAD 2.73, não rodado nesta instalação]`).
3. **step_02b_close_excel_instance**: fecha o Excel sem salvar (`Excel.CloseExcel.Close`,
   `[colado KB: PAD 2.73, não rodado nesta instalação]`). Diferença deliberada em relação
   ao legado, que não fecha a planilha.
4. **step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre**: só documentação.
   A credencial chega por `in_rest_token` (sem ação de cofre). Vem antes do REST porque o
   POST depende dela (no legado, `main.json:4` vem depois de `main.json:3`).
5. **step_03_post_data_to_rest_api**: POST ao sistema externo (`main.json:3`, `REST.post`
   → `Web.InvokeWebService.InvokeWebServicePost`, `[colado KB: PAD 2.73, não rodado nesta
   instalação]`), com `Authorization` montado em `CustomHeaders` a partir de
   `cfg_rest_auth_scheme` e `in_rest_token`.

Regiões, nesta ordem:

- "Leitura da Base de Entrada": step_01, step_02, step_02b.
- "Subfluxo comum: Obter credencial do cofre (candidato a reuso)": step_04.
- "Envio de Dados ao Sistema Externo (REST)": step_03.
- "Fora do escopo aprovado (ADR-028)": comandos 5 e 6, não convertidos.

Valores que a extração não capturou (arquivo, intervalo, URL, `Accept`/`ContentType`,
esquema de autorização) são `SET cfg_... TO $''''''` com `# TODO reflow` acima. Formato
do corpo e critério de status HTTP também ficaram como `# TODO reflow`. Lista completa em
`notas-conversao.md` → "Pendências antes de rodar no designer".

## Comandos fora do escopo aprovado (ADR-028)

`CustomPackage/transform` (`main.json:5`) e `Browser/unmappedAction`
(`main.json:6`) não têm ação PAD mapeada em `reference/a360-to-pad.md`
("pendente de classificação") e estão explicitamente fora do checkpoint aprovado
(`ADR-028`, `docs/decisions.md`). Requerem revisão humana e uma nova entrada na tabela
verdade antes de qualquer conversão futura.

## Teste

Nenhum teste foi executado no PAD ainda. `fix-robin-eol` e `lint-robin` rodaram em
2026-11-05 sem achados, e a auditoria semântica (`review.md`) não tem achado bloqueante.
Gerar o flow de teste (`05-test/`) não depende do designer; **executá-lo** depende: antes
de rodar no PAD, um analista precisa declarar `in_rest_token` (sensível) no designer,
preencher as `cfg_` pendentes e decidir o formato do corpo, o esquema de autorização e o
critério de status HTTP. Só a execução real promove as ações usadas para
`[validado PAD: rodou]` (ver `reference/robin-actions.md` → "Como promover uma ação").
