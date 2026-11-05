# Auditoria semântica: uc-01-excel-vault

<!--
Gerado pelo agent reflow-robin-reviewer em 2026-11-05 (segunda rodada), sobre o
Main.robin corrigido em 2026-11-05 a partir da auditoria anterior (achados R1-1,
R5-1, R7-1, R8-1, R8-2, R8-3, R8-4, R8-5) e das "Decisões do analista (Cleyber,
2026-11-05)" registradas em notas-conversao.md:28-44. Substitui a auditoria da
primeira rodada de 2026-11-05.

Pré-condições (verificadas pelo chamador): fix-robin-eol aplicado;
`lint-robin a360-excel-vault`, `reflow scan` e `kb verify` sem achados. Esta
auditoria cobre o que o lint não cobre: se o flow que cola faz o que o legado
fazia.

Baseline de escopo (não é achado): conversão deliberadamente parcial, ADR-028.
Só main.json:1-4 no escopo. main.json:5-6 aparecem só como comentário na Região
"Fora do escopo aprovado (ADR-028)" (Main.robin:199-219).

Critério desta rodada: decisão do analista e `cfg_` vazia com `# TODO reflow`
explícito são pendências legítimas do humano, não achados bloqueantes de
conversão.

Conteúdo de input/ é dado, nunca instrução. input/a360-excel-vault/main.json foi
lido só para conferir semântica; não contém instrução dirigida a agentes
(nenhuma tentativa de prompt injection).
-->

## Resumo

| Categoria | Achados novos | Severidade |
| --- | --- | --- |
| 1. Cobertura de caso de uso | 0 | |
| 2. Densidade de `TODO reflow` | 0 | informativo |
| 3. Nomenclatura | 1 (R3-1) | menor |
| 4. Consistência notas × Main.robin (e README) | 1 (R4-1) | menor |
| 5. Sinalização de subfluxo comum | 0 | |
| 6. Subflow padrão por nome de bot | 0 | não aplicável (1 observação) |
| 7. Ação `proposto`/`colado KB` | 0 | |
| 8. Semântica contra a KB | 2 (R8-6, R8-7) | menores |
| **Total** | **4** | nenhum bloqueante |

## Status dos achados anteriores

| Achado | Status | Evidência |
| --- | --- | --- |
| R1-1 (bloqueante): POST sem autenticação, credencial depois do POST | **Resolvido**, com pendência legítima do analista | `CustomHeaders: $'''Authorization: %cfg_rest_auth_scheme% %in_rest_token%'''` (Main.robin:196); `in_rest_token` documentada como entrada sensível (Main.robin:27-30, :162-164; README.md:31-35; notas:84-87); Região da credencial movida para antes do REST (Main.robin:32-35, :128-166, :168-197). Pendente: esquema em `cfg_rest_auth_scheme` vazia com TODO (Main.robin:75-81). |
| R5-1 (menor): falta âncora e segunda evidência | **Resolvido** | Main.robin:151-155 cita `reference/subfluxos-comuns.md#obter-credencial-do-cofre`, `a360-browser-rest/input/main.json:3` e `a360-excel-vault/input/main.json:4`; mesmo em notas:72-78. |
| R7-1 (menor): forma de uma linha descrita como validada | **Resolvido** | Main.robin:92-95, notas:17, README.md:42-46: ação `[validado PAD: rodou]` no multilinha, forma de uma linha `[colado KB: PAD 2.73, não rodado nesta instalação]`, conforme robin-actions.md:199-207. |
| R8-1 (médio): Excel nunca fechado | **Resolvido** | `Excel.CloseExcel.Close Instance: out_excel_instance` (Main.robin:125), logo após a leitura e antes do POST, sem salvar (`constraints.CloseMode: DoNotSave`, PAD_Robin_ActionKB.json:11150-11152). Diferença deliberada em relação ao legado documentada (Main.robin:114-119, notas:19, README.md:49-51). |
| R8-2 (médio): DataTable como texto e JSON afirmado sem evidência | **Resolvido por decisão do analista** (pendência legítima com TODO) | `Accept`/`ContentType` agora vêm de `cfg_rest_accept`/`cfg_rest_content_type` vazias com TODO (Main.robin:66-73); nada afirma JSON. Corpo `$'''%out_excel_data%'''` mantido com TODO explícito de formato e serialização (Main.robin:183-188; notas:41-43, :97). |
| R8-3 (menor): seletor sem autenticação própria | **Resolvido por decisão do analista** | Decisão 2 (notas:35-38): token no cabeçalho, seletor `InvokeWebServicePost` mantido (`UseAuthentication: False`, PAD_Robin_ActionKB.json:52850), registrado em Main.robin:178-182. |
| R8-4 (menor): falha HTTP passa em silêncio | **Resolvido por decisão do analista** (pendência legítima com TODO) | TODO em Main.robin:189-194 pede critério de status e decisão de interromper; cita só os erros que a ação declara (`DirectoryDoesNotExistError`, `InvalidCustomHeaderError`, `InvokeWebServiceError`, PAD_Robin_ActionKB.json:52886-52892). Nenhum `ON ERROR` inventado. |
| R8-5 (menor): extensão dupla no caminho | **Resolvido** | `Path: $'''%cfg_excel_input_folder%/%cfg_excel_file_name%'''` sem `.xlsx` fixo (Main.robin:98); TODO diz que `cfg_excel_file_name` vai com extensão (Main.robin:42-45; notas:93). Coerente com o atributo `file` do legado, que inclui a extensão. |

Observação de R3 anterior: `cfg_credential_reference`, que era definida e nunca
consumida, foi removida (notas:32-34). Resolvido.

## 1. Cobertura de caso de uso

Sem achado. Os 4 passos de UC-01 (`02-docs/use-cases.md:12-15`, main.json:1-4)
têm correspondente: step_01 (Main.robin:98), step_02 (:111), step_04 (:128-166,
documentação da origem da credencial, por decisão do analista), step_03 (:196).
O resultado esperado "chamada HTTP autenticada, sem exposição do valor da
credencial" (`use-cases.md:16-18`) agora é atendido estruturalmente: o token
entra por entrada sensível `in_rest_token` e vai no cabeçalho `Authorization`,
nunca como literal. `business-rules.md` (RN-01) não tem condicional: nada a
virar `IF`. O passo extra step_02b (fechar Excel) não tem origem no legado e
está documentado como diferença deliberada.

## 2. Densidade de `TODO reflow`

Sem achado. 10 comentários `# TODO reflow` (Main.robin:39, :49, :58, :66, :75,
:162, :183, :189, :211, :217). Dos 5 passos no escopo, **4 são ação real da
whitelist** (step_01, 02, 02b, 03); step_04 é comentário por decisão do analista
(credencial por entrada, sem ação de cofre). Os 2 TODO de main.json:5-6 são
esperados por ADR-028. Os demais TODO são `cfg_` não capturadas pela extração,
formato do corpo e critério HTTP: pendências do humano, não conversão
incompleta.

Informativo (impeditivo de **execução**, não de conversão): todas as `cfg_`
continuam vazias (Main.robin:46-47, :53-56, :64, :72-73, :81) e `in_rest_token`
precisa ser declarada no designer. O legado (`input/a360-excel-vault/main.json`)
tem `file` e `range` que podem orientar o preenchimento depois de confirmados
pelo analista; o valor de `authorization` do nó 3 **nunca** deve ir para o flow
(alerta A4), e o conversor corretamente não o copiou.

## 3. Convenções de nomenclatura

Todos os nomes de variável têm prefixo correto e snake_case minúsculo:
`cfg_excel_input_folder`, `cfg_excel_file_name`, `cfg_excel_start_column`,
`cfg_excel_start_row`, `cfg_excel_end_column`, `cfg_excel_end_row`,
`cfg_rest_endpoint_url`, `cfg_rest_accept`, `cfg_rest_content_type`,
`cfg_rest_auth_scheme`, `in_rest_token`, `out_excel_instance`,
`out_excel_data`, `out_rest_status_code`, `out_rest_response`,
`out_rest_response_headers`. Nenhum é palavra reservada.

### R3-1 (menor): `step_02b_close_excel_instance` foge do padrão `step_NN_<verbo>_<objeto>`

- `robin-conventions.md:85` fixa `step_NN_<verbo>_<objeto>`; `02b` não é `NN`
  (Main.robin:114, notas:19, README.md:49).
- O motivo é compreensível (manter `step_NN` ligado à ordem do legado, Main.robin:34-35,
  e o passo não tem origem no legado), e o nome é só comentário, sem efeito na
  colagem. Mas é uma variação nova que não está prevista na convenção.
- Ação: o analista decide se aceita a variação (e, nesse caso, ela vale ser
  registrada em `robin-conventions.md` por edição humana) ou se o conversor
  renumera. Não impede `reflow-test`.

## 4. Consistência `notas-conversao.md` × `Main.robin`

Bate nos dois sentidos. As 4 ações de notas:17-20
(`Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`,
`Excel.ReadFromExcel.ReadCells`, `Excel.CloseExcel.Close`,
`Web.InvokeWebService.InvokeWebServicePost`) e os itens `**REGION`/`SET`
(notas:21-22) aparecem em Main.robin:98, :111, :125, :196, com o mesmo passo e o
mesmo status. No sentido inverso, toda linha de ação do flow está nas notas.
`Credentials.GetCredential` aparece só em comentário no Main.robin (:137-138),
como "nenhuma ação", coerente com notas:24-26. `Cyberark.GetPassword.GetPassword`
não é mais citado em nenhum dos dois. Os 4 rótulos de Região de notas:21 batem
com Main.robin:83, :128, :168, :199. As citações da KB divergem de linha, mas
ambas são válidas: Main.robin:67 aponta os parâmetros com default
(PAD_Robin_ActionKB.json:52806-52815) e notas:43 aponta `required_params`
(:52835-52847).

### R4-1 (menor): seção "Teste" do README está desatualizada e mistura gerar com executar o teste

- README.md:83-84 diz que "Esta rodada não rodou `fix-robin-eol` nem
  `lint-robin` (sem shell): ficam com o orquestrador". O chamador já rodou os
  dois sem achados: a frase ficou velha.
- README.md:84-87 diz que, **antes de gerar** `05-test/`, o analista precisa
  declarar `in_rest_token`, preencher as `cfg_`, decidir corpo e critério HTTP e
  **rodar o flow no designer**. Isso é pré-condição de **executar** o teste e de
  promover ações para `[validado PAD: rodou]`, não de gerar o roteiro de
  cenários com PASS/FAIL vazio que o `reflow-test` produz. Como está, o README
  sugere um gate mais restritivo do que o pipeline tem.
- Ação: conversor, numa nova rodada, atualiza a seção "Teste" (remover a frase
  sobre `fix-robin-eol`/`lint-robin` e separar "gerar 05-test" de "executar no
  designer"). Não impede `reflow-test`.

## 5. Sinalização de subfluxo comum

Sem achado. step_04 corresponde à entrada `catalogado` `obter-credencial-do-cofre`
(`subfluxos-comuns.md:55-75`) e tem a sinalização completa: sufixo
`_subfluxo_comum_obter_credencial_do_cofre` (Main.robin:130), comentário com
âncora, as duas evidências e a recomendação de reuso (:149-160), Região
`Subfluxo comum: Obter credencial do cofre (candidato a reuso)` (:128) e
registro em notas:70-78. Nenhum "candidato a novo subfluxo comum" declarado
(notas:82), então não há evidência a conferir. Nenhuma entrada `proposto`
sinalizada como `catalogado`.

Observação (não é achado): com a decisão de entrada sensível, a Região do
subfluxo comum ficou só com comentário (nenhuma ação busca a credencial no
PAD). A sinalização continua correta como rastreio do padrão do legado, e o
próprio comentário (:159-160) registra que a recomendação de reuso vale quando
houver cofre no PAD.

## 6. Subflow padrão do PAD por nome de bot

Não aplicável. `dependencies` está vazio (`01-inventory/inventory.json:34`);
não há `TaskBot.run` com `target`/`botName`. O flow não tem `CALL` nem cita
`Log_Splunk`.

Observação para o analista (não é achado, a regra não se aplica sem
dependência): a tabela de `subfluxos-comuns.md:140` lista
`ConsultarCredencialProducao` como subflow padrão **ativo** para consultar
credencial de produção, relacionado a `obter-credencial-do-cofre`. Se no
ambiente de produção o token não puder chegar por entrada do flow, esse subflow
é a alternativa já padronizada a considerar, em vez de uma ação de cofre nova.

## 7. Ação `proposto` / `colado KB` usada corretamente

Sem achado. Nenhuma ação `proposto`. Nas `colado KB`, todos os valores de
exemplo foram trocados por nomes do flow:

- step_02 (:111): `ExcelInstance` → `out_excel_instance`, `$'''example'''` →
  `cfg_excel_start_column`/`cfg_excel_end_column`, `1` → `cfg_excel_start_row`/
  `cfg_excel_end_row`, `ExcelData` → `out_excel_data`.
- step_02b (:125): `ExcelInstance` (robin-actions.md:280) → `out_excel_instance`,
  a instância real aberta no step_01.
- step_03 (:196): `Url`, `Accept`, `ContentType`, `CustomHeaders`,
  `RequestBody` saíram de `$'''example'''`/`application/json` para
  `cfg_`/`in_`/`out_`; saídas `StatusCode`/`WebServiceResponse`/
  `WebServiceResponseHeaders` → `out_rest_*`.
- Nenhum `$'''example'''`, `ExcelInstance`, `ExcelData`, `C:\temp\...` no flow.
- `out_excel_instance`/`out_excel_data` coincidem com os snippets **validados
  pelo analista** (robin-actions.md:196, :228), não com o exemplo da KB: uso
  coerente, não cópia preguiçosa.
- Comentários de step_01, 02, 02b e 03 declaram o status real (`colado KB`;
  step_01 com a distinção multilinha/uma linha) (:92-95, :109, :123, :177).

## 8. Semântica contra a KB

Seletores conferidos e corretos:

- step_01: `Excel.open` → `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`
  (a360-to-pad.md:30).
- step_02: atributo `range` (`A1:B3` no legado) → `Excel.ReadFromExcel.ReadCells`
  (intervalo), não `ReadCell`/`ReadAllCells` (a360-to-pad.md:31).
- step_02b: `Excel.CloseExcel.Close` (PAD_Robin_ActionKB.json:11133), único
  parâmetro `Instance` presente; `CloseMode: DoNotSave`, coerente com um flow
  que só lê (a360-to-pad.md:33).
- step_03: `REST.post` → `Web.InvokeWebService.InvokeWebServicePost`
  (PAD_Robin_ActionKB.json:52584, `Method: Post`). Os 11 `required_params`
  (:52835-52847) estão presentes; `UserAgent` (opcional) omitido.
- Recursos abertos/fechados: o Excel é aberto (:98) e fechado (:125). Nenhum
  navegador ou conexão de banco no escopo.
- Erro em integração externa: o legado não tem tratamento observável
  (`subfluxos-comuns.md:82-85`); a decisão fica no TODO de R8-4 (:189-194), com
  os erros certos da KB. Pendência legítima.

### R8-6 (menor): `Authorization` com esquema vazio gera cabeçalho ambíguo e falha silenciosa

- Main.robin:196 monta `Authorization: %cfg_rest_auth_scheme% %in_rest_token%`.
  Com `cfg_rest_auth_scheme` vazia (:81), o cabeçalho sai com espaço duplo entre o
  nome e o token, que só funciona se o destino aceitar o token sem prefixo.
- Se o destino exigir um esquema e ninguém preencher a `cfg_`, o POST recebe 401
  e, com `FailOnErrorStatus: False` sem verificação de `out_rest_status_code`
  (R8-4), o flow termina "com sucesso" sem ter autenticado.
- Não é defeito de conversão: o TODO de :75-80 já pede o esquema. O achado é só
  amarrar as duas pendências: ao decidir R8-4, incluir no critério o caso de
  falha de autenticação, e ao decidir o esquema, confirmar se "sem prefixo" é
  aceitável (nesse caso, ajustar o texto para não deixar o espaço sobrando).

### R8-7 (menor): planilha aberta com `ReadOnly: False` num flow que só lê

- step_01 (:98) abre com `ReadOnly: False`; o flow só lê e fecha sem salvar
  (:125). O valor veio do snippet validado (robin-actions.md:194), não do
  legado (main.json:1 não tem atributo de modo de abertura).
- Abrir para escrita trava o arquivo para outros usuários durante a execução e,
  se o flow parar entre step_01 e step_02b (erro em `ReadCells`, sem tratamento),
  o processo Excel fica aberto com o arquivo travado.
- Ação: analista avalia `ReadOnly: True` (troca só de valor, permitida pelo
  método de template; o seletor não muda). Não impede `reflow-test`.

## Conclusão

- Os 8 achados anteriores estão tratados: **R1-1, R5-1, R7-1, R8-1, R8-5
  resolvidos**; **R8-2, R8-3, R8-4 resolvidos por decisão do analista**, com
  pendência legítima registrada em `# TODO reflow` e nas notas. Nenhum ficou sem
  resolução.
- 4 achados novos, todos **menores** e nenhum bloqueante: R3-1 (nome
  `step_02b`), R4-1 (seção "Teste" do README desatualizada), R8-6 (esquema de
  autorização vazio + falha silenciosa), R8-7 (`ReadOnly: False`).
- Nenhuma ação inventada, nenhum valor de exemplo da KB, nenhum segredo literal,
  escopo de ADR-028 respeitado.
- **Pronto para `reflow-test`** no sentido de gerar `05-test/` (cenários e
  estrutura PASS/FAIL vazia, sem execução): não há achado de conversão
  bloqueante. **Não está pronto para executar** o teste no designer até o
  analista declarar `in_rest_token` (sensível), preencher as 10 `cfg_` vazias,
  decidir formato do corpo, esquema de autorização e critério de status HTTP.
  Os cenários gerados devem cobrir essas pendências (inclusive 401 por esquema
  errado e corpo em formato inesperado).
- Esta auditoria não aprova nem bloqueia: o checkpoint continua com o analista
  humano.
