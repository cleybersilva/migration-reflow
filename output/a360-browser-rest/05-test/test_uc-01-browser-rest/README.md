# uc-01-browser-rest — teste

Roteiro de teste do flow convertido em
`output/a360-browser-rest/04-pad/uc-01-browser-rest/Main.robin` (versão de 2026-11-05,
auditada em `04-pad/uc-01-browser-rest/review.md`, rodada 3), cobrindo UC-01
(`02-docs/use-cases.md:9-20`): abrir a página do sistema externo no navegador, chamar o
serviço REST autenticado com a credencial que no legado vinha do Credential Vault (no
flow PAD, a entrada sensível `in_rest_token`) e fechar o navegador ao fim.

**Este teste foi gerado, não executado.** Nenhum cenário abaixo foi rodado no PAD. As
ações do `Main.robin` ao lado estão `[colado KB: PAD 2.73, não rodado nesta instalação]`
(ver `notas-conversao.md`); o resultado real só existe depois que um analista colar o
flow no designer do PAD e executar cada cenário (ver `docs/runbook.md`).

Regenerado em 2026-11-05 por completo: a versão anterior citava ids que não existem no
PAD, esperava uma ação de cofre que o flow não usa e uma falha sinalizada para 4xx/5xx
que o flow não produz.

## Escopo

- Dentro: `main.json:1-3` (checkpoint de 2026-10-21, `00-manifest.json:2-7`):
  `Browser.open` (step_01), `CredentialVault.getCredential` (step_03, substituído pela
  entrada sensível `in_rest_token`, decisão do analista de 2026-11-05) e `REST.get`
  (step_02), mais o fechamento do navegador (step_05, sem origem no legado, R8-1).
- Fora: UC-02 (`TaskBot.run` em `main.json:4`, leitura Excel em `child.json:1`), verdict
  `PARTIAL` em `03-classification/classification.md`.
- `02-docs/business-rules.md:8-22` não registra nenhuma condicional. Os cenários cobrem
  o caminho feliz da sequência linear e os pontos apontados pela auditoria (I-2 e R8-3
  em `review.md`), sem inventar regra de negócio sem evidência `arquivo:linha`.
- Ordem de execução: step_01, step_03 (só documentação), step_02, step_05,
  step_06_record_test_result (só deste teste). A numeração segue a ordem do legado
  (regra do R3-1 do piloto `a360-excel-vault`).
- Linhas de ação idênticas às do flow principal (mesmos ids, argumentos e saídas).

## Pré-requisitos (todos os cenários)

1. Rodar `uv run python -m reflow fix-robin-eol a360-browser-rest` e
   `uv run python -m reflow lint-robin a360-browser-rest` sem achados.
2. No designer, criar as variáveis de **entrada**:
   - `in_target_url`: tipo texto. URL da página do sistema externo (valor não capturado
     pela extração, `01-inventory/inventory.json:56-66`), informada na execução.
   - `in_rest_token`: tipo texto, marcada como **sensível**. O valor é informado só na
     hora da execução, nunca no `Main.robin`, neste README ou na evidência.
3. Preencher as `cfg_` do topo do `Main.robin` com o analista (valores não capturados,
   `01-inventory/inventory.json:42-51`, `02-docs/integrations.md`):
   `cfg_rest_endpoint_url` (homologação), `cfg_rest_accept` e `cfg_rest_content_type`
   (formato confirmado, sem assumir JSON, R7-1), `cfg_rest_auth_prefix` (esquema já
   seguido de um espaço, ou vazia para token puro, R1-1), e `cfg_test_case_id` com o id
   do cenário.
4. Confirmar o navegador do legado (alerta A1 em `02-docs/risks.md`) e a extensão do PAD
   instalada nele. Se for Chrome, trocar o step_01 pelo irmão
   `WebAutomation.LaunchChrome.LaunchChrome` (mesmos argumentos) aqui e no flow
   principal.
5. Endpoint de destino em **homologação**, nunca produção. Para CT-01 e CT-02, ter como
   ver o cabeçalho de autorização que chegou ao destino (log de requisições do destino
   de homologação ou endpoint de eco de homologação) e usar um token de teste
   descartável, nunca uma credencial real, porque o valor do cabeçalho fica visível
   nessa conferência.
6. Decidir antes, com o analista, o critério de status HTTP (R8-3): que faixa conta como
   sucesso e se fora dela o flow deveria interromper ou só registrar. Enquanto R8-3
   estiver aberto, o flow não sinaliza falha HTTP e este teste não espera isso.
7. Evidências (print, status, trecho da resposta sem dado sensível) salvas só em
   `C:\Users\Public\Documents\`.

Atenção: o step_02 usa `FailOnErrorStatus: False`. Uma resposta 4xx/5xx **não**
interrompe o flow; ele termina sem erro de ação mesmo sem ter autenticado. Em todo
cenário que chega ao step_02, o analista confere `out_rest_status_code`,
`out_rest_response` e `out_rest_response_headers` no painel de variáveis.

Sobre o cabeçalho (I-2 do `review.md`): o step_02 monta o valor do cabeçalho de
autorização com duas expressões coladas, `%cfg_rest_auth_prefix%` seguida de
`%in_rest_token%`, sem espaço entre elas. Com prefixo preenchido, o valor efetivo deve
ser o esquema, exatamente um espaço e o token. Com prefixo vazio, deve ser só o token,
sem espaço no início. Esse padrão passou no lint, mas nunca rodou no PAD.

## Cenários

### CT-01: Caminho feliz com prefixo preenchido

- **Passos:**
  1. Executar o flow inteiro: `step_01_open_browser` (origem `Browser.open`,
     `main.json:1`) abre `in_target_url`.
  2. `step_03_get_credential_subfluxo_comum_obter_credencial_do_cofre` não executa ação:
     o token vem de `in_rest_token` (origem `CredentialVault.getCredential`,
     `main.json:3`).
  3. `step_02_call_rest_api` (origem `REST.get`, `main.json:2`) chama
     `cfg_rest_endpoint_url` com o cabeçalho de autorização.
  4. `step_05_close_browser` fecha o navegador aberto no step_01.
  5. Conferir o cabeçalho recebido no destino, as variáveis de saída e o Gerenciador de
     Tarefas.
- **Dado de entrada:** `in_target_url` válida e acessível; `cfg_rest_endpoint_url` de
  homologação acessível; `cfg_rest_accept`/`cfg_rest_content_type` no formato
  confirmado; `cfg_rest_auth_prefix` com o esquema confirmado seguido de um espaço;
  `in_rest_token` com token de teste válido de homologação.
- **Resultado esperado:** o navegador confirmado em A1 abre `in_target_url` sem erro (a
  página não é lida por nenhum passo, R1-2); o cabeçalho de autorização que chega ao
  destino é o esquema, um único espaço e o token, sem espaço duplo nem no fim;
  `out_rest_status_code` igual ao status de sucesso definido pelo analista (R8-3);
  `out_rest_response` com os dados do serviço, prontos para uso (UC-01,
  `02-docs/use-cases.md:19-20`); ao fim, nenhuma janela nem processo do navegador
  aberto pelo step_01 sobra; o valor de `in_rest_token` não aparece em
  `out_rest_response`, `out_rest_response_headers`, log do PAD nem evidência.
- **Resultado observado (analista):**

### CT-02: Prefixo vazio, token puro no cabeçalho

- **Passos:**
  1. Executar o flow inteiro como em CT-01, com `cfg_rest_auth_prefix` vazia.
  2. Conferir o cabeçalho recebido no destino e `out_rest_status_code`.
- **Dado de entrada:** igual a CT-01, exceto `cfg_rest_auth_prefix` = `$''''''` (como
  está hoje no flow principal).
- **Resultado esperado:** o cabeçalho de autorização que chega ao destino é só o token,
  sem espaço no início e sem esquema; o step_02 **não** falha com erro de ação. Se o
  destino aceita token puro, `out_rest_status_code` igual ao status de sucesso definido
  pelo analista; se exige esquema, o status de autenticação negada que o destino
  documentar (ex.: 401) aparece em `out_rest_status_code` e o flow termina sem erro de
  ação (`FailOnErrorStatus: False`, R8-3 aberto). Nos dois casos o step_05 fecha o
  navegador. Registrar qual dos dois casos ocorreu: isso fecha a pendência do prefixo
  (R1-1).
- **Resultado observado (analista):**

### CT-03: Token vazio ou errado

- **Passos:**
  1. Executar o flow inteiro como em CT-01, duas vezes, uma para cada variação.
  2. Conferir se o step_02 falhou com erro de ação ou devolveu status, e se o step_05
     executou.
- **Dado de entrada:** igual a CT-01 (prefixo preenchido), exceto `in_rest_token`: (a)
  vazia; (b) com um token inválido ou expirado de homologação.
- **Resultado esperado:**
  - (a) Token vazio: o cabeçalho fica só com o prefixo (ou vazio, se o prefixo também
    estiver vazio). Um de dois comportamentos, a registrar: o step_02 falha com
    `InvalidCustomHeaderError` (declarado na KB), o flow para ali sem tratamento e o
    step_05 não executa (conferir e registrar se o navegador ficou aberto); ou a chamada
    sai e o status de autenticação negada aparece em `out_rest_status_code`, com o flow
    terminando sem erro de ação e o step_05 fechando o navegador.
  - (b) Token errado: o status de autenticação negada que o destino documentar (ex.:
    401) aparece em `out_rest_status_code`; o flow **termina sem erro de ação**
    (`FailOnErrorStatus: False`), o que confirma que a falha hoje só é visível pela
    variável de status (R8-3); o step_05 fecha o navegador.
  - Nos dois casos, nenhum valor de token em `out_rest_response`,
    `out_rest_response_headers`, log nem evidência.
- **Resultado observado (analista):**

### CT-04: Serviço REST responde 4xx/5xx

- **Passos:**
  1. Executar o flow inteiro como em CT-01, com um endpoint que responde erro.
  2. Conferir `out_rest_status_code` e `out_rest_response`, e se o step_05 executou.
- **Dado de entrada:** igual a CT-01, exceto `cfg_rest_endpoint_url` apontando para um
  recurso inexistente do mesmo destino de homologação (resposta 4xx, ex.: 404) e, se o
  destino oferecer, para um recurso que responde 5xx.
- **Resultado esperado:** o status recebido aparece em `out_rest_status_code` (ex.: 404
  ou 500), com a mensagem do destino em `out_rest_response`; o step_02 **não** falha com
  erro de ação e o flow termina normalmente (`FailOnErrorStatus: False`); o step_05
  fecha o navegador. Enquanto R8-3 estiver aberto, nenhuma falha sinalizada é esperada:
  se o analista considerar que esse status deveria interromper o flow, registrar como
  insumo para a decisão de R8-3, não como defeito deste teste.
- **Resultado observado (analista):**

### CT-05: URL de destino do navegador inválida

- **Passos:**
  1. Executar o flow inteiro com `in_target_url` inválida.
  2. Conferir em que passo o flow parou e se alguma chamada chegou ao destino REST.
- **Dado de entrada:** `in_target_url` com uma URL mal formada (ex.: texto sem esquema,
  `nao-e-uma-url`) e, numa segunda rodada, com um host inexistente do domínio reservado
  `.invalid`; demais `cfg_` e `in_rest_token` como em CT-01.
- **Resultado esperado:** o step_01 falha com erro declarado na KB (`InvalidUrlError`
  para a URL mal formada; `LaunchEdgeError` ou página de erro de navegação para o host
  inexistente, a registrar qual); como o flow não tem tratamento de erro, ele para no
  step_01: o step_02 e o step_05 não executam e **nenhuma** chamada chega ao destino
  REST. Se o navegador chegou a abrir com página de erro e o flow seguiu, registrar esse
  comportamento (nesse caso o step_02 e o step_05 executam como em CT-01).
- **Resultado observado (analista):**

## Tabela de resultados

| Cenário | Passos | Dado de entrada | Resultado esperado | Resultado observado | Status |
| --- | --- | --- | --- | --- | --- |
| CT-01 | step_01 → step_03 (doc) → step_02 → step_05 | URL e endpoint válidos, prefixo preenchido, token de teste válido | Navegador abre e fecha; cabeçalho = esquema, um espaço, token; `out_rest_status_code` = sucesso definido (R8-3); token não exposto | | (a executar no PAD) |
| CT-02 | step_01 → step_03 (doc) → step_02 → step_05 | Igual a CT-01, `cfg_rest_auth_prefix` vazia | Cabeçalho = só o token, sem espaço inicial; sucesso ou negação em `out_rest_status_code`, sem erro de ação; navegador fechado | | (a executar no PAD) |
| CT-03 | step_01 → step_03 (doc) → step_02 → step_05 | (a) `in_rest_token` vazia; (b) token errado | (a) `InvalidCustomHeaderError` ou negação no status, registrar qual; (b) negação em `out_rest_status_code`, sem erro de ação; token não exposto | | (a executar no PAD) |
| CT-04 | step_01 → step_03 (doc) → step_02 → step_05 | Endpoint que responde 4xx/5xx | Status em `out_rest_status_code`, sem erro de ação nem falha sinalizada (R8-3 aberto); navegador fechado | | (a executar no PAD) |
| CT-05 | step_01 | `in_target_url` mal formada ou host inexistente | `InvalidUrlError`/`LaunchEdgeError`; step_02 e step_05 não executam; nenhuma chamada REST | | (a executar no PAD) |

As colunas **Resultado observado** e **Status** ficam vazias até a execução real. Só o
analista as preenche (`passou`/`falhou` + evidência em `C:\Users\Public\Documents\`),
depois de colar o `Main.robin` deste teste no designer do PAD e rodar cada cenário de
verdade (ver `docs/runbook.md`). Este documento nunca marca cenário como aprovado.
