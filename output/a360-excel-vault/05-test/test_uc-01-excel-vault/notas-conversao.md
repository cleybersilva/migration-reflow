# Notas de conversão — teste uc-01-excel-vault

Ações Robin usadas em `Main.robin` deste teste, todas da whitelist
`reference/robin-actions.md`, com o id Robin real (ADR-029). Mesma regra do conversor:
nenhuma sintaxe inventada, snippets copiados com só os valores trocados, as mesmas linhas
de ação do flow principal (`04-pad/uc-01-excel-vault/Main.robin`). Gerado em 2026-11-05,
não executado no PAD.

- `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess` — equivalente ao A360 `Excel/open` (`main.json:1`); `step_01_open_excel_file`, cenários CT-01, CT-04 (arquivo inexistente, erro `OpenDocumentError` da KB) e CT-05; ação `[validado PAD: rodou]` no snippet multilinha do analista, forma de uma linha `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Excel.ReadFromExcel.ReadCells` — equivalente ao A360 `Excel/read` (`main.json:2`); `step_02_read_excel_range`, cenários CT-01 e CT-05 (intervalo inválido, erro `ReadCellsError` da KB); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Excel.CloseExcel.Close` — sem origem no legado (diferença deliberada do flow principal, R8-1); `step_02b_close_excel_instance`, cenário CT-01; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Web.InvokeWebService.InvokeWebServicePost` — equivalente ao A360 `REST/post` (`main.json:3`); `step_03_post_data_to_rest_api`, cenários CT-01, CT-02 (401) e CT-03 (corpo inesperado); `FailOnErrorStatus: False` mantido igual ao flow principal, por isso o status é conferido em `out_rest_status_code`; token só via entrada sensível `in_rest_token`; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `SET` — configuração `cfg_` no topo e `step_05_record_test_result` (`out_test_result`, vazio até a execução real no PAD); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `**REGION` — um bloco por estágio do flow, com os cenários que ele verifica no rótulo; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.

O passo da credencial (origem `CredentialVault/get`, `main.json:4`) não tem ação: por
decisão do analista (2026-11-05) a credencial chega pela entrada sensível `in_rest_token`,
declarada no designer. Nenhuma ação de cofre é usada neste teste.

Entrada a declarar no designer: `in_rest_token` (texto, sensível).
