# uc-01-excel-vault

Flow Robin convertido a partir do projeto A360 `a360-excel-vault`, escopo
**somente a parte confirmada** do fluxo aprovada no checkpoint humano —
`Excel/open` → `Excel/read` → `REST/post` (autenticado por
`CredentialVault/get`) — conforme `01-inventory/inventory.json:2-49`,
`02-docs/use-cases.md` (UC-01) e `02-docs/process-flow.md` (passos 1–4).

Os dois comandos não reconhecidos pela extração — `CustomPackage/transform`
(`main.json:5`) e `Browser/unmappedAction` (`main.json:6`), registrados em
`01-inventory/inventory.json:54-69` — **não fazem parte deste flow**:
ficaram explicitamente fora do escopo aprovado no checkpoint, conforme
**ADR-028** (`docs/decisions.md`) e o veredito `PARTIAL` em
`output/a360-excel-vault/03-classification/classification.md`. Eles
aparecem em `Main.robin` só como comentário `# TODO reflow` dentro da Região
"Fora do escopo aprovado (ADR-028)", para manter a sequência do processo
legível — nunca como se tivessem sido convertidos.

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
  exato da aprovação (somente Excel + REST + CredentialVault) documentado em
  **ADR-028** (`docs/decisions.md`), porque o manifesto hoje não tem campo
  próprio para registrar um escopo parcial.

## Passo a passo convertido

Reconvertido em 2026-11-04 com a whitelist ancorada na PAD Robin Action KB vendorizada
(ADR-029). O `Main.robin` anterior não colava no PAD. Este passa no `lint-robin`, que
agora interpreta a sintaxe Robin.

1. **step_01_open_excel_file**: abre a planilha Excel de entrada (`main.json:1`,
   `Excel.open` → `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`,
   `[validado PAD: rodou]`).
2. **step_02_read_excel_range**: lê o intervalo de dados (`main.json:2`, `Excel.read` →
   `Excel.ReadFromExcel.ReadCells`, `[colado KB: PAD 2.73, não rodado nesta instalação]`).
3. **step_03_post_data_to_rest_api**: envia os dados via POST ao sistema externo
   (`main.json:3`, `REST.post` → `Web.InvokeWebService.InvokeWebServicePost`,
   `[colado KB: PAD 2.73, não rodado nesta instalação]`).
4. **step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre**: obtém a
   credencial (`main.json:4`, `CredentialVault.get` → `Credentials.GetCredential`,
   `[não validado]`, por isso é só `# TODO reflow`), nunca o valor bruto, só a
   referência (`main.json:4:credential-vault`).

Os passos estão organizados em `**REGION` / `**ENDREGION`:

- "Leitura da Base de Entrada": steps 1 e 2.
- "Envio de Dados ao Sistema Externo (REST)": step 3.
- "Subfluxo comum: Obter credencial do cofre (candidato a reuso)": step 4.
- "Fora do escopo aprovado (ADR-028)": comandos 5 e 6, não convertidos.

Valores que a extração não capturou (arquivo, intervalo, URL, corpo, autorização) são
`SET cfg_... TO $''''''` com `# TODO reflow` acima: preencher com o analista antes de
colar. Lista completa em `notas-conversao.md` → "Pendências antes de rodar no designer".

## Comandos fora do escopo aprovado (ADR-028)

`CustomPackage/transform` (`main.json:5`) e `Browser/unmappedAction`
(`main.json:6`) não têm ação PAD mapeada em `reference/a360-to-pad.md`
("sem equivalente" / "pendente de classificação") e estão explicitamente
fora do checkpoint aprovado (`ADR-028`, `docs/decisions.md`). Eles aparecem
em `Main.robin` apenas como `TODO reflow` dentro da Região "Fora do escopo
aprovado (ADR-028)", só para manter a sequência do processo legível —
requerem revisão humana e uma nova entrada na tabela verdade antes de
qualquer conversão futura.

## Teste

Nenhum teste foi executado no PAD ainda, e a fase `05-test/` deste projeto ainda não
existe. Antes de gerar `05-test/`, um analista precisa preencher as `cfg_` pendentes,
decidir a origem da credencial e rodar o flow no designer, promovendo as ações usadas
para `[validado PAD: rodou]` (ver `reference/robin-actions.md` → "Como promover uma
ação").
