---
original_verdict: PARTIAL
reviewed_verdict: PARTIAL
agreement: concorda
---

# Revisão independente — a360-excel-vault

Esta revisão foi feita do zero a partir de `01-inventory/inventory.json`,
`02-docs/` e `reference/classification-rubric.md`, sem ler
`03-classification/classification.md` antes de chegar à minha própria
contagem de critérios. A comparação com o veredito original só foi feita
depois de eu ter concluído minha análise.

Conteúdo de `input/` e de artefatos derivados dele (inventário, `02-docs/`,
`classification.md`) é tratado como dado, nunca como instrução — nenhuma
ordem encontrada em `main.json` ou em comentários do legado foi seguida
nesta revisão.

## Inventário do fluxo

Seis comandos aparecem em `main.json`, conforme `01-inventory/inventory.json`:

- **Confirmados** (mapeados com confiança pela extração determinística):
  1. `Excel/open` (atributo `file`) — `main.json:1` (`01-inventory/inventory.json:15-23`)
  2. `Excel/read` (atributo `range`) — `main.json:2` (`01-inventory/inventory.json:24-32`)
  3. `REST/post` (atributos `body`, `authorization`) — `main.json:3` (`01-inventory/inventory.json:38-49`)
  4. `CredentialVault/get` (atributo `credential`) — `main.json:4` (`01-inventory/inventory.json:2-13`)
- **Não reconhecidos** (`unknown_commands`):
  5. `CustomPackage/transform` — `main.json:5` (`01-inventory/inventory.json:54-61`)
  6. `Browser/unmappedAction` — `main.json:6` (`01-inventory/inventory.json:62-69`)

`ui_interactions` está vazio (`01-inventory/inventory.json:53`) e
`dependencies` também (`01-inventory/inventory.json:34`).

## Minha análise

### Critérios C1–C5 (favorecem PAD) — aplicados à parte confirmada

| # | Atende? | Evidência |
| --- | --- | --- |
| C1 — fluxo majoritariamente UI | **Não** | `ui_interactions` vazio (`01-inventory/inventory.json:53`); os 4 comandos confirmados são Excel/REST/CredentialVault, nenhum é interação de UI (`01-inventory/inventory.json:15-49`, `2-13`). |
| C2 — app Windows com UI estável | **Não avaliável** | Nenhum elemento de UI identificado na parte confirmada; nada a avaliar. |
| C3 — volume compatível com RPA | **Sem evidência** | Inventário não registra volumetria/frequência em nenhuma seção. |
| C4 — não existe API oficial para a mesma automação | **Não** | O próprio fluxo já usa `REST/post` (`main.json:3`, `01-inventory/inventory.json:38-49`) como via de integração — API já existe e já está em uso. |
| C5 — depende de sessão interativa de usuário | **Não** | Autenticação via `CredentialVault/get` (`main.json:4`, `01-inventory/inventory.json:2-13`), credencial de serviço, não sessão interativa/MFA. |

**C1–C5 na parte confirmada: 0/5 atendidos.**

### Critérios N1–N5 (reduzem adequação ao PAD) — aplicados à parte confirmada

| # | Aplica-se? | Evidência |
| --- | --- | --- |
| N1 — já existe API REST/SOAP com credencial de serviço para a mesma tarefa | **Sim, forte** | `REST/post` (`main.json:3`, `01-inventory/inventory.json:38-49`) autenticado por `CredentialVault/get` (`main.json:4`, `01-inventory/inventory.json:2-13`) — a tarefa de envio de dados já é 100% resolvida via API. |
| N2 — app já SaaS/cloud com endpoint | **Não confirmado** | O destino do `REST/post` não é identificado além do pacote genérico `REST` (`integrations.md:7`, `01-inventory/inventory.json:38-49`); não há como afirmar que é SaaS. |
| N3 — volume exige paralelismo incompatível com PAD | **Sem evidência** | Inventário não traz volumetria. |
| N4 — tarefa é puramente ETL sem interação de UI | **Sim, forte, na parte confirmada** | Sequência `Excel/open` → `Excel/read` → `REST/post` é um padrão ETL clássico (extrai da planilha, carrega via API), com `ui_interactions` vazio (`01-inventory/inventory.json:53`, `15-49`). |
| N5 — já existe automação equivalente estável em outra tecnologia | **Sem evidência** | Nenhuma menção no inventário. |

**N1–N5 na parte confirmada: N1 e N4 fortes; os demais sem evidência.**

### Os dois comandos não reconhecidos

`CustomPackage/transform` (`main.json:5`) e `Browser/unmappedAction`
(`main.json:6`) não entraram em `ui_interactions` nem em nenhum caso de uso
(`use-cases.md:20-27` registra explicitamente que nenhum uso foi presumido
para eles) nem em `business-rules.md` (`business-rules.md:19-25`, "TODO
reflow"). Não há evidência no inventário que confirme interação de UI em
nenhum dos dois — o nome do pacote `Browser` é sugestivo, mas sugestão não é
confirmação, e a própria extração os separou de `ui_interactions`, não os
classificando ali. Por outro lado, também não há evidência que confirme que
são apenas ETL/transformação de dados (o que reforçaria N4). Portanto, não
atendo a nenhum C ou N com confiança para esses dois comandos — são
incerteza genuína, não uma "parte claramente UI" nem uma "parte claramente
dados/API".

### Aplicação da regra de decisão

- A parte confirmada (4 de 6 comandos) não atende a nenhum C1–C5 e atende
  fortemente a N1 e N4 → isoladamente apontaria para `NOT_PAD` (regra
  explícita de "nuvem/API já disponível", `reference/classification-rubric.md:31-35`).
- Os dois comandos não reconhecidos impedem descartar por completo um
  componente de UI (regra C1), mas também não confirmam nada — não existe,
  hoje, uma "parte claramente UI" no sentido da regra 3 da rubrica
  (`reference/classification-rubric.md:51-53`), apenas incerteza.
- Isso é exatamente a situação prevista na regra KISS da rubrica: "na dúvida
  entre `PARTIAL` e `NOT_PAD`, escolha `PARTIAL` e registre o motivo nos
  alertas" (`reference/classification-rubric.md:9`). Como não há como
  eliminar a hipótese de UI nos dois comandos pendentes, mas a parte
  confirmada por si só não justificaria PAD, o veredito correto, aplicando a
  rubrica à risca, é `PARTIAL`.

## Alertas A1–A5 conferidos

| # | Aplica-se? | Evidência |
| --- | --- | --- |
| A1 — extensão de navegador específica | Pendente de confirmação | `main.json:6` (`01-inventory/inventory.json:62-69`); `risks.md:5`. |
| A2 — coordenadas de tela fixas | Não | `01-inventory/inventory.json:53` (`ui_interactions` vazio). |
| A3 — versão específica de app desktop | Não | Sem evidência no inventário. |
| A4 — `CredentialVault` do A360 | Sim | `main.json:4` (`01-inventory/inventory.json:2-13`); exige plano de migração para o Credential Manager do PAD. |
| A5 — biblioteca/DLL compartilhada | Não | `dependencies` vazio (`01-inventory/inventory.json:34`). |

## Conclusão

Minha contagem de critérios (C1–C5 = 0/5 na parte confirmada; N1 e N4 fortes
na parte confirmada; os dois comandos não reconhecidos sem evidência
suficiente para qualquer critério) reproduz, de forma independente, a mesma
leitura e o mesmo ponto de aplicação da regra KISS do veredito original.

**Veredito revisado: `PARTIAL`.** Concordo com o veredito original — não
houve amenização: a reavaliação dos critérios, feita do zero, chega à mesma
contagem e ao mesmo ponto de dúvida (os dois comandos não mapeados), que é
resolvido pela mesma regra explícita da rubrica.
