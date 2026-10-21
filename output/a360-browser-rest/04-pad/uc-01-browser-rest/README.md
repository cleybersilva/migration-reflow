# uc-01-browser-rest

Flow Robin convertido a partir do projeto A360 `a360-browser-rest`, escopo
**UC-01 apenas** — abertura de página no navegador, consulta REST e obtenção
de credencial no Credential Vault (`main.json:1`, `main.json:2`,
`main.json:3`, via `01-inventory/inventory.json` e `02-docs/use-cases.md`).

UC-02 (`TaskBot.run` → `Excel.read`, `main.json:4` / `child.json:1`) **não**
faz parte deste flow: ficou fora do escopo aprovado no checkpoint
(`output/a360-browser-rest/00-manifest.json` → `checkpoint`), conforme o
veredito `PARTIAL` em `output/a360-browser-rest/03-classification/classification.md`.

## Origem

- Projeto: `a360-browser-rest` (origem A360, `00-manifest.json`).
- Caso de uso: UC-01 — "Consulta a serviço externo via navegador e REST com
  credencial do cofre" (`02-docs/use-cases.md`).
- Checkpoint humano: aprovado em `2026-10-21T16:44:33+00:00`
  (`00-manifest.json` → `checkpoint.approved_at`), escopo restrito a UC-01.

## Passo a passo convertido

1. **step_01_open_browser** — abre a página no navegador (`main.json:1`,
   `Browser.open` → `Browser.LaunchNewBrowser`).
2. **step_02_call_rest_api** — consulta o serviço externo via REST
   (`main.json:2`, `REST.get` → `Web.InvokeRestApi`).
3. **step_03_get_credential** — obtém a credencial no Credential Vault
   (`main.json:3`, `CredentialVault.getCredential` → `Credentials.GetCredential`),
   nunca o valor bruto — só a referência ao cofre
   (`main.json:3:credential-vault`).

Todas as três ações estão hoje com status `[não validado]` em
`reference/robin-actions.md` e `reference/a360-to-pad.md`; por isso o
`Main.robin` cita `TODO reflow` nos trechos onde entraria o snippet real
copiado do designer do Power Automate Desktop. Nenhuma sintaxe Robin foi
inventada.

## Pendências antes de rodar no designer

- **A1** (`02-docs/risks.md`): `Browser.open` depende de extensão de
  navegador própria do A360; padronizar o ambiente do analista (ou o
  equivalente no PAD) antes de montar `step_01_open_browser`.
- **A4** (`02-docs/risks.md`): `CredentialVault.getCredential` precisa de um
  plano de migração da credencial para o Credential Manager do PAD antes de
  montar `step_03_get_credential`.
- Valor de `in_target_url` (atributo `url` de `main.json:1`) não foi
  capturado pela extração determinística (`01-inventory/inventory.json`
  registra só o nome do atributo); confirmar com um analista antes de
  preencher.
- Dúvida registrada em `02-docs/business-rules.md` e
  `03-classification/classification.md`: não há evidência de que
  `REST.get` (`main.json:2`) dependa da sessão aberta no navegador
  (`main.json:1`), nem de que seja independente dela. Se um analista
  confirmar que a chamada REST funciona sem o navegador, este caso de uso
  deve ser reavaliado para `NOT_PAD`.

## Teste

Nenhum teste foi executado no PAD ainda (nenhuma das três ações passou de
`[não validado]` para `[validado PAD: rodou]`). A fase `05-test/` deste
projeto, se existir, deve ser regerada depois que este `Main.robin` receber
os snippets reais — ver `reference/robin-actions.md` → "Como promover uma
ação para `[validado PAD: rodou]`".
