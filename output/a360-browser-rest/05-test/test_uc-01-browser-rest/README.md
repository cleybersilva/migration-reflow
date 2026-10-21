# uc-01-browser-rest — teste

Roteiro de teste do flow convertido em
`output/a360-browser-rest/04-pad/uc-01-browser-rest/Main.robin`, cobrindo
UC-01 (`02-docs/use-cases.md`): abertura de navegador, chamada REST e
obtenção de credencial do cofre (`main.json:1-3`,
`01-inventory/inventory.json`).

UC-02 (bot filho / leitura de Excel) não faz parte deste flow nem deste
teste — verdict `PARTIAL` em
`output/a360-browser-rest/03-classification/classification.md` — e fica
fora de escopo aqui.

> `02-docs/business-rules.md` registra que a extração não encontrou nenhuma
> condição ou ramificação explícita neste projeto (`unknown_commands` e
> `warnings` vazios em `01-inventory/inventory.json`); por isso os cenários
> abaixo cobrem o caminho feliz da sequência linear documentada e os modos
> de falha óbvios de cada ação (navegador, REST, credencial), sem inventar
> regra de negócio que não tem evidência `arquivo:linha`.

Este README descreve cenários a executar; **nenhum deles foi rodado**. O
`Main.robin` ao lado tem todas as ações ainda `[não validado]` (ver
`notas-conversao.md`), então o roteiro só vira teste de verdade depois que
um analista monta cada ação no designer do PAD, cola o texto real no lugar
do placeholder e executa o flow (ver `docs/runbook.md`).

## Cenários

### CT-01 — Caminho feliz: navegador abre, REST responde e credencial é obtida

- **Passos:**
  1. Executar `step_01_open_browser` com `in_target_url` apontando para o
     endereço do sistema externo (origem `Browser.open`, `main.json:1`).
  2. Executar `step_02_call_rest_api` contra o serviço REST (origem
     `REST.get`, `main.json:2`).
  3. Executar `step_03_get_credential` buscando a credencial em
     `cfg_credential_reference` (origem `CredentialVault.getCredential`,
     `main.json:3`).
- **Dado de entrada:** `in_target_url` com uma URL válida e acessível do
  sistema externo; endpoint REST disponível; referência de credencial
  (`cfg_credential_reference`) existente no cofre do PAD.
- **Resultado esperado:** navegador abre a página sem erro; `Web.InvokeRestApi`
  retorna status HTTP 2xx com corpo preenchido em `out_rest_response`;
  `Credentials.GetCredential` retorna a credencial (sem expor o valor bruto
  em nenhum log) em `out_credential`, conforme objetivo de negócio descrito
  em UC-01 (`02-docs/use-cases.md`).

### CT-02 — Referência de credencial inexistente no cofre do PAD

- **Passos:**
  1. Executar `step_03_get_credential` com `cfg_credential_reference`
     apontando para uma referência que não existe no Credential Manager do
     PAD.
- **Dado de entrada:** `cfg_credential_reference` com um nome de credencial
  inválido/não cadastrado (ex.: `"main.json:3:credential-vault-inexistente"`).
- **Resultado esperado:** `Credentials.GetCredential` falha com erro de
  credencial não encontrada; o flow não deve seguir expondo nenhum valor
  bruto de credencial em `out_credential` nem em log, conforme a observação
  de segurança da tabela verdade (`reference/a360-to-pad.md` —
  "CredentialVault | getCredential", "nunca copiar o valor bruto, só a
  referência ao cofre").

### CT-03 — URL do navegador inacessível (timeout/erro de rede)

- **Passos:**
  1. Executar `step_01_open_browser` com `in_target_url` apontando para um
     endereço inválido ou indisponível.
- **Dado de entrada:** `in_target_url` com uma URL inexistente ou um host
  fora do ar (ex.: `"https://host-invalido.exemplo.invalido"`).
- **Resultado esperado:** `Browser.LaunchNewBrowser` encerra com erro de
  navegação (timeout ou falha de resolução de endereço); os passos
  seguintes (`step_02_call_rest_api`, `step_03_get_credential`) não devem
  ser executados com dado parcial/corrompido.

### CT-04 — Serviço REST retorna erro (4xx/5xx)

- **Passos:**
  1. Executar `step_01_open_browser` normalmente (pré-condição satisfeita).
  2. Executar `step_02_call_rest_api` contra um endpoint que responde com
     erro.
- **Dado de entrada:** endpoint REST configurado para devolver status 4xx
  ou 5xx (ex.: `404` ou `500`) para a chamada de `main.json:2`.
- **Resultado esperado:** `Web.InvokeRestApi` reporta o erro HTTP recebido;
  `out_rest_response` não deve conter dado de negócio como se a chamada
  tivesse tido sucesso — o flow deve sinalizar falha de forma visível ao
  analista, em vez de seguir como se o resultado esperado em UC-01
  (`02-docs/use-cases.md`, "Resultado esperado") tivesse sido alcançado.

## Tabela de resultados

| Cenário | Passos | Dado de entrada | Resultado esperado | Status |
| --- | --- | --- | --- | --- |
| CT-01 | step_01 → step_02 → step_03 | URL válida, endpoint REST OK, credencial cadastrada | Navegador abre; REST responde 2xx em `out_rest_response`; credencial obtida em `out_credential` sem expor valor bruto | (a executar no PAD) |
| CT-02 | step_03 | `cfg_credential_reference` inválida/não cadastrada | `Credentials.GetCredential` falha com erro de credencial não encontrada; nenhum valor bruto exposto | (a executar no PAD) |
| CT-03 | step_01 | `in_target_url` inválida/host fora do ar | `Browser.LaunchNewBrowser` falha com erro de navegação; passos seguintes não executam | (a executar no PAD) |
| CT-04 | step_01 → step_02 | Endpoint REST retornando 4xx/5xx | `Web.InvokeRestApi` reporta erro HTTP; flow sinaliza falha, sem tratar como sucesso | (a executar no PAD) |

A coluna **Status** só é preenchida com `passou`/`falhou` + evidência depois
que um analista colar o `Main.robin` deste teste no designer do PAD e
executar cada cenário de verdade (ver `docs/runbook.md`). Nunca escrever
`PASS`/`FAIL` nesta tabela a partir deste documento.
