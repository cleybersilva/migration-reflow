# Notas de conversão — uc-01-excel-vault

Ações Robin usadas em `Main.robin`, todas da whitelist
`reference/robin-actions.md`. Mapeamento de origem em
`reference/a360-to-pad.md`. Escopo restrito à parte confirmada do fluxo,
aprovada no checkpoint (ADR-028, `docs/decisions.md`): `Excel/open`,
`Excel/read`, `REST/post`, `CredentialVault/get`.

- `Excel.LaunchExcel` — step_01_open_excel_file; equivalente a `Excel.open` (`main.json:1`); único passo com status `[validado PAD: rodou]` nesta conversão (variante `LaunchAndOpenUnderExistingProcess`, confirmada pelo analista em 2026-10-30); ressalva registrada em `reference/a360-to-pad.md` sobre o `packageName` simples "Excel" (sem "avançado") deste projeto ainda não estar confirmado como o mesmo pacote AA360 validado.
- `Excel.ReadFromWorksheet` — step_02_read_excel_range; equivalente a `Excel.read` (`main.json:2`, atributo `range`); variante usada é "intervalo específico" (`Start column`/`Start row`/`End column`/`End row`), com status `[não validado]` em `reference/robin-actions.md` — por isso o `Main.robin` cita `TODO reflow` no lugar do snippet real; não usar a variante `ReadCell` (validada só para célula única) nem `ReadAllCells` (proposto, só para planilha inteira), porque nenhuma das duas corresponde ao atributo `range` deste passo.
- `Web.InvokeRestApi` — step_03_post_data_to_rest_api; equivalente a `REST.post` (`main.json:3`, atributos `body` e `authorization`); status `[não validado]` — `TODO reflow` no lugar do snippet real; URL do sistema externo não capturada pela extração (`02-docs/integrations.md`).
- `Credentials.GetCredential` — step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre; equivalente a `CredentialVault.get` (`main.json:4`, atributo `credential`); status `[não validado]` — `TODO reflow` no lugar do snippet real; usar só a referência ao cofre (`main.json:4:credential-vault`), nunca o valor bruto da credencial; exige plano de migração para o Credential Manager do PAD (alerta A4 em `02-docs/risks.md`) antes de montar no designer. **Subfluxo comum catalogado**: corresponde à entrada `obter-credencial-do-cofre` em `reference/subfluxos-comuns.md` (status `catalogado`, evidência de 2 projetos — a própria entrada cita `a360-excel-vault/input/main.json:4` como uma das duas evidências); recomendação de reuso via subflow compartilhado (`Subflow_ObterCredencialDoCofre`), nunca remontar `Credentials.GetCredential` isolado a cada conversão.
- `FlowControl.Region` — organiza os quatro estágios do flow ("Leitura da Base de Entrada", "Envio de Dados ao Sistema Externo (REST)", "Subfluxo comum: Obter credencial do cofre (candidato a reuso)", "Fora do escopo aprovado (ADR-028)"); status `[não validado]` em `reference/robin-actions.md` — toda abertura/fechamento de Região no `Main.robin` é, por isso, `TODO reflow`, nunca sintaxe de Região inventada.

## Fora da whitelist / fora do escopo (não citados acima de propósito)

`CustomPackage.transform` (`main.json:5`) e `Browser.unmappedAction`
(`main.json:6`) **não** foram convertidos e **não** têm entrada na
whitelist `reference/robin-actions.md` nem ação mapeada em
`reference/a360-to-pad.md` (lá aparecem como "sem equivalente" / "pendente
de classificação"). Por isso nenhum dos dois é citado como item de lista
acima — citar um nome de ação que não existe na whitelist reprovaria o
`lint-robin`. Eles ficaram explicitamente fora do escopo aprovado no
checkpoint, conforme **ADR-028** (`docs/decisions.md`), e aparecem em
`Main.robin` só como comentário/`TODO reflow` dentro da Região "Fora do
escopo aprovado (ADR-028)", para manter a sequência do processo legível —
nunca como se fossem ação convertida.

## Candidato a novo subfluxo comum

Nenhum identificado nesta conversão além do já catalogado
(`obter-credencial-do-cofre`, citado acima). As duas outras entradas de
`reference/subfluxos-comuns.md` (`tratamento_erro_padrao`,
`notificacao_de_falha_por_email`) seguem `proposto`, sem evidência, e não
se aplicam a este flow (não há bloco de tratamento de erro nem notificação
por e-mail em `01-inventory/inventory.json`).

## Execução das ferramentas de lint/normalização

O agent de conversão não tinha ferramenta de shell disponível na própria
sessão, então gerou `Main.robin` com quebra de linha LF. Rodados depois,
pela orquestração: `uv run python -m reflow fix-robin-eol a360-excel-vault`
(normalizou `Main.robin` para CRLF, exigido pelo PAD) e
`uv run python -m reflow lint-robin a360-excel-vault` → **ok, nenhum
`.robin` pendente de validação**. Os três artefatos (`Main.robin`,
`README.md`, `notas-conversao.md`) estão confirmados.
