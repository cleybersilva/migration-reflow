# Notas de conversão — uc-01-browser-rest

Ações Robin usadas em `Main.robin`, todas da whitelist
`reference/robin-actions.md`, com o id Robin real (ancorado na PAD Robin Action KB
vendorizada, ADR-029). Mapeamento de origem em `reference/a360-to-pad.md`. Nenhuma ação
abaixo está `[validado PAD: rodou]` ainda.

Reconvertido em 2026-11-04: a versão anterior não colava no PAD (comentários `//`,
linhas `cfg_x: "..."` e placeholders soltos derrubavam a colagem inteira) e usava nomes
que não existem no PAD (`Browser.LaunchNewBrowser`, `Web.InvokeRestApi`).

- `WebAutomation.LaunchEdge.LaunchEdge` — step_01_open_browser; equivalente a `Browser.open` (`main.json:1`); status `[colado KB: PAD 2.73, não rodado nesta instalação]`; depende da extensão do PAD no navegador do ambiente (alerta A1 em `02-docs/risks.md`); se o legado usar Chrome, trocar pelo irmão `WebAutomation.LaunchChrome.LaunchChrome`. URL vem da entrada `in_target_url` (valor não capturado pela extração).
- `Web.InvokeWebService.InvokeWebService` — step_02_call_rest_api; equivalente a `REST.get` (`main.json:2`) com `Method: Web.Method.Get`; status `[colado KB: PAD 2.73, não rodado nesta instalação]`; URL em `cfg_rest_endpoint_url`, não capturada pela extração; dúvida registrada em `02-docs/business-rules.md` sobre dependência (ou não) da sessão do navegador aberta no passo anterior.
- `Credentials.GetCredential` — step_03_get_credential; equivalente a `CredentialVault.getCredential` (`main.json:3`); status `[não validado]` (não é id Robin real; a KB não tem ação de cofre), por isso o passo é só `# TODO reflow`; usar só a referência ao cofre (`main.json:3:credential-vault`), nunca o valor bruto da credencial; exige plano de migração (alerta A4 em `02-docs/risks.md`).
- `**REGION` — organiza os três estágios do flow; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `SET` — configuração `cfg_` no topo; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
