# Notas de conversão — uc-01-browser-rest

Ações Robin usadas em `Main.robin`, todas da whitelist
`reference/robin-actions.md`. Mapeamento de origem em
`reference/a360-to-pad.md`. Nenhuma ação abaixo está `[validado PAD: rodou]`
ainda — todas seguem `[não validado]`, por isso o `Main.robin` cita `TODO
reflow` no lugar do snippet real.

- `Browser.LaunchNewBrowser` — step_01_open_browser; equivalente a `Browser.open` (`main.json:1`); depende da extensão de navegador do A360 no ambiente atual (alerta A1 em `02-docs/risks.md`), padronizar antes de montar no designer.
- `Web.InvokeRestApi` — step_02_call_rest_api; equivalente a `REST.get` (`main.json:2`); dúvida registrada em `02-docs/business-rules.md` sobre dependência (ou não) da sessão do navegador aberta no passo anterior.
- `Credentials.GetCredential` — step_03_get_credential; equivalente a `CredentialVault.getCredential` (`main.json:3`); usar só a referência ao cofre (`main.json:3:credential-vault`), nunca o valor bruto da credencial; exige plano de migração para o Credential Manager do PAD (alerta A4 em `02-docs/risks.md`) antes de montar no designer.
