# Notas de conversão — teste uc-01-browser-rest

Ações Robin usadas em `Main.robin` deste teste, todas da whitelist
`reference/robin-actions.md`. Mesma regra do conversor: nenhuma sintaxe
inventada; hoje todas estão `[não validado]`, então o texto do snippet é o
placeholder "TODO reflow" registrado na whitelist.

- `Browser.LaunchNewBrowser` — equivalente ao A360 `Browser.open`
  (`main.json:1`); usada em `step_01_open_browser` para os cenários CT-01 e
  CT-03 (abrir a página do sistema externo / simular URL inacessível).
  Status na whitelist: `[não validado]`.
- `Web.InvokeRestApi` — equivalente ao A360 `REST.get` (`main.json:2`);
  usada em `step_02_call_rest_api` para os cenários CT-01 e CT-04 (chamada
  ao serviço REST com sucesso / com erro HTTP). Status na whitelist:
  `[não validado]`.
- `Credentials.GetCredential` — equivalente ao A360
  `CredentialVault.getCredential` (`main.json:3`); usada em
  `step_03_get_credential` para os cenários CT-01 e CT-02 (obtenção da
  credencial do cofre / referência inexistente). Nunca copiar o valor bruto
  da credencial, só a referência ao cofre (`cfg_credential_reference`).
  Status na whitelist: `[não validado]`.
- `Variables.SetVariable` — não corresponde a nenhuma ação A360; usada em
  `step_04_record_test_result` apenas para o analista registrar
  manualmente o resultado observado de cada cenário depois da execução
  real no PAD (`out_test_result`). Status na whitelist: `[não validado]`.

Nenhuma outra ação do módulo `reference/robin-actions.md` foi usada neste
teste. `uv run python -m reflow lint-robin a360-browser-rest` deve cruzar
esta lista contra a whitelist e aprovar, já que todas as quatro ações acima
constam em `reference/robin-actions.md`.
