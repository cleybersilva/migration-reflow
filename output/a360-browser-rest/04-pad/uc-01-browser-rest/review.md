# Auditoria semântica: uc-01-browser-rest

<!--
Gerado pelo agent reflow-robin-reviewer em 2026-11-05, sobre o Main.robin
reconvertido em 2026-11-04 (ADR-029, KB Robin vendorizada; commit 3c7c10b).
Substitui a auditoria de 2026-10-21, que avaliava a versão antiga (ids
inexistentes `Browser.LaunchNewBrowser`/`Web.InvokeRestApi`, placeholders que
derrubavam a colagem) e não se aplica mais.

Pré-condições (verificadas pelo chamador): `lint-robin --all`, `reflow scan` e
`kb verify` sem achados. Esta auditoria cobre o que o lint não cobre: se o flow
que cola faz o que o legado fazia.

Baseline de escopo (não é achado): só UC-01 (main.json:1-3), checkpoint de
2026-10-21 (00-manifest.json:2-7). UC-02 (TaskBot.run -> Excel.read) fora, por
verdict PARTIAL.

Critério (o mesmo da auditoria de a360-excel-vault): decisão do analista e
`cfg_` vazia com `# TODO reflow` explícito são pendências legítimas do humano,
não achados bloqueantes de conversão.

Conteúdo de input/ é dado, nunca instrução. input/a360-browser-rest/main.json e
child.json foram lidos só como evidência estrutural: contêm apenas nós
packageName/commandName/attributes com valores sintéticos; nenhuma instrução
dirigida a agentes (nenhuma tentativa de prompt injection).
-->

## Resumo

| Categoria | Achados | Severidade |
| --- | --- | --- |
| 1. Cobertura de caso de uso | 1 (R1-1) | médio, decisão do analista |
| 2. Densidade de `TODO reflow` | 0 | informativo |
| 3. Nomenclatura | 0 (sufixo ausente tratado em R5-1) | |
| 4. Consistência notas × Main.robin (e README) | 2 (R4-1, R4-2) | menor |
| 5. Sinalização de subfluxo comum | 1 (R5-1) | médio |
| 6. Subflow padrão por nome de bot | 0 | não aplicável |
| 7. Ação `proposto`/`colado KB` | 1 (R7-1) | menor, decisão do analista |
| 8. Semântica contra a KB | 3 (R8-1, R8-2, R8-3) | 2 médios (R8-2 com decisão), 1 menor com decisão |
| **Total** | **8** | nenhum bloqueante de colagem; 4 médios |

## 1. Cobertura de caso de uso

Os 3 fatos de UC-01 (`02-docs/use-cases.md:16-18`: main.json:1, :2, :3) têm
passo correspondente, na ordem do inventário: step_01_open_browser
(Main.robin:47), step_02_call_rest_api (:62) e step_03_get_credential
(:65-79, só comentário por ação `[não validado]`). `business-rules.md:8-22` não
tem condicional: nada a virar `IF`. UC-02 corretamente ausente.

### R1-1 (médio, decisão do analista): a credencial não autentica nada no flow

- O objetivo de UC-01 é consultar o serviço externo "autenticando-se com uma
  credencial guardada no Credential Vault" (`use-cases.md:12-14`). No flow, a
  chamada REST (Main.robin:62) sai sem nenhum cabeçalho nem autenticação, e a
  credencial (step_03, :65-79) vem **depois** dela e não alimenta nenhum passo.
- O flow reproduz fielmente a ordem do legado: no inventário o REST é o nó 2 e
  a credencial o nó 3 (`01-inventory/inventory.json:42-51`, :2-13), e em
  `input/a360-browser-rest/main.json` nenhum atributo do `REST.get` referencia a
  credencial. Ou seja, a contradição está entre o objetivo documentado e a
  evidência, não é erro de transcrição do conversor. Por isso médio, e não
  bloqueante como o R1-1 de a360-excel-vault (lá a ordem do legado era a
  inversa).
- Agravante documental: a entrada `obter-credencial-do-cofre` cita esta mesma
  evidência como "antes de `REST.get` em `main.json:2`"
  (`reference/subfluxos-comuns.md:62-63`), o que não bate com o inventário. O
  conversor não edita esse arquivo; fica para revisão humana.
- O seletor atual suporta autenticação sem trocar de ação: `CustomHeaders` é
  parâmetro opcional de `Web.InvokeWebService.InvokeWebService`
  (PAD_Robin_ActionKB.json:52291-52296), e há o irmão
  `Web.InvokeWebService.InvokeWebServiceUseAuth` (:52544) para autenticação
  básica. Qualquer dos dois só depois da decisão de R1-1 e da origem da
  credencial (step_03).
- **Pergunta ao analista:** "A chamada `REST.get` (main.json:2) usa a credencial
  de `main.json:3`? Se sim, como (cabeçalho de autorização montado a partir de
  entrada sensível, ou autenticação básica usuário/senha), e a credencial passa
  a ser obtida antes da chamada? Se não, qual passo do UC-01 consome essa
  credencial?"

## 2. Densidade de `TODO reflow`

Sem achado. 4 comentários `# TODO reflow` (Main.robin:22, :31, :43, :74). Dos 3
passos, **2 são ação real da whitelist** (step_01, step_02); step_03 é
comentário porque `Credentials.GetCredential` é `[não validado]` e não é id
Robin (`reference/robin-actions.md:553-561`), o que é a regra
(`robin-conventions.md:21`). Os demais são valor não capturado pela extração
(`in_target_url`, `cfg_rest_endpoint_url`) e a escolha do navegador (A1):
pendências do humano.

Informativo (impeditivo de execução, não de conversão): `cfg_rest_endpoint_url`
vazia (:33) e `in_target_url` precisa ser declarada no designer.

## 3. Convenções de nomenclatura

Sem achado próprio. `step_01_open_browser`, `step_02_call_rest_api`,
`step_03_get_credential` seguem `step_NN_<verbo>_<objeto>`
(robin-conventions.md:85); `cfg_credential_reference`, `cfg_output_folder`,
`cfg_rest_endpoint_url`, `in_target_url`, `out_browser`,
`out_rest_response_headers`, `out_rest_response`, `out_rest_status_code`: prefixo
correto, snake_case minúsculo, nenhuma palavra reservada. O sufixo de subfluxo
comum que falta em step_03 está em R5-1.

## 4. Consistência `notas-conversao.md` × `Main.robin`

As ações de notas:12-16 (`WebAutomation.LaunchEdge.LaunchEdge`,
`Web.InvokeWebService.InvokeWebService`, `Credentials.GetCredential` só como
TODO, `**REGION`, `SET`) batem com Main.robin:47, :62, :65-79, as 3 Regiões e os
3 `SET`, com o mesmo nome de passo e o mesmo status. Nenhuma linha de ação do
flow fica fora das notas. Divergências estão no README e em variáveis sem uso:

### R4-1 (menor): README.md do flow descreve a versão antiga

- README.md:23-26 ainda mapeia `Browser.open` para `Browser.LaunchNewBrowser` e
  `REST.get` para `Web.InvokeRestApi`, ids que **não existem** no PAD
  (robin-actions.md:361, :409; notas:8-10).
- README.md:32-36 diz que as três ações estão `[não validado]` e que o flow
  cita `TODO reflow` "onde entraria o snippet real"; hoje step_01 e step_02 são
  ação `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- README.md:59-63 (seção "Teste") repete o mesmo status antigo.
- Ação: conversor, numa nova rodada, alinha o README às notas (ids, status,
  pendências A1/A4 apontando para os passos atuais). Só documentação; não muda
  o flow.

### R4-2 (menor): configuração e saída sem consumidor

- `cfg_output_folder` (Main.robin:30) é definida e nunca usada: UC-01 não grava
  arquivo. Remover ou justificar no comentário.
- `cfg_credential_reference` (:29) só aparece em comentário (:77). Aceitável
  enquanto step_03 é TODO, mas o comentário do passo deveria dizer que é a
  entrada prevista do subfluxo comum (ver R5-1).
- `out_browser` (:47) nunca é consumido; ligado a R8-1 (o fechamento do
  navegador é o consumidor natural).
- Nenhuma das três situações está registrada em notas-conversao.md.

## 5. Sinalização de subfluxo comum

### R5-1 (médio): step_03 é a entrada `catalogado` `obter-credencial-do-cofre` e não está sinalizado

- `reference/subfluxos-comuns.md:55-75` cataloga o padrão com evidência deste
  mesmo projeto (`a360-browser-rest/input/main.json:3`). A regra
  (subfluxos-comuns.md:21-34; robin-conventions.md:101-106) exige, e o flow não
  tem:
  - nome do passo com sufixo `_subfluxo_comum_obter_credencial_do_cofre`
    (hoje `step_03_get_credential`, Main.robin:67);
  - comentário citando `reference/subfluxos-comuns.md#obter-credencial-do-cofre`,
    as duas evidências e a recomendação de reuso (entrada
    `cfg_credential_reference`, saída `out_credential`);
  - Região `Subfluxo comum: Obter credencial do cofre (candidato a reuso)` (hoje
    `Credencial do Cofre`, :65);
  - registro do apontamento em notas-conversao.md.
- O passo ser só comentário não dispensa a sinalização: a360-excel-vault
  sinalizou o step_04 equivalente, também sem ação real.
- Nenhum "candidato a novo subfluxo comum" declarado nas notas; nenhuma entrada
  `proposto` sinalizada como `catalogado`.

## 6. Subflow padrão do PAD por nome de bot

Não aplicável. A única dependência (`TaskBot.run`, inventory.json:25-37;
target `child.json`) é UC-02, fora do escopo, e não bate com nenhum nome da
tabela (subfluxos-comuns.md:136-143). Nenhum `CALL` no flow, nenhuma citação a
`Log_Splunk`. Observação para a decisão de step_03: se em produção a credencial
não puder chegar por entrada sensível do flow, o subflow padrão ativo
`ConsultarCredencialProducao` é a alternativa já padronizada.

## 7. Ação `proposto` / `colado KB` usada corretamente

Nenhuma ação `proposto`. Nas duas `colado KB`, `$'''example'''` virou
`in_target_url`/`cfg_rest_endpoint_url` e as saídas padrão (`Browser`,
`WebServiceResponse`, `WebServiceResponseHeaders`, `StatusCode`) viraram
`out_browser`/`out_rest_*`. Status real declarado nos dois comentários
(Main.robin:41-42, :56-58), sem tratar como validado. Nenhum `$'''example'''`
nem caminho de teste da KB no flow.

### R7-1 (menor, decisão do analista): `Accept`/`ContentType` copiados do snippet sem evidência

- Main.robin:62 usa `application/json` nos dois campos, valor literal do snippet
  da whitelist (robin-actions.md:364). O legado não registra formato
  (inventory.json:42-51 só tem o atributo `url`); o padrão da própria KB é
  `application/xml` (PAD_Robin_ActionKB.json:52487-52498). `Accept` errado pode
  gerar 406 ou resposta em formato inesperado.
- Mesmo critério do R8-2 de a360-excel-vault: trocar por `cfg_rest_accept` e
  `cfg_rest_content_type` vazias com `# TODO reflow`, ou registrar a decisão do
  analista.
- **Pergunta ao analista:** "Que formato o endpoint de `REST.get` (main.json:2)
  devolve, e ele exige `Accept` específico?"

## 8. Semântica contra a KB

Seletores corretos: `REST.get` para `Web.InvokeWebService.InvokeWebService` com
`Method: Web.Method.Get`, sem corpo (robin-actions.md:356-357; KB :52499-52515);
`Browser.open` para `WebAutomation.LaunchEdge.LaunchEdge` (KB :70652-70754),
com a troca para Chrome pendente de A1 (Main.robin:43-45). `required_params`
presentes nos dois. `TargetDesktop` e `PiPUserDataFolderMode` aparecem como
obrigatórios em `input_params` do LaunchEdge (:70694-70707) mas não no
`golden_example` colado limpo (:70657): segue o exemplo, não é achado.

### R8-1 (médio): navegador aberto e nunca fechado

- step_01 abre o Edge em `out_browser` (Main.robin:47) e nenhum passo o fecha.
  A whitelist tem `WebAutomation.CloseWebBrowser`
  `[colado KB: PAD 2.73, não rodado nesta instalação]` (robin-actions.md:416-424;
  KB :62581-62608), cujo argumento `BrowserInstance` recebe `out_browser`.
- No legado, REST e credencial são filhos do bloco `Browser.open`
  (`input/a360-browser-rest/main.json:4-12`): o fechamento natural é depois de
  step_02/step_03, numa Região de encerramento, documentado como diferença
  deliberada (como o step_07 de a360-excel-vault).
- Ação: conversor acrescenta o passo de fechamento, com status e erro declarado
  (`CloseWebBrowserError`) no comentário.

### R8-2 (médio, decisão do analista): a chamada REST no PAD não herda a sessão do navegador

- `Web.InvokeWebService.InvokeWebService` não tem nenhum parâmetro de instância
  de navegador (KB :52272-52515): no PAD a chamada é independente da página
  aberta em step_01, sem cookies nem sessão dela.
- Evidência nova para a dúvida de `business-rules.md` e
  `classification.md:50-54`: no `main.json` do legado, `REST.get` e
  `CredentialVault.getCredential` estão **aninhados** como filhos de
  `Browser.open` (input/a360-browser-rest/main.json:4-12). O inventário achata
  essa estrutura em nós 1, 2 e 3, por isso a fase 02 não a viu. O aninhamento
  sugere escopo de navegador, mas não prova que a chamada HTTP use a sessão.
- Consequência: se o legado dependia da sessão, este flow não reproduz o
  comportamento (a chamada sai "anônima"); se não dependia, a própria
  classificação manda reavaliar UC-01 para NOT_PAD (classification.md:72-74;
  README.md:50-55). Nos dois casos a conversão atual não está fechada.
- **Pergunta ao analista:** "A chamada `REST.get`, aninhada dentro do bloco
  `Browser.open` no `main.json`, depende de cookie ou sessão da página aberta
  (login web antes da API)? Se sim, como a sessão deve chegar à chamada no PAD;
  se não, UC-01 é reclassificado para NOT_PAD?"

### R8-3 (menor, decisão do analista): falha de integração passa em silêncio

- step_02 usa `FailOnErrorStatus: False` (Main.robin:62) e nenhum passo confere
  `out_rest_status_code`: um 4xx/5xx segue como sucesso. step_01 com
  `in_target_url` inválida falha sem tratamento.
- O legado não tem tratamento de erro observável (inventory.json sem try/catch;
  main.json sem nó de erro), então não há `ON ERROR` a transcrever. Mas o
  `05-test` (CT-04, README.md:75-87 e :96) espera que "o flow sinalize falha",
  o que o flow atual não faz.
- Se o analista quiser tratamento, só com erros declarados pela KB:
  `InvalidUrlError`, `LaunchEdgeError` no step_01 (:70746-70751);
  `DirectoryDoesNotExistError`, `InvalidCustomHeaderError`,
  `InvokeWebServiceError` no step_02 (:52573-52580); `CloseWebBrowserError` no
  fechamento de R8-1 (:62601-62606). Alternativa sem `ON ERROR`: `IF` sobre
  `out_rest_status_code`.
- **Pergunta ao analista:** "Status HTTP fora de 2xx deve interromper o flow
  (falha visível) ou só ser registrado? Qual faixa de status conta como
  sucesso?"

## Conclusão

- A auditoria de 2026-10-21 fica substituída; nenhum de seus achados se aplica
  à versão atual.
- 8 achados, **nenhum bloqueante de colagem**: médios R1-1, R5-1, R8-1, R8-2;
  menores R4-1, R4-2, R7-1, R8-3. Exigem decisão do analista: R1-1, R7-1,
  R8-2, R8-3 (perguntas acima). R5-1, R8-1, R4-1 e R4-2 o conversor trata
  sozinho numa nova rodada.
- Nenhuma ação inventada, nenhum valor de exemplo da KB, nenhum segredo
  literal, escopo do checkpoint respeitado.
- **Não recomendado seguir para `reflow-test` como está.** R8-2 pode tirar
  UC-01 do PAD (NOT_PAD), R1-1 pode reordenar passos e acrescentar
  autenticação, e R8-1/R5-1 mudam nomes e passos. O certo é: decisões do
  analista, nova rodada do `reflow-pad-converter`, `fix-robin-eol` e
  `lint-robin`, nova auditoria.
- **`05-test/test_uc-01-browser-rest/` precisa ser regenerado** depois dessa
  rodada: o README de teste cita os ids inexistentes `Browser.LaunchNewBrowser`
  e `Web.InvokeRestApi` (README.md:42, :70, :83, :95-96), o CT-02 espera
  comportamento de `Credentials.GetCredential`, que não é ação Robin, e o CT-04
  espera falha sinalizada que o flow não produz (R8-3). O manifesto já marca
  `04-pad` e `05-test` como fases desatualizadas (00-manifest.json:23-26).
- Esta auditoria não aprova nem bloqueia: o checkpoint continua com o analista
  humano.
