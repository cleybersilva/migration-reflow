# Notas de conversão — teste uc-01-browser-rest

Ações Robin usadas em `Main.robin` deste teste, todas da whitelist
`reference/robin-actions.md`, com o id Robin real (ADR-029). Mesma regra do conversor:
nenhuma sintaxe inventada, snippets copiados com só os valores trocados, e as mesmas
linhas de ação do flow principal (`04-pad/uc-01-browser-rest/Main.robin`, versão de
2026-11-05, `review.md` rodada 3). Regenerado em 2026-11-05 por completo; gerado, não
executado no PAD.

- `WebAutomation.LaunchEdge.LaunchEdge` — equivalente ao A360 `Browser.open` (`main.json:1`); `step_01_open_browser`, cenários CT-01 a CT-04 (abre `in_target_url`) e CT-05 (URL inválida, erros `InvalidUrlError`/`LaunchEdgeError` declarados na KB); linha idêntica à do flow principal; troca pelo irmão Chrome pendente de A1 (`02-docs/risks.md`); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `Web.InvokeWebService.InvokeWebService` — equivalente ao A360 `REST.get` (`main.json:2`) com `Method: Web.Method.Get`; `step_02_call_rest_api`, cenários CT-01 a CT-04; linha idêntica à do flow principal, com `CustomHeaders` juntando `cfg_rest_auth_prefix` e `in_rest_token` sem espaço entre as duas expressões (I-2 do review, coberto por CT-01, CT-02 e CT-03); `FailOnErrorStatus: False` mantido, por isso 4xx/5xx são conferidos em `out_rest_status_code` e nenhum cenário espera falha sinalizada enquanto R8-3 estiver aberto; token vazio pode gerar `InvalidCustomHeaderError` (declarado na KB); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `WebAutomation.CloseWebBrowser` — sem origem no legado (diferença deliberada do flow principal, R8-1); `step_05_close_browser`, cenários CT-01 a CT-04 (navegador fechado ao fim); não executa em CT-05 nem quando o step_02 falha com erro de ação; consome `out_browser`; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `SET` — configuração `cfg_` no topo (as quatro do flow principal mais `cfg_test_case_id`) e `step_06_record_test_result` (`out_test_result`, vazio até a execução real no PAD); status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `**REGION` — um bloco por estágio do flow, na mesma ordem do flow principal, com os cenários que ele verifica no rótulo, mais "Registro do Resultado"; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.

O passo da credencial (origem `CredentialVault.getCredential`, `main.json:3`) não tem
ação: por decisão do analista (2026-11-05, R1-1) a credencial chega pela entrada
sensível `in_rest_token`, declarada no designer. Nenhuma ação de cofre é usada neste
teste; a seção `[não validado]` de credenciais da whitelist não é usada.

A Região "Fora do escopo aprovado (UC-02)" do flow principal não é repetida aqui: ela só
tem comentários e UC-02 não é testado (verdict `PARTIAL`).

O passo de registro do resultado é step_06: step_01 a step_04 são números do legado e
step_05 é o fechamento do navegador do flow principal; passo sem origem no legado recebe
o próximo número livre (regra do R3-1 do piloto `a360-excel-vault`).

Entradas a declarar no designer: `in_target_url` (texto) e `in_rest_token` (texto,
sensível).
