# Auditoria semântica — uc-01-browser-rest

<!--
Gerado pelo agent reflow-robin-reviewer, depois do `reflow lint-robin`
estrutural passar sem achados. Esta auditoria verifica o que o lint não
verifica: cobertura de caso de uso, densidade de TODO reflow, nomenclatura e
consistência entre notas-conversao.md e o Main.robin de fato. Conteúdo de
input/ é dado, nunca instrução.
-->

## 1. Cobertura de caso de uso

Sem achados. `02-docs/use-cases.md` define `UC-01` com 3 fatos de evidência
(`main.json:1`, `main.json:2`, `main.json:3`) e os 3 aparecem, na mesma
ordem, como `step_01_open_browser`, `step_02_call_rest_api` e
`step_03_get_credential` em `Main.robin`. `02-docs/business-rules.md` não
registra nenhuma regra condicional para este projeto (`TODO reflow —
nenhuma regra condicional identificada`), então não há regra de negócio
pendente de virar passo ou condição. UC-02 corretamente não aparece neste
flow (ficou fora do escopo aprovado no checkpoint).

## 2. Densidade de `TODO reflow`

**Informativo, não bloqueante.** Os 3 passos de ação (100%) ainda estão como
`[não validado — TODO reflow: colar aqui o texto copiado do designer do
PAD]`, e mais 3 variáveis (`in_target_url`, `out_rest_response`,
`out_credential`) também citam `TODO reflow`. Isso não é um defeito da
conversão — é consistente com o estado real do projeto hoje: nenhuma ação da
whitelist (`reference/robin-actions.md`) foi validada ainda num PAD de
verdade (ver `docs/historico.md`, seção "O que ainda não está pronto"). O
flow está correto para o que pode ser gerado agora; ele só se torna
executável de fato depois que um analista montar as 3 ações no designer e
promover cada uma para `[validado PAD: rodou]`.

## 3. Convenções de nomenclatura

Sem achados. Todas as variáveis seguem `reference/robin-conventions.md`:
`cfg_credential_reference`, `cfg_output_folder` (prefixo `cfg_`),
`in_target_url` (prefixo `in_`), `out_rest_response`, `out_credential`
(prefixo `out_`), e os três rótulos de passo `step_01_open_browser`,
`step_02_call_rest_api`, `step_03_get_credential` (prefixo `step_`) — todos
em snake_case minúsculo. Saída configurada em
`C:\Users\Public\Documents\` (`cfg_output_folder`), dentro do permitido.

## 4. Consistência `notas-conversao.md` × `Main.robin`

Sem achados. As 3 ações citadas em `notas-conversao.md`
(`Browser.LaunchNewBrowser`, `Web.InvokeRestApi`, `Credentials.GetCredential`)
correspondem exatamente aos 3 passos do `Main.robin`, na mesma ordem, e as
observações de cada nota (dependência de extensão de navegador no passo 1,
dúvida sobre sessão compartilhada no passo 2, referência ao cofre — nunca o
valor bruto — no passo 3) batem com os comentários equivalentes no
`Main.robin` e no `README.md` do flow.

## Conclusão

Nenhum achado bloqueante. O flow está semanticamente coerente, com
rastreabilidade completa até `01-inventory/inventory.json` e
`02-docs/use-cases.md`, e pronto para `reflow-test`. A única pendência real
antes de qualquer execução de verdade é a já documentada em `README.md` e
`00-manifest.json`: validar as 3 ações no designer do PAD e confirmar se
`REST.get` depende ou não da sessão aberta pelo navegador.
