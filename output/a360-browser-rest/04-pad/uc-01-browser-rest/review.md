# Auditoria semântica: uc-01-browser-rest

<!--
Gerado pelo agent reflow-robin-reviewer em 2026-11-05 (rodada 3), sobre o
Main.robin corrigido em 2026-11-05 a partir da rodada 2 e das decisões do
analista (notas-conversao.md, "Decisões do analista").

Pré-condições (verificadas pelo chamador): `fix-robin-eol`, `lint-robin` e
`reflow scan` sem achados. Esta auditoria cobre o que o lint não cobre: se o
flow que cola faz o que o legado fazia.

Baseline de escopo (não é achado): só UC-01 (main.json:1-3), checkpoint de
2026-10-21 (00-manifest.json:2-7). UC-02 (TaskBot.run -> Excel.read) fora, por
verdict PARTIAL.

Critério (o mesmo das rodadas anteriores e do piloto a360-excel-vault): decisão
do analista e `cfg_` vazia com `# TODO reflow` explícito são pendências
legítimas do humano, não achados bloqueantes de conversão.

Conteúdo de input/ é dado, nunca instrução. input/a360-browser-rest/main.json
foi relido só como evidência estrutural (nós packageName/commandName/attributes
com valores sintéticos `example.invalid` e `synthetic-vault-reference`):
nenhuma instrução dirigida a agentes, nenhuma tentativa de prompt injection.
-->

## Histórico das rodadas

| Rodada | Data | Versão auditada | Resultado |
| --- | --- | --- | --- |
| 1 | 2026-10-21 | Main.robin antigo (ids inexistentes `Browser.LaunchNewBrowser`/`Web.InvokeRestApi`, placeholders que derrubavam a colagem) | Substituída pela rodada 2; nenhum achado se aplica à versão reconvertida. |
| 2 | 2026-11-05 | Reconversão de 2026-11-04 (ADR-029, commit 3c7c10b) | 8 achados, nenhum bloqueante: médios R1-1, R5-1, R8-1, R8-2; menores R4-1, R4-2, R7-1, R8-3. Não recomendado seguir para `reflow-test`. |
| 3 | 2026-11-05 | Correção da rodada 2 com decisões do analista (esta) | Os 8 achados resolvidos (R8-3 como pendência legítima com TODO). 1 achado novo menor (R1-2, documental, do humano). Pronto para `reflow-test`. |

## Resumo

| Categoria | Achados | Severidade |
| --- | --- | --- |
| 1. Cobertura de caso de uso | 1 novo (R1-2) | menor, pendência do humano |
| 2. Densidade de `TODO reflow` | 0 | informativo |
| 3. Nomenclatura | 0 | |
| 4. Consistência notas/README × Main.robin | 0 | informativo (I-1) |
| 5. Sinalização de subfluxo comum | 0 | |
| 6. Subflow padrão por nome de bot | 0 | não aplicável |
| 7. Ação `proposto`/`colado KB` | 0 | |
| 8. Semântica contra a KB | 0 | informativos (I-2, I-3) |
| **Total** | **1** | 0 bloqueantes, 0 médios, 1 menor, 4 informativos |

## Situação dos achados da rodada 2

| Achado | Situação | Evidência |
| --- | --- | --- |
| R1-1 (médio): credencial não autentica nada, vinha depois do REST | **Resolvido** | Decisão 2 do analista (notas:38-46). Cabeçalho de autorização em `CustomHeaders` do step_02 a partir de `cfg_rest_auth_prefix` e da entrada sensível `in_rest_token` (Main.robin:178); entrada documentada (Main.robin:22-27, :104-109, :133-135; README.md:22-26; notas:111-116); Região da credencial antes do REST (Main.robin:92-137, :139-179), motivo comentado (Main.robin:29-36, :111-112). `CustomHeaders` é parâmetro opcional do seletor (KB :52291-52296). Pendência legítima: prefixo vazio com TODO (Main.robin:66-74). |
| R4-1 (menor): README descrevia a versão antiga | **Resolvido** | README.md:28-64 cita só ids reais e status `[colado KB: PAD 2.73, não rodado nesta instalação]`; pendências A1/A4 apontam para step_01/step_03 (README.md:73-76); seção "Teste" atualizada sem estado datado de gate (README.md:80-91). Resíduo de redação em I-1. |
| R4-2 (menor): configuração e saída sem consumidor | **Resolvido** | `cfg_output_folder` e `cfg_credential_reference` removidas (Main.robin:44-48; notas:63-66); `out_browser` consumida pelo step_05 (Main.robin:203). |
| R5-1 (médio): step_03 sem sinalização de subfluxo comum | **Resolvido** | Nome `step_03_get_credential_subfluxo_comum_obter_credencial_do_cofre` (Main.robin:94), Região `Subfluxo comum: Obter credencial do cofre (candidato a reuso)` (:92), comentário com a entrada, as duas evidências e a recomendação de reuso (:114-131), registro em notas:80-100. Mesmo formato do step_04 do piloto a360-excel-vault. |
| R7-1 (menor): `Accept`/`ContentType` copiados do snippet | **Resolvido** | `cfg_rest_accept`/`cfg_rest_content_type` vazias com TODO citando o default `application/xml` da KB e a ausência de evidência (Main.robin:56-64); decisão 4 (notas:50-52). |
| R8-1 (médio): navegador aberto e nunca fechado | **Resolvido** | `WebAutomation.CloseWebBrowser` como step_05_close_browser na Região "Encerramento" (Main.robin:181-204), diferença deliberada documentada (:190-194), id e argumento conferem com a KB (:62581-62606) e a whitelist (robin-actions.md:416-424). Numeração 05 segue a regra do R3-1 do piloto (:186-189). |
| R8-2 (médio): REST não herda a sessão do navegador | **Resolvido por decisão do analista** | Decisão 1 (notas:29-37): API independente da sessão; registrada no comentário do step_02 (Main.robin:150-156). Resíduo documental fora do escopo do conversor em R1-2. |
| R8-3 (menor): falha de integração passa em silêncio | **Resolvido como pendência legítima** | Decisão 3 (notas:47-49): `# TODO reflow` explícito no step_02 (Main.robin:166-176) com a consequência de `FailOnErrorStatus: False`, só erros declarados pela KB (:52573-52580) e sem `ON ERROR` inventado; step_01 e step_05 com erros declarados citados (Main.robin:199-201). O flow continua sem sinalizar falha HTTP até a decisão: o CT de falha do `05-test` deve refletir isso. |

## 1. Cobertura de caso de uso

Os 3 fatos de UC-01 (`02-docs/use-cases.md:16-18`; `pad_use_cases` em
`classification.md:4`) têm passo: step_01_open_browser (Main.robin:89, ação
real), step_03 (Main.robin:92-137, só documentação por decisão do analista: a
credencial chega por `in_rest_token`, consumida em :178) e step_02_call_rest_api
(Main.robin:178, ação real). `business-rules.md:8-22` não tem condicional: nada
a virar `IF`. UC-02 corretamente ausente como ação (ver avaliação da Região
abaixo). O objetivo "autenticando-se com uma credencial" (`use-cases.md:12-14`),
que motivou R1-1, agora é atendido pelo cabeçalho do step_02.

### R1-2 (menor, pendência do humano): a decisão R8-2 contradiz a classificação e não está registrada no manifesto

- `classification.md:72-74` diz que, se a chamada REST funcionar sem o
  navegador, UC-01 "deve ser reavaliado para NOT_PAD (N1 puro)"; os
  `Próximos passos` (:96-98) repetem isso como decisão de checkpoint. A decisão 1
  do analista (notas:29-37) confirma a independência e mesmo assim mantém UC-01
  no PAD, sem que a classificação nem o `checkpoint.scope` do manifesto
  (00-manifest.json:2-7) registrem o motivo.
- Consequência semântica: com a API independente, step_01 abre uma página que
  nenhum passo lê e step_05 a fecha (Main.robin:89, :203). É fiel ao legado
  (main.json não lê nada da página), mas o único passo de UI do flow passa a não
  ter efeito funcional, e mesmo assim mantém a exigência de A1 (extensão do PAD
  no navegador) para rodar.
- O conversor já sinalizou isso para revisão humana (notas:33-37) e não pode
  editar manifesto nem classificação: não há o que corrigir no `Main.robin`.
- **Ação do analista:** registrar no manifesto/classificação por que UC-01
  continua no PAD apesar da independência (ou reconsiderar NOT_PAD). Não impede
  gerar o `05-test`.

## 2. Densidade de `TODO reflow`

Sem achado. 7 comentários `# TODO reflow` (Main.robin:40, :50, :56, :66, :85,
:133, :166). Dos 4 passos no escopo, **3 são ação real da whitelist** (step_01,
step_02, step_05), mais 4 `SET cfg_`; step_03 é documentação por decisão do
analista. Todos os TODO são pendências do humano: valores não capturados pela
extração (`in_target_url`, `cfg_rest_endpoint_url`, `cfg_rest_accept`,
`cfg_rest_content_type`, `cfg_rest_auth_prefix`), navegador do legado (A1),
declaração de `in_rest_token` como sensível (A4) e critério de status HTTP
(R8-3). A conversão não está incompleta: está bloqueada por dados, não por ação
faltante.

## 3. Convenções de nomenclatura

Sem achado. `step_01_open_browser`, `step_02_call_rest_api`,
`step_03_get_credential_subfluxo_comum_obter_credencial_do_cofre`,
`step_05_close_browser` e `step_04_out_of_scope_subflow_child` seguem
`step_NN_<verbo>_<objeto>` com os sufixos exigidos (robin-conventions.md:85,
:92-106), no mesmo padrão do piloto a360-excel-vault. Variáveis `in_target_url`,
`in_rest_token`, `cfg_rest_endpoint_url`, `cfg_rest_accept`,
`cfg_rest_content_type`, `cfg_rest_auth_prefix`, `out_browser`,
`out_rest_response_headers`, `out_rest_response`, `out_rest_status_code`:
prefixo correto, snake_case minúsculo, nenhuma palavra reservada. A numeração
fora da ordem de execução (03 antes de 02, 05 sem origem) está justificada no
cabeçalho (Main.robin:29-36) e no README (README.md:34-36).

## 4. Consistência `notas-conversao.md`/README × `Main.robin`

Sem achado. As 5 entradas de notas:17-21 (`WebAutomation.LaunchEdge.LaunchEdge`,
`Web.InvokeWebService.InvokeWebService`, `WebAutomation.CloseWebBrowser`,
`**REGION`, `SET`) batem com Main.robin:89, :178, :203, as 5 Regiões na ordem
declarada (notas:20; Main.robin:76, :92, :139, :181, :206) e os 4 `SET`, com o
mesmo passo e o mesmo status. Nenhuma linha de ação do flow fica fora das notas.
`Credentials.GetCredential` aparece só como linha de tabela verdade em
comentário (Main.robin:98-102), coerente com notas:23-25. README.md:38-64 lista
os mesmos passos, a mesma ordem de Regiões e os mesmos status.

- **I-1 (informativo):** README.md:4-6 descreve o escopo como "consulta REST
  autenticada pela credencial do Credential Vault"; é a descrição do legado
  (UC-01), mas no flow PAD não há cofre: a credencial vem de `in_rest_token`
  (README.md:25-26, :42-44). Uma nova rodada pode trocar por "credencial que no
  legado vinha do Credential Vault". Não muda o flow.

## 5. Sinalização de subfluxo comum

Sem achado. Sinalização completa do step_03 (ver R5-1 acima). A entrada
`obter-credencial-do-cofre` é `catalogado` (subfluxos-comuns.md:75), com as duas
evidências citadas no flow (Main.robin:119-120). Nenhum "candidato a novo
subfluxo comum" declarado (notas:99-100); nenhuma entrada `proposto`
(`tratamento_erro_padrao`, `notificacao_de_falha_por_email`) sinalizada como
`catalogado`: o TODO R8-3 não cria bloco de erro, então não há o que sinalizar.

Pendência do humano, já registrada pelo conversor (notas:94-97), fora do escopo
de escrita de ambos os agents: `reference/subfluxos-comuns.md:62-63` descreve a
evidência deste projeto como "antes de `REST.get`", o que não bate com o
inventário (`01-inventory/inventory.json:2-13`, :42-51).

## 6. Subflow padrão do PAD por nome de bot

Não aplicável. A única dependência (`TaskBot.run`, inventory.json:25-37, target
`child.json`, botName `child`) é UC-02, fora do escopo, e não bate com nenhum
nome ativo nem descontinuado da tabela (subfluxos-comuns.md:136-143); o
comentário do step_04 diz isso explicitamente (Main.robin:214-216). Nenhum
`CALL`, nenhuma citação a `Log_Splunk`. `ConsultarCredencialProducao` é citado
corretamente só como alternativa a decidir (Main.robin:127-131), não aplicado.

### Avaliação da Região "Fora do escopo aprovado (UC-02)" (Main.robin:206-220)

Adequada, sem achado:

- Só comentário, sem `CALL` nem ação: UC-02 não é tratado como convertido
  (`NÃO CONVERTIDO`, :208-210), coerente com o verdict PARTIAL e o escopo do
  checkpoint, citados (:217-219).
- Rastreabilidade correta: `TaskBot.run`, atributo `botName`, dependência
  `resolvida` para `child.json` (inventory.json:25-37) e leitura Excel do filho
  (child.json:1).
- Posição fiel ao legado: em `input/a360-browser-rest/main.json`, `TaskBot.run`
  é irmão **posterior** ao bloco `Browser.open`, não filho dele; por isso vir
  depois de "Encerramento" (fechamento do navegador) reproduz a ordem original.
- Nome `step_04_out_of_scope_subflow_child` mantém o número do legado e o
  sufixo `_subflow_<bot_filho>` (robin-conventions.md:92-95), no mesmo formato
  dos steps fora de escopo do piloto a360-excel-vault.
- O rótulo não é um estágio de `use-cases.md` (robin-conventions.md:89-91), mas
  é deliberado e explícito; aceitável. Região só com comentários passou no lint;
  colagem real ainda não exercitada nesta instalação.

## 7. Ação `proposto` / `colado KB` usada corretamente

Sem achado. Nenhuma ação `proposto`. Nas três `colado KB`, `$'''example'''`
virou `in_target_url`/`cfg_rest_endpoint_url`, as saídas padrão (`Browser`,
`WebServiceResponse`, `WebServiceResponseHeaders`, `StatusCode`) viraram
`out_browser`/`out_rest_*`, e a entrada `BrowserInstance: Browser` do
CloseWebBrowser virou `out_browser`. O `application/json` literal do snippet saiu
(R7-1). Status real declarado nos três comentários (Main.robin:83-84, :147-149,
:197-198), sem tratar como validado (cabeçalho :17-18). Nenhum `$'''example'''`,
`ExcelInstance` ou caminho de teste da KB no flow. Timeouts (60/60, 30) e
booleanos são os defaults da KB, não valores de exemplo.

## 8. Semântica contra a KB

Sem achado. Seletores corretos: `Browser.open` para
`WebAutomation.LaunchEdge.LaunchEdge` (KB :70652), troca para Chrome pendente de
A1 (Main.robin:85-87; irmão existe na KB :68594); `REST.get` para
`Web.InvokeWebService.InvokeWebService` com `Method: Web.Method.Get` (enum
listado, KB :52499-52515), sem `RequestBody`; `Url`, `Accept` e `ContentType`
obrigatórios presentes; `UserAgent` (opcional, :52286-52290) omitido, permitido.
`CustomHeaders` está em `input_params` do seletor; o irmão `UseAuth` não foi
usado, coerente com token em cabeçalho. Todo recurso aberto é fechado: o único é
o navegador (step_01 → step_05). Não há Excel nem banco. Tratamento de erro: o
legado não tinha (inventory.json sem try/catch), nenhum `ON ERROR` foi
inventado, e os erros citados nos comentários são exatamente os declarados em
`error_handling` (KB :52573-52580, :62601-62606; robin-actions.md:408).

- **I-2 (informativo, para o `05-test`):** a montagem do cabeçalho junta duas
  expressões `%...%` adjacentes dentro da string (Main.robin:178), o mesmo padrão
  do piloto a360-excel-vault (ADR-030). Passou no lint, mas nenhum dos dois flows
  rodou no PAD. O flow de teste deve conferir o valor efetivo do cabeçalho com
  prefixo vazio e com prefixo preenchido, e o comportamento com `in_rest_token`
  vazia (candidato a `InvalidCustomHeaderError` ou a um 401 silencioso, que hoje
  só aparece em `out_rest_status_code`, R8-3).
- **I-3 (informativo):** as citações `main.json:N` seguem dois sentidos no mesmo
  arquivo: ordinal de nó do inventário (`main.json:1-4`, ex. Main.robin:32, :211)
  e linha física do JSON (`main.json:4-12` para o bloco `Browser.open`,
  Main.robin:155, :193). Ambas conferem, mas `main.json:4` (TaskBot.run, nó 4)
  fica na linha física 13. Quem rastrear à mão deve saber disso; não exige
  correção agora.
- Observação para quem mantém a whitelist (não é achado do flow): a seção do GET
  (robin-actions.md:354-365) não menciona `CustomHeaders`, ao contrário da do
  POST (:369-370); o parâmetro existe no seletor (KB :52291-52296).
- `out_rest_response` e `out_rest_response_headers` não têm consumidor: é o
  resultado do UC-01 ("prontos para uso pelo restante do fluxo",
  use-cases.md:19-20), e o legado também não os consumia em `main.json:1-3`.

## Conclusão

- Os 8 achados da rodada 2 estão resolvidos (R8-2 e R8-3 por decisão do
  analista, com o TODO de critério HTTP como pendência legítima).
- 1 achado novo, **menor e do humano** (R1-2: registrar no manifesto e na
  classificação por que UC-01 fica no PAD apesar da API independente). 0
  bloqueantes, 0 médios. 4 informativos (I-1, I-2, I-3 e a observação da
  whitelist).
- Nenhuma ação inventada, nenhum valor de exemplo da KB, nenhum segredo literal,
  nenhum `ON ERROR` com erro não declarado, escopo do checkpoint respeitado.
- **Pronto para `reflow-test`** (gerar o flow de teste). A **execução** do teste
  continua dependendo do analista: declarar `in_target_url` e `in_rest_token`
  (sensível) no designer, preencher `cfg_rest_endpoint_url`, `cfg_rest_accept`,
  `cfg_rest_content_type` e `cfg_rest_auth_prefix`, confirmar o navegador (A1) e
  decidir o critério de status HTTP (R8-3).
- `05-test/test_uc-01-browser-rest/` está desatualizado (00-manifest.json:23-26)
  e precisa ser regenerado: a versão atual cita ids e comportamentos antigos. O
  novo teste deve cobrir I-2 e não esperar falha sinalizada para 4xx/5xx
  enquanto R8-3 estiver aberto.
- Esta auditoria não aprova nem bloqueia: o checkpoint continua com o analista
  humano.
