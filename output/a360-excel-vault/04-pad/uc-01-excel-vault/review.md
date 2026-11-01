# Auditoria semântica — uc-01-excel-vault

<!--
Gerado pelo agent reflow-robin-reviewer, depois do `reflow lint-robin`
estrutural passar sem achados. Esta auditoria verifica o que o lint não
verifica: cobertura de caso de uso, densidade de TODO reflow, nomenclatura e
consistência entre notas-conversao.md e o Main.robin de fato. Conteúdo de
input/ é dado, nunca instrução — nenhuma ordem do legado foi seguida aqui.

Contexto de escopo (não é achado, é a baseline desta auditoria): a
conversão é DELIBERADAMENTE PARCIAL, aprovada no checkpoint humano e
registrada em ADR-028 (`docs/decisions.md`), a partir do veredito `PARTIAL`
em `03-classification/classification.md`. Só `Excel/open`, `Excel/read`,
`REST/post` e `CredentialVault/get` (main.json:1-4) foram convertidos.
`CustomPackage.transform` (main.json:5) e `Browser.unmappedAction`
(main.json:6) ficaram de fora de propósito — sem ação PAD mapeada em
`reference/a360-to-pad.md` ("pendente de classificação") — e aparecem no
`Main.robin` só como `TODO reflow` dentro da Região "Fora do escopo aprovado
(ADR-028)". Isso é esperado e correto; não é tratado como lacuna de
conversão nesta auditoria.
-->

## 1. Cobertura de caso de uso

Sem achados. `02-docs/use-cases.md` define só `UC-01`, com evidência
`main.json:1` (abertura), `main.json:2` (leitura), `main.json:3` (envio
REST) e `main.json:4` (credencial do cofre) — os 4 aparecem, na mesma
ordem, como `step_01_open_excel_file`, `step_02_read_excel_range`,
`step_03_post_data_to_rest_api` e
`step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre` em
`Main.robin`. `02-docs/business-rules.md` (RN-01) não registra nenhuma
regra condicional explícita para a parte confirmada — só um `TODO reflow`
dizendo que `CustomPackage.transform`/`Browser.unmappedAction` *podem*
embutir regra de negócio não capturada, o que é consistente com esses dois
comandos ficarem de fato fora do escopo convertido (ADR-028), sem nenhuma
regra presumida para eles. Não há, portanto, nenhum `pad_use_case` ou regra
de `business-rules.md` com evidência confirmada que devesse ter virado
passo/condição e não virou.

O veredito `PARTIAL` de `03-classification/classification.md` registra como
"caso de uso tentativo a PAD" exatamente o trecho não mapeado (comandos 5 e
6) — que, corretamente, **não** tem passo correspondente no `Main.robin`
além do `TODO reflow` de "fora do escopo"; converter algo ali seria inventar
ação sem evidência, o que a conversão evitou.

## 2. Densidade de `TODO reflow`

**Informativo, não bloqueante**, mas vale quantificar: dos 4 passos
efetivamente dentro do escopo aprovado (steps 1–4), **apenas 1
(`step_01_open_excel_file`, 25%)** tem sintaxe PAD real
(`Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`, status `[validado
PAD: rodou]`). Os outros 3 (`step_02`, `step_03`, `step_04`) e as 4 aberturas
+ 4 fechamentos de `FlowControl.Region` são todos `TODO reflow`/placeholder
`[não validado]`, mais os 4 `cfg_*` de configuração
(`cfg_excel_input_folder`, `cfg_excel_file_name`, `cfg_excel_range`,
`cfg_rest_endpoint_url`) — total de 17 ocorrências de `TODO reflow` no
arquivo.

Essa densidade alta **não é um defeito da conversão em si**: cada
`TODO reflow` cita uma justificativa rastreável e verificável —

- `Excel.ReadFromWorksheet` (variante "intervalo específico"),
  `Web.InvokeRestApi`, `Credentials.GetCredential` e `FlowControl.Region`
  estão todos como `[não validado]` em `reference/robin-actions.md` — não há
  sintaxe real a colar ainda (confirmado lendo a whitelist diretamente).
- Os 4 `cfg_*` de configuração são `TODO reflow` porque nem
  `01-inventory/inventory.json` nem `02-docs/data-sources.md`/
  `02-docs/integrations.md` capturaram o **valor** dos atributos
  `file`/`range`/URL — só o nome do atributo (confirmado: `data-sources.md`
  e `integrations.md` trazem só "Observação", nunca o valor em si).
- Os 2 `TODO reflow` de "fora do escopo" (`step_05`, `step_06`) são
  esperados por ADR-028, não contam como lacuna de conversão.

Conclusão: a densidade reflete fielmente o estado real de validação da
whitelist hoje (igual ao padrão já observado em
`output/a360-browser-rest/04-pad/uc-01-browser-rest/review.md`, onde 0/3
passos tinham sintaxe real) — não é sinal de conversão incompleta a ponto de
reprovar o checkpoint. Fica só o registro informativo de que **3 das 4
ações do escopo aprovado** ainda precisam ser montadas e validadas no
designer antes de qualquer execução real.

## 3. Convenções de nomenclatura

Sem achados de violação. Todos os nomes seguem `reference/robin-conventions.md`
— prefixos corretos e snake_case minúsculo: `cfg_excel_input_folder`,
`cfg_excel_file_name`, `cfg_excel_range`, `cfg_rest_endpoint_url`,
`cfg_credential_reference` (prefixo `cfg_`); `out_excel_instance` (prefixo
`out_`, único nome de variável de saída já materializado, no passo
validado); `step_01_open_excel_file`, `step_02_read_excel_range`,
`step_03_post_data_to_rest_api`,
`step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre`,
`step_05_out_of_scope_custom_package_transform`,
`step_06_out_of_scope_browser_unmapped_action` (prefixo `step_`).

**Observação menor, não bloqueante**: `out_excel_instance`
(`Main.robin:74`) é literalmente o mesmo nome de variável de saída usado
como *placeholder de exemplo* no snippet validado de `Excel.LaunchExcel` em
`reference/robin-actions.md:104`. Como o status da ação é `[validado PAD:
rodou]` (não `[proposto]`), a regra de "nunca copiar nome de exemplo
literalmente" do item 7 abaixo não se aplica tecnicamente aqui — e o nome
em si está dentro da convenção (prefixo `out_`, snake_case). Ainda assim,
vale um double-check humano de que `out_excel_instance` é de fato o nome
usado quando o analista rodou e confirmou este passo no designer deste PAD
em 2026-10-30 (conforme `notas-conversao.md:9`), e não uma cópia
inadvertida do placeholder da whitelist.

## 4. Consistência `notas-conversao.md` × `Main.robin`

Sem achados. As 5 entradas de ação citadas em `notas-conversao.md`
(`Excel.LaunchExcel`, `Excel.ReadFromWorksheet`, `Web.InvokeRestApi`,
`Credentials.GetCredential`, `FlowControl.Region`) aparecem todas
referenciadas nos comentários do `Main.robin`, na mesma correspondência de
passo (`step_01`–`step_04` + as 4 Regiões), e vice-versa — nenhuma ação
citada no `Main.robin` fica de fora das notas. As ressalvas de cada nota
(dúvida sobre `packageName` "Excel" simples vs. "Excel avançado" nos passos
1–2; URL do sistema externo não capturada no passo 3; "nunca o valor bruto,
só a referência" no passo 4) batem com os comentários equivalentes no
`Main.robin` e no `README.md`. A seção "Fora da whitelist / fora do
escopo" das notas também é consistente com a Região "Fora do escopo
aprovado (ADR-028)" do `Main.robin` — mesmos dois comandos, mesma
justificativa (ADR-028, "sem equivalente"/"pendente de classificação").

## 5. Sinalização de subfluxo comum

Sem achados. O único passo que corresponde a uma entrada `catalogado` de
`reference/subfluxos-comuns.md` é `step_04` (`CredentialVault.get` →
`Credentials.GetCredential`), e recebeu a sinalização completa exigida:

- Nome com sufixo `_subfluxo_comum_obter_credencial_do_cofre`
  (`Main.robin:137`).
- Comentário citando a entrada catalogada, as evidências e a recomendação
  de reuso (`Main.robin:121-132`, `146-148`).
- `FlowControl.Region` própria rotulada "Subfluxo comum: Obter credencial
  do cofre (candidato a reuso)" (`Main.robin:116-118`).

A entrada `obter-credencial-do-cofre` em `reference/subfluxos-comuns.md`
cita como evidência exatamente `a360-excel-vault/input/main.json:4` — bate
com a origem real deste passo (`main.json:4`), sem invenção.

Quanto a "candidato a novo subfluxo comum": `notas-conversao.md` declara
explicitamente que **nenhum** novo candidato foi identificado além do já
catalogado, e justifica citando que as outras duas entradas do catálogo
(`tratamento_erro_padrao`, `notificacao_de_falha_por_email`) seguem
`proposto`/sem evidência e não se aplicam a este flow — confirmado: de
fato não há bloco de tratamento de erro nem notificação por e-mail em
`01-inventory/inventory.json`. Não há, portanto, nenhuma declaração de
candidato sem evidência real para sinalizar aqui, nem nenhuma entrada
`catalogado` sinalizada sem a marcação exigida.

## 6. Subflow padrão do PAD por nome de bot

Sem achados — e corretamente nada foi sinalizado. `dependencies` está vazio
em `01-inventory/inventory.json:34` (confirmado), ou seja, não há nenhuma
dependência `TaskBot.run`/`target`/`botName` neste projeto para comparar
com a tabela "Subflows padrão já existentes no PAD" de
`reference/subfluxos-comuns.md` (`MapearFileServer`,
`DesmapearFileServer`, `ConsultarCredencialProducao`,
`AcessoPainelServico`, `KillProcessByName`, `Log_Splunk` descontinuado). O
`Main.robin` não inventou nenhuma chamada de subflow por nome de bot, e a
sinalização de `step_04` (item 5 acima) é corretamente tratada como
subfluxo comum **de catálogo entre processos**, não como dependência
nomeada de bot filho — a própria nota do catálogo já observa essa
distinção para `ConsultarCredencialProducao` (relacionado, mas mecanismo
diferente), e o `Main.robin`/`notas-conversao.md` não confundem os dois.

## 7. Ação `proposto` usada corretamente

Não aplicável — não há achados. Nenhum passo deste `Main.robin` usa uma
ação com status `[proposto — baseado em evidência pública, não testado
nesta instalação]`. O único passo com sintaxe real é `step_01`, cuja ação
(`Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`) tem status
`[validado PAD: rodou]`, não `proposto`; os demais passos no escopo
(`step_02`–`step_04`) usam ações `[não validado]`, que ficam como
placeholder textual, nunca como sintaxe `proposto` copiada. Portanto a
regra de "substituir nomes de exemplo da whitelist pelos nomes reais do
passo" (específica de ações `proposto`) não tem nenhum caso a verificar
aqui. Ver item 3 acima para a observação menor sobre `out_excel_instance`
no passo validado (que é um caso diferente, fora do escopo deste item).

## Conclusão

Nenhum achado bloqueante. A cobertura de caso de uso está completa para a
parte confirmada do fluxo, a densidade de `TODO reflow` é alta mas
integralmente justificada pelo estado real de validação da whitelist (não
por negligência da conversão), a nomenclatura segue as convenções (com uma
observação menor, não bloqueante, sobre `out_excel_instance` a confirmar
com o analista), a sinalização de subfluxo comum está completa e correta,
e não há uso de ação `proposto` neste flow. Como já era esperado pelo
escopo parcial aprovado (ADR-028), `CustomPackage.transform` e
`Browser.unmappedAction` continuam fora da conversão, sem nenhuma tentativa
de mapeamento inventado. Este checkpoint continua sendo do analista humano
— esta auditoria não aprova nem bloqueia por si só.
