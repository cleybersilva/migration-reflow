# Notas de conversão — teste uc-01-browser-rest

Ações Robin usadas em `Main.robin` deste teste, todas da whitelist
`reference/robin-actions.md`, com o id Robin real (ADR-029). Mesma regra do conversor:
nenhuma sintaxe inventada. Reconvertido em 2026-11-04 junto com o flow principal.

- `WebAutomation.LaunchEdge.LaunchEdge` — equivalente ao A360 `Browser.open`
  (`main.json:1`); usada em `step_01_open_browser` para os cenários CT-01 e CT-03
  (abrir a página do sistema externo / simular URL inacessível). Status na whitelist:
  `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Web.InvokeWebService.InvokeWebService` — equivalente ao A360 `REST.get`
  (`main.json:2`), `Method: Web.Method.Get`; usada em `step_02_call_rest_api` para os
  cenários CT-01 e CT-04 (chamada com sucesso / com erro HTTP). Status na whitelist:
  `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Credentials.GetCredential` — equivalente ao A360 `CredentialVault.getCredential`
  (`main.json:3`); cenários CT-01 e CT-02; segue `# TODO reflow`, porque o status na
  whitelist é `[não validado]` (não é id Robin real). Nunca copiar o valor bruto da
  credencial, só a referência ao cofre (`cfg_credential_reference`).
- `SET` — configuração `cfg_` e `step_04_record_test_result` (`out_test_result`, vazio
  até a execução real no PAD). Status na whitelist: `[colado KB: PAD 2.73, não rodado
  nesta instalação]`.
- `**REGION` — um bloco por grupo de cenários. Status na whitelist: `[colado KB: PAD
  2.73, não rodado nesta instalação]`.
