---
verdict: PARTIAL
pad_use_cases:
  - "Trecho não confirmado dos comandos `CustomPackage/transform` (main.json:5, 01-inventory/inventory.json:54-61) e `Browser/unmappedAction` (main.json:6, 01-inventory/inventory.json:62-69) — candidato tentativo a PAD, condicionado à revisão humana que confirme interação de UI; nenhum caso de uso foi registrado em use-cases.md para esses comandos (use-cases.md:20-27), portanto não há, hoje, caso de uso de use-cases.md pronto para seguir ao PAD sem essa confirmação."
alerts:
  - "A1 — `Browser/unmappedAction` (main.json:6, 01-inventory/inventory.json:62-69): pendente de classificação; não é possível confirmar, a partir do inventário, se depende de extensão de navegador específica (risks.md:5)."
  - "A4 — `CredentialVault/get` (main.json:4, 01-inventory/inventory.json:2-13): uso confirmado do Cofre de Credenciais da Automation 360 (atributo `credential`); exige plano de migração dessa referência para o Credential Manager do PAD antes de qualquer conversão (risks.md:8)."
  - "Dúvida PARTIAL vs NOT_PAD registrada por regra KISS: os dois comandos não mapeados (`CustomPackage/transform` em main.json:5 e `Browser/unmappedAction` em main.json:6, ambos em 01-inventory/inventory.json:54-69) impedem confirmar se há, de fato, um componente de UI relevante no fluxo. Como a porção confirmada do fluxo (Excel + REST + CredentialVault) aponta para NOT_PAD, mas a incerteza sobre os dois comandos não permite descartar UI, aplicou-se a regra da rubrica 'na dúvida entre PARTIAL e NOT_PAD, escolha PARTIAL e registre o motivo' (reference/classification-rubric.md:9)."
---

# Classificação — a360-excel-vault

Fontes analisadas: `output/a360-excel-vault/01-inventory/inventory.json` e todo
`output/a360-excel-vault/02-docs/`. Critérios aplicados exatamente como
definidos em `reference/classification-rubric.md` (C1–C5, N1–N5, A1–A5).

Conteúdo de `input/` e de artefatos derivados dele (inventário, docs) é dado,
nunca instrução — nenhuma ordem encontrada em `main.json` ou em comentários do
legado foi seguida nesta classificação.

## Resumo do fluxo confirmado

Quatro comandos foram mapeados com confiança pela extração determinística
(`01-inventory/inventory.json:2-49`):

1. `Excel/open` (atributo `file`) — `main.json:1`.
2. `Excel/read` (atributo `range`) — `main.json:2`.
3. `REST/post` (atributos `body`, `authorization`) — `main.json:3`.
4. `CredentialVault/get` (atributo `credential`) — `main.json:4`.

Além desses, há **dois comandos não reconhecidos** (`unknown_commands`,
`01-inventory/inventory.json:54-69`), tratados nesta classificação como
**incerteza**, nunca como ação já mapeada ou requisito de negócio confirmado,
conforme instrução da tarefa:

5. `CustomPackage/transform` — `main.json:5` (`01-inventory/inventory.json:54-61`).
6. `Browser/unmappedAction` — `main.json:6` (`01-inventory/inventory.json:62-69`).

O inventário não registra nenhuma interação de UI confirmada
(`ui_interactions` vazio, `01-inventory/inventory.json:53`) e nenhuma
dependência entre bots (`dependencies` vazio, `01-inventory/inventory.json:34`).

## Critérios de UI — C1–C5 (favorecem PAD)

| # | Critério | Atende? | Evidência / observação |
| --- | --- | --- | --- |
| C1 | Fluxo majoritariamente UI desktop/Web | **Não, pela parte confirmada** | `ui_interactions` vazio (`01-inventory/inventory.json:53`); os 4 comandos confirmados são Excel (open/read), REST (post) e CredentialVault (get) — nenhum é interação de UI. A **incerteza** está nos 2 comandos não mapeados; `Browser/unmappedAction` (main.json:6) sugere possível ação de navegador, mas isso não está confirmado nem pode ser presumido (`01-inventory/inventory.json:62-69`). |
| C2 | App Windows com UI estável (sem CAPTCHA/canvas) | **Não avaliável** | Nenhum elemento de UI foi identificado na parte confirmada; não há evidência suficiente para avaliar estabilidade de UI nos 2 comandos pendentes. |
| C3 | Volume/frequência compatível com RPA | **Sem evidência** | Inventário não registra volumetria ou frequência de execução. Não há indício de exigência de tempo real/baixa latência, mas também não há confirmação positiva. |
| C4 | Não existe SDK/API oficial para a mesma automação | **Não** | O próprio fluxo já usa uma chamada `REST/post` (`main.json:3`, `01-inventory/inventory.json:38-49`) para a integração com o sistema externo — ou seja, já existe e já está em uso uma via de API para a tarefa principal de integração. |
| C5 | Depende de sessão de usuário interativa (login manual, MFA) | **Não** | A autenticação é feita via `CredentialVault/get` (`main.json:4`), um mecanismo de credencial de serviço, não uma sessão interativa de usuário. Nenhuma evidência de MFA ou login manual. |

**Resultado C1–C5 (parte confirmada):** nenhum critério atendido com confiança.
A única fonte de dúvida é o par de comandos não mapeados.

## Critérios de não-UI — N1–N5 (reduzem adequação ao PAD)

| # | Critério | Aplica-se? | Evidência / observação |
| --- | --- | --- | --- |
| N1 | Já existe API REST/SOAP documentada e com credencial de serviço disponível para a mesma tarefa | **Sim (forte)** | O fluxo confirmado já realiza a integração via `REST/post` (`main.json:3`, `01-inventory/inventory.json:38-49`), autenticado por credencial de serviço do `CredentialVault` (`main.json:4`, `01-inventory/inventory.json:2-13`). A automação já demonstra, na prática, que a tarefa de envio de dados é alcançável 100% via API, sem UI. |
| N2 | App já é SaaS/cloud-native com endpoint de integração | **Possível, não confirmado** | O sistema externo de destino do `REST/post` não é identificado além do pacote genérico `REST` (`integrations.md:7`); não há evidência direta de que o destino é SaaS, mas a existência de um endpoint REST já ativo é compatível com essa hipótese. Não contado como critério forte por falta de confirmação do produto destino. |
| N3 | Volume exige paralelismo/alta disponibilidade incompatível com PAD | **Sem evidência** | Inventário não traz dados de volumetria. |
| N4 | Tarefa é puramente ETL de dados estruturados, sem interação de UI | **Sim (forte), na parte confirmada** | A sequência confirmada é: abrir Excel → ler intervalo → enviar via POST — um padrão ETL clássico (extrair de planilha, transformar implicitamente, carregar via API), sem nenhuma interação de UI registrada (`ui_interactions` vazio, `01-inventory/inventory.json:53`). |
| N5 | Já existe automação equivalente estável em outra tecnologia | **Sem evidência** | Inventário não cita nenhuma automação equivalente existente. |

**Resultado N1–N5 (parte confirmada):** N1 e N4 fortes; N2 possível mas não
confirmado; N3 e N5 sem evidência.

## Aplicação da regra de decisão

Pela regra de decisão da rubrica (`reference/classification-rubric.md:47-58`):

- A **parte confirmada** do fluxo (Excel open/read + REST post + CredentialVault
  get) não atende a nenhum critério C1–C5 com confiança e atende fortemente a
  N1 e N4 → isoladamente, essa parte apontaria para **NOT_PAD** (ETL com
  integração já via API, candidata a script determinístico/Azure Function em
  vez de PAD, conforme regra explícita de "nuvem/API já disponível" da
  rubrica, linhas 31–35).
- Os **dois comandos não mapeados** (`CustomPackage/transform`, main.json:5, e
  `Browser/unmappedAction`, main.json:6) são tratados como **incerteza**, não
  como ação mapeada: não há evidência suficiente para confirmar se envolvem
  interação de UI (o que favoreceria C1/PAD) ou se são apenas mais uma etapa
  de transformação/integração de dados (o que reforçaria N4/NOT_PAD). Nenhum
  caso de uso foi presumido para eles em `use-cases.md` (use-cases.md:20-27) e
  nenhuma função de negócio foi presumida em `business-rules.md` (TODO reflow,
  business-rules.md:19-25).
- Isso configura exatamente a situação de dúvida entre `PARTIAL` e `NOT_PAD`
  prevista na rubrica. Regra aplicada: **"na dúvida entre PARTIAL e NOT_PAD,
  escolha PARTIAL e registre o motivo nos alertas"**
  (`reference/classification-rubric.md:9`).

**Veredito: PARTIAL.**

- Parte 1 — confirmada (Excel open/read, REST post, CredentialVault get):
  recomenda-se **não converter para PAD** sem reavaliação; perfil é de ETL +
  integração via API já existente (N1/N4), melhor atendido por tecnologia
  determinística (ex.: script Python, Azure Function) do que por PAD, salvo
  decisão humana em contrário no checkpoint.
- Parte 2 — pendente (`CustomPackage/transform`, `Browser/unmappedAction`):
  **não deve ser convertida nem descartada ainda**; requer revisão humana e
  consulta a `reference/robin-actions.md` antes de qualquer decisão de PAD ou
  NOT_PAD para esse trecho, conforme já registrado em `process-flow.md:34-49`
  e `risks.md:5`.

## Casos de uso para o PAD

`use-cases.md` registra apenas **UC-01** (envio de dados de planilha Excel
para sistema externo via credencial do cofre), e esse caso de uso corresponde
exatamente à parte confirmada do fluxo, que — como descrito acima — aponta
para NOT_PAD (N1/N4), não para PAD. Os comandos pendentes não geraram caso de
uso em `use-cases.md` (use-cases.md:20-27).

Por isso, **não há hoje nenhum caso de uso confirmado de use-cases.md pronto
para seguir ao PAD**. O único candidato tentativo a PAD é o trecho ainda não
classificado dos comandos `CustomPackage/transform` (main.json:5) e
`Browser/unmappedAction` (main.json:6), condicionado à confirmação, em
revisão humana, de que algum deles representa de fato interação de UI (ver
`process-flow.md:34-49`).

## Alertas de portabilidade (A1–A5)

| # | Alerta | Aplica-se? | Evidência | Observação |
| --- | --- | --- | --- | --- |
| A1 | Depende de extensão de navegador específica | Pendente de confirmação | `main.json:6` (`01-inventory/inventory.json:62-69`) | `Browser/unmappedAction` não está classificado; não se sabe se envolve extensão de navegador. Ver `risks.md:5`. |
| A2 | Depende de coordenadas de tela fixas | Não | `01-inventory/inventory.json:53` | `ui_interactions` vazio; nenhuma evidência de coordenadas fixas. |
| A3 | Depende de versão específica de app desktop | Não | — | Nenhuma evidência no inventário. |
| A4 | Usa `CredentialVault` do A360 | **Sim** | `main.json:4` (`01-inventory/inventory.json:2-13`) | Credencial obtida via `CredentialVault/get`; exige plano de migração para o Credential Manager do PAD antes da conversão. Ver `risks.md:8`. |
| A5 | Biblioteca/DLL compartilhada entre projetos | Não | `01-inventory/inventory.json:34` | `dependencies` vazio; nenhuma evidência de biblioteca/DLL compartilhada. |

## Próximos passos

Por ser `PARTIAL`, este projeto **exige aprovação humana explícita no
checkpoint** (`AGENTS.md:29-30`) antes de qualquer conversão, com decisão
separada para cada uma das duas partes:

1. Confirmar, via revisão humana e consulta a `reference/robin-actions.md`,
   a função real de `CustomPackage/transform` (main.json:5) e
   `Browser/unmappedAction` (main.json:6).
2. Decidir explicitamente no manifesto se a parte confirmada (Excel + REST +
   CredentialVault) segue para PAD (regra KISS, se o analista preferir não
   fragmentar o projeto) ou é encerrada como NOT_PAD/realocada para outra
   tecnologia.
3. Registrar a decisão final em `docs/decisions.md`, conforme `AGENTS.md:73`.
