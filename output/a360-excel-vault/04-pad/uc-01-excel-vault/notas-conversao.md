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

- `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess` — step_01_open_excel_file; equivalente a `Excel.open` (`main.json:1`); único passo `[validado PAD: rodou]` (confirmado pelo analista em 2026-10-30), usado na forma de colagem de uma linha da seção (ver ressalva em `robin-actions.md`); ressalva em `reference/a360-to-pad.md` sobre o `packageName` simples "Excel" (sem "avançado") deste projeto ainda não confirmado como o mesmo pacote AA360 validado.
- `Excel.ReadFromExcel.ReadCells` — step_02_read_excel_range; equivalente a `Excel.read` (`main.json:2`, atributo `range`); seletor de **intervalo** (`StartColumn`/`StartRow`/`EndColumn`/`EndRow`), que fecha a lacuna deixada pelo ADR-025; status `[colado KB: PAD 2.73, não rodado nesta instalação]`. Não usar `ReadCell` (célula única) nem `ReadAllCells` (planilha inteira), que não correspondem ao atributo `range`.
- `Web.InvokeWebService.InvokeWebServicePost` — step_03_post_data_to_rest_api; equivalente a `REST.post` (`main.json:3`, atributos `body` e `authorization`); status `[colado KB: PAD 2.73, não rodado nesta instalação]`; URL, corpo e cabeçalho de autorização não capturados pela extração (`02-docs/integrations.md`), por isso vêm de `cfg_` vazias com `# TODO reflow`.
- `Credentials.GetCredential` — step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre; equivalente a `CredentialVault.get` (`main.json:4`, atributo `credential`); status `[não validado]` (não é id Robin real; a KB não tem ação de cofre), por isso o passo é só `# TODO reflow`; usar só a referência ao cofre (`main.json:4:credential-vault`), nunca o valor bruto. **Subfluxo comum catalogado**: entrada `obter-credencial-do-cofre` em `reference/subfluxos-comuns.md`.
- `**REGION` — organiza os quatro estágios do flow ("Leitura da Base de Entrada", "Envio de Dados ao Sistema Externo (REST)", "Subfluxo comum: Obter credencial do cofre (candidato a reuso)", "Fora do escopo aprovado (ADR-028)"); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `SET` — configuração `cfg_` no topo; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.

## Fora da whitelist / fora do escopo (não citados acima de propósito)

`CustomPackage.transform` (`main.json:5`) e `Browser.unmappedAction`
(`main.json:6`) **não** foram convertidos e **não** têm entrada na whitelist
`reference/robin-actions.md` nem ação mapeada em `reference/a360-to-pad.md` (lá aparecem
como "pendente de classificação"). Estão fora do checkpoint aprovado (ADR-028) e
aparecem no `Main.robin` só como comentário dentro da Região "Fora do escopo aprovado
(ADR-028)".

## Subfluxo comum sinalizado

O **step_04** corresponde à entrada `obter-credencial-do-cofre`, catalogada (status
`catalogado`, evidência de 2 projetos) em `reference/subfluxos-comuns.md`. A própria
evidência observada ali já cita este projeto (`a360-excel-vault/input/main.json:4`).
Recomendação registrada no catálogo: extrair para um subflow compartilhado (ex.:
`Subflow_ObterCredencialDoCofre`) que recebe `cfg_credential_reference` e devolve a
credencial, em vez de repetir o passo isolado a cada conversão.

Não há dependência `TaskBot.run`/`CALL` neste projeto — `dependencies` está vazio em
`01-inventory/inventory.json:34` — então essa sinalização é exclusivamente do catálogo
de padrões repetidos entre processos.

## Pendências antes de rodar no designer

- **Credencial** (alerta A4 em `02-docs/risks.md`): decidir a origem real no PAD
  (variável de entrada sensível do flow ou `Cyberark.GetPassword.GetPassword`) e o plano
  de migração antes de montar `step_04`.
- **Valores não capturados** pela extração determinística (`01-inventory/inventory.json`,
  `02-docs/data-sources.md`, `02-docs/integrations.md`): `file` (`main.json:1`), `range`
  (`main.json:2`), URL, corpo e autorização de `REST.post` (`main.json:3`). Preencher
  `cfg_excel_input_folder`, `cfg_excel_file_name`, `cfg_excel_start_column`,
  `cfg_excel_start_row`, `cfg_excel_end_column`, `cfg_excel_end_row`,
  `cfg_rest_endpoint_url` e `cfg_rest_custom_headers` com o analista.
- **Ordem herdada do legado**: a credencial (`main.json:4`) vem depois do `REST/post`
  (`main.json:3`). Revisar com o analista se a autenticação do step_03 deveria usá-la.
- **Fechamento do Excel**: o legado não fecha a planilha; avaliar incluir
  `Excel.CloseExcel.Close` ao fim do flow.
- Tabela verdade (`reference/a360-to-pad.md`): as linhas "Excel | open" e "Excel | read" ainda têm a
  ressalva do `packageName` simples `Excel` (sem "avançado"); reavaliar com um export real.
- **A1** (`02-docs/risks.md`): `Browser/unmappedAction` (fora do escopo) pode depender
  de extensão de navegador específica, só relevante se entrar em escopo no futuro.
