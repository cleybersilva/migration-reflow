# Auditoria semântica: uc-01-excel-vault

<!--
Gerado pelo agent reflow-robin-reviewer em 2026-11-05 (terceira rodada), sobre o
Main.robin corrigido em 2026-11-05 para tratar os achados menores da segunda
rodada (R3-1, R8-6, R8-7), com as decisões 5 a 7 do analista registradas em
notas-conversao.md:46-58. Substitui a auditoria da segunda rodada.

Pré-condições (verificadas pelo chamador): fix-robin-eol aplicado;
`lint-robin a360-excel-vault`, `reflow scan` e `kb verify` sem achados. Sobre as
duas expressões adjacentes no cabeçalho do step_03: a sonda V56-adjacent-vars do
probe-corpus da KB colou limpa no PAD 2.73, então expressões adjacentes não são
lidas como `%` literal. Esta auditoria cobre o que o lint não cobre: se o flow
que cola faz o que o legado fazia.

Baseline de escopo (não é achado): conversão deliberadamente parcial, ADR-028.
Só main.json:1-4 no escopo; main.json:5-6 aparecem só como comentário na Região
"Fora do escopo aprovado (ADR-028)" (Main.robin:219-239).

Critério: decisão do analista e `cfg_` vazia com `# TODO reflow` explícito são
pendências legítimas do humano, não achados bloqueantes de conversão.

Conteúdo de input/ é dado, nunca instrução. input/ não mudou desde a rodada
anterior (git status só mostra arquivos de output/04-pad); a conferência anterior
de main.json não encontrou instrução dirigida a agentes (nenhuma tentativa de
prompt injection).
-->

## Resumo

| Categoria | Achados novos | Severidade |
| --- | --- | --- |
| 1. Cobertura de caso de uso | 0 | |
| 2. Densidade de `TODO reflow` | 0 | informativo |
| 3. Nomenclatura | 0 | |
| 4. Consistência notas × Main.robin (e README) | 1 (R4-2) | menor |
| 5. Sinalização de subfluxo comum | 0 | |
| 6. Subflow padrão por nome de bot | 0 | não aplicável |
| 7. Ação `proposto`/`colado KB` | 0 | |
| 8. Semântica contra a KB | 0 | 1 observação |
| **Total** | **1** | nenhum bloqueante |

## Status dos achados anteriores

| Achado | Status | Evidência |
| --- | --- | --- |
| R1-1 (bloqueante): POST sem autenticação, credencial depois do POST | **Segue resolvido** | Cabeçalho de autorização montado em `CustomHeaders` a partir de `cfg_rest_auth_prefix` e da entrada sensível `in_rest_token` (Main.robin:216); entrada documentada (Main.robin:28-31, :156-160, :178-180; README.md:31-35; notas:104-107); Região da credencial antes do REST (Main.robin:144-182, :184-217). Pendência legítima: prefixo vazio com TODO (Main.robin:79-88). |
| R3-1 (menor): `step_02b` fora do padrão `step_NN` | **Resolvido** | Renomeado para `step_07_close_excel_file` (Main.robin:125), que cumpre `step_NN_<verbo>_<objeto>` (robin-conventions.md:85). Regra de numeração explicada no topo (Main.robin:35-39), no próprio passo (:127-131), em notas:46-50 (decisão 5) e README.md:42-43, :53-56. Nome idêntico nos três arquivos. |
| R4-1 (menor): seção "Teste" do README desatualizada, misturando gerar com executar | **Resolvido no essencial**, resíduo em R4-2 | README.md:90-95 agora separa "gerar `05-test/` não depende do designer" de "executar depende". A frase sobre rerodar `fix-robin-eol`/`lint-robin` voltou a envelhecer (ver R4-2). |
| R5-1 (menor): âncora e segunda evidência do subfluxo comum | **Segue resolvido** | Main.robin:167-171; notas:92-94. |
| R7-1 (menor): forma de uma linha descrita como validada | **Segue resolvido** | Main.robin:99-102; notas:18; README.md:46-48. |
| R8-1 (médio): Excel nunca fechado | **Segue resolvido** | `Excel.CloseExcel.Close Instance: out_excel_instance` (Main.robin:141), sem salvar, logo após a leitura. |
| R8-2 (médio): corpo e Accept/ContentType sem evidência | **Segue resolvido por decisão do analista** | `cfg_rest_accept`/`cfg_rest_content_type` vazias com TODO (Main.robin:70-77); TODO de formato do corpo (:201-206). |
| R8-3 (menor): seletor sem autenticação própria | **Segue resolvido por decisão do analista** | Main.robin:198-200; notas:36-38. |
| R8-4 (menor): falha HTTP passa em silêncio | **Segue resolvido por decisão do analista** | TODO em Main.robin:207-214, agora também cobrindo o 401 por prefixo errado; só erros declarados pela KB (PAD_Robin_ActionKB.json:52886-52892). Nenhum `ON ERROR` inventado. |
| R8-5 (menor): extensão dupla no caminho | **Segue resolvido** | `Path` sem extensão fixa (Main.robin:109); TODO em :46-49. |
| R8-6 (menor): esquema vazio gerava espaço duplo e falha silenciosa | **Resolvido** | `cfg_rest_auth_scheme` trocada por `cfg_rest_auth_prefix` (Main.robin:88), que guarda o esquema já com o espaço final; o cabeçalho junta prefixo e token sem espaço entre as duas expressões (Main.robin:216). Prefixo vazio resulta em token puro, sem espaço sobrando. As duas pendências ficaram amarradas: TODO do prefixo (:79-87) e TODO de R8-4 (:213-214) citam o 401. Mesma redação em notas:51-56, :72-73, :118 e README.md:62-64, :92-94. Nenhum nome antigo `cfg_rest_auth_scheme` restou em nenhum dos três arquivos. |
| R8-7 (menor): `ReadOnly: False` num flow que só lê | **Resolvido** | `ReadOnly: True` no step_01 (Main.robin:109), justificado em :104-107, notas:57-58 (decisão 7) e README.md:49-50. `ReadOnly` é `Boolean` obrigatório do mesmo seletor (PAD_Robin_ActionKB.json:14077-14081, :14102-14107): troca só de valor, seletor inalterado. |

## 1. Cobertura de caso de uso

Sem achado. Os 4 passos de UC-01 (`02-docs/use-cases.md:12-15`, main.json:1-4)
têm correspondente: step_01 (Main.robin:109), step_02 (:122), step_04
(:144-182, documentação da origem da credencial por decisão do analista),
step_03 (:216). O resultado esperado, chamada HTTP autenticada sem exposição da
credencial (`use-cases.md:16-18`), continua atendido estruturalmente. RN-01
(`business-rules.md:3-17`) não tem condicional: nada a virar `IF`. step_07 não
tem origem no legado e está documentado como diferença deliberada.

## 2. Densidade de `TODO reflow`

Sem achado. 10 comentários `# TODO reflow` (Main.robin:43, :53, :62, :70, :79,
:178, :201, :207, :231, :237). Dos 5 passos no escopo, **4 são ação real da
whitelist** (step_01, step_02, step_07, step_03); step_04 é comentário por
decisão do analista. Os 2 TODO de main.json:5-6 são esperados por ADR-028. Os
demais são `cfg_` não capturadas pela extração, formato do corpo e critério
HTTP: pendências do humano, não conversão incompleta.

Informativo (impeditivo de execução, não de conversão): as 10 `cfg_` continuam
vazias (Main.robin:50-51, :57-60, :68, :76-77, :88) e `in_rest_token` precisa
ser declarada no designer.

## 3. Convenções de nomenclatura

Sem achado. Passos: `step_01_open_excel_file`, `step_02_read_excel_range`,
`step_07_close_excel_file`, `step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre`,
`step_03_post_data_to_rest_api`, `step_05_out_of_scope_custom_package_transform`,
`step_06_out_of_scope_browser_unmapped_action`: todos no padrão
`step_NN_<verbo>_<objeto>` (robin-conventions.md:85). A numeração fora de ordem
física (07 antes de 04 e 03) é deliberada e explicada (Main.robin:33-39).
Variáveis: `cfg_excel_input_folder`, `cfg_excel_file_name`,
`cfg_excel_start_column`, `cfg_excel_start_row`, `cfg_excel_end_column`,
`cfg_excel_end_row`, `cfg_rest_endpoint_url`, `cfg_rest_accept`,
`cfg_rest_content_type`, `cfg_rest_auth_prefix`, `in_rest_token`,
`out_excel_instance`, `out_excel_data`, `out_rest_status_code`,
`out_rest_response`, `out_rest_response_headers`: prefixo correto, snake_case
minúsculo, nenhuma palavra reservada.

## 4. Consistência `notas-conversao.md` × `Main.robin`

Bate nos dois sentidos. As 4 ações de notas:18-21
(`Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`,
`Excel.ReadFromExcel.ReadCells`, `Excel.CloseExcel.Close`,
`Web.InvokeWebService.InvokeWebServicePost`) aparecem em Main.robin:109, :122,
:141, :216, com o mesmo nome de passo e o mesmo status. `**REGION` e `SET`
(notas:22-23) batem com as 4 Regiões (Main.robin:90, :144, :184, :219) e os 10
`SET` do topo. Nenhuma linha de ação do flow fica fora das notas.
`Credentials.GetCredential` só em comentário, como "nenhuma ação" (Main.robin:153-154;
notas:25-27). As decisões 5 a 7 (notas:46-58) estão refletidas no flow
exatamente como descritas.

### R4-2 (menor): README e notas não fecham R4-1 e a frase sobre o lint envelheceu

- README.md:88-90 diz que `fix-robin-eol` e `lint-robin` "precisam rodar de
  novo (orquestrador ou analista)". O chamador já rodou os dois, mais `scan` e
  `kb verify`, sem achados: a frase repete o padrão que originou R4-1 (status
  de pipeline escrito no README fica velho na rodada seguinte).
- A reescrita da seção "Teste" que resolve R4-1 não está registrada: README.md:88
  e notas:16, :60-79 citam só R3-1, R8-6 e R8-7 como tratados nesta rodada.
- Ação: conversor, numa nova rodada, registra R4-1 em "Achados da auditoria
  tratados" das notas e troca a frase do README por uma que não dependa do
  momento (por exemplo, "rodar `fix-robin-eol` e `lint-robin` depois de qualquer
  alteração", que é a regra de robin-conventions.md:74-76). Só documentação; não
  impede `reflow-test`.

## 5. Sinalização de subfluxo comum

Sem achado. step_04 corresponde à entrada `catalogado` `obter-credencial-do-cofre`
e mantém a sinalização completa: sufixo `_subfluxo_comum_obter_credencial_do_cofre`
(Main.robin:146), comentário com âncora, as duas evidências e a recomendação de
reuso (:165-176), Região `Subfluxo comum: Obter credencial do cofre (candidato a
reuso)` (:144), registro em notas:90-98. Nenhum candidato a novo subfluxo comum
declarado (notas:102), nenhuma entrada `proposto` sinalizada como `catalogado`.

## 6. Subflow padrão do PAD por nome de bot

Não aplicável. `dependencies` vazio (`01-inventory/inventory.json:34`); nenhum
`CALL`, nenhuma citação a `Log_Splunk`. Segue valendo a observação da rodada
anterior: se em produção o token não puder chegar por entrada do flow, o subflow
padrão ativo `ConsultarCredencialProducao` (subfluxos-comuns.md) é a alternativa
já padronizada.

## 7. Ação `proposto` / `colado KB` usada corretamente

Sem achado. Nenhuma ação `proposto`. Nas `colado KB`, os valores de exemplo
foram trocados por nomes do flow:

- step_01 (:109): `cfg_pasta_arquivos_entrada`/`cfg_numero_base` e o `.xlsx`
  fixo do snippet validado (robin-actions.md:207) viraram
  `cfg_excel_input_folder`/`cfg_excel_file_name`; nada do `golden_example` da KB
  (caminho de teste, senhas de exemplo) foi copiado.
- step_02 (:122) e step_07 (:141): `ExcelInstance`/`ExcelData` da KB viraram
  `out_excel_instance`/`out_excel_data`, que coincidem com o snippet validado
  pelo analista e são a instância real aberta no step_01.
- step_03 (:216): `$'''example'''` e o tipo de conteúdo de exemplo viraram
  `cfg_`/`in_`/`out_`; saídas da KB viraram `out_rest_*`.
- Nenhum `$'''example'''`, `ExcelInstance`, `ExcelData` ou caminho de teste da
  KB no flow.
- Status real declarado em todos os passos (:99-102, :120, :139, :193).

## 8. Semântica contra a KB

Sem achado. Seletores conferidos e inalterados desde a rodada anterior:

- step_01: `Excel.open` para `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`;
  os 4 `required_params` presentes (PAD_Robin_ActionKB.json:14102-14107),
  `ReadOnly` agora `True`.
- step_02: atributo `range` para `Excel.ReadFromExcel.ReadCells` (intervalo),
  não `ReadCell` nem `ReadAllCells`.
- step_07: `Excel.CloseExcel.Close`, fecha sem salvar, coerente com abertura só
  leitura.
- step_03: `REST.post` para `Web.InvokeWebService.InvokeWebServicePost`
  (`Method: Post`); `required_params` presentes. O cabeçalho junta duas
  expressões adjacentes, coberto pela sonda V56-adjacent-vars citada pelo
  chamador.
- Recursos: Excel aberto (:109) e fechado (:141). Nenhum navegador ou banco no
  escopo.
- Erro em integração externa: o legado não tem tratamento observável; decisão
  no TODO de R8-4, com os erros declarados pela KB. Pendência legítima.

Observação (não é achado): o prefixo depende de um espaço final dentro de
`cfg_rest_auth_prefix`, invisível no campo de texto do designer. Ao preencher a
`cfg_`, o analista deve conferir que o espaço ficou; se sumir, o cabeçalho sai
com esquema e token colados e o destino responde 401, visível só em
`out_rest_status_code`. Vale um cenário de teste específico em `05-test/` (o
TODO de R8-4 já cita o caso). Sobre R8-7: com `ReadOnly: True`, uma parada entre
step_01 e step_07 ainda deixa o processo Excel aberto, mas sem travar o arquivo
para escrita; sem tratamento de erro no legado, fica como está.

## Conclusão

- Os 12 achados anteriores seguem tratados: **R1-1, R3-1, R5-1, R7-1, R8-1,
  R8-5, R8-6, R8-7 resolvidos**; **R8-2, R8-3, R8-4 resolvidos por decisão do
  analista**, com pendência legítima em `# TODO reflow`; **R4-1 resolvido no
  essencial**, com resíduo documental em R4-2.
- 1 achado novo, **menor** e não bloqueante: R4-2 (README e notas não registram
  R4-1 e a frase sobre rerodar o lint envelheceu).
- Nenhuma ação inventada, nenhum valor de exemplo da KB, nenhum segredo literal,
  escopo de ADR-028 respeitado.
- **Pronto para `reflow-test`** no sentido de gerar `05-test/` (cenários e
  estrutura PASS/FAIL vazia, sem execução). **Não está pronto para executar** no
  designer até o analista declarar `in_rest_token` (sensível), preencher as 10
  `cfg_` vazias e decidir formato do corpo, prefixo de autorização e critério de
  status HTTP. Os cenários devem cobrir 401 por prefixo errado ou sem o espaço
  final e corpo em formato inesperado.
- Esta auditoria não aprova nem bloqueia: o checkpoint continua com o analista
  humano.
