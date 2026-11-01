# uc-01-excel-vault

Flow Robin convertido a partir do projeto A360 `a360-excel-vault`, escopo
**somente a parte confirmada** do fluxo aprovada no checkpoint humano —
`Excel/open` → `Excel/read` → `REST/post` (autenticado por
`CredentialVault/get`) — conforme `01-inventory/inventory.json:2-49`,
`02-docs/use-cases.md` (UC-01) e `02-docs/process-flow.md` (passos 1–4).

Os dois comandos não reconhecidos pela extração — `CustomPackage/transform`
(`main.json:5`) e `Browser/unmappedAction` (`main.json:6`), registrados em
`01-inventory/inventory.json:54-69` — **não fazem parte deste flow**:
ficaram explicitamente fora do escopo aprovado no checkpoint, conforme
**ADR-028** (`docs/decisions.md`) e o veredito `PARTIAL` em
`output/a360-excel-vault/03-classification/classification.md`. Eles
aparecem em `Main.robin` só como comentário/`TODO reflow` dentro da Região
"Fora do escopo aprovado (ADR-028)", para manter a sequência do processo
legível — nunca como se tivessem sido convertidos.

## Origem

- Projeto: `a360-excel-vault` (origem A360, `00-manifest.json`).
- Caso de uso: `UC-01` — "Envio de dados de planilha Excel para sistema
  externo autenticado por credencial do cofre" (`02-docs/use-cases.md`),
  restrito à parte confirmada do fluxo.
- Classificação: `PARTIAL` (`03-classification/classification.md`), com
  segunda opinião concordante (`03-classification/review.md`).
- Checkpoint humano: aprovado, registrado em
  `output/a360-excel-vault/00-manifest.json` → `checkpoint`
  (`decision: "approved"`, `recorded_at: 2026-10-31T01:55:17Z`). Escopo
  exato da aprovação (somente Excel + REST + CredentialVault) documentado em
  **ADR-028** (`docs/decisions.md`), porque o manifesto hoje não tem campo
  próprio para registrar um escopo parcial.

## Passo a passo convertido

1. **step_01_open_excel_file** — abre a planilha Excel de entrada
   (`main.json:1`, `Excel.open` → `Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess`,
   `[validado PAD: rodou]` em `reference/robin-actions.md`).
2. **step_02_read_excel_range** — lê o intervalo de dados da planilha
   (`main.json:2`, `Excel.read` → `Excel.ReadFromWorksheet`, variante
   "intervalo específico", `[não validado]` em `reference/robin-actions.md`
   — vira `TODO reflow` no `Main.robin`).
3. **step_03_post_data_to_rest_api** — envia os dados via requisição HTTP
   POST ao sistema externo (`main.json:3`, `REST.post` →
   `Web.InvokeRestApi`, `[não validado]` — vira `TODO reflow`).
4. **step_04_get_credential_subfluxo_comum_obter_credencial_do_cofre** —
   obtém a credencial no Cofre de Credenciais (`main.json:4`,
   `CredentialVault.get` → `Credentials.GetCredential`, `[não validado]` —
   vira `TODO reflow`), nunca o valor bruto, só a referência
   (`main.json:4:credential-vault`).

Os passos estão organizados em `FlowControl.Region` (status `[não
validado]` na whitelist, por isso cada abertura/fechamento de Região também
é um `TODO reflow`, nunca sintaxe inventada):

- "Leitura da Base de Entrada" — steps 1–2.
- "Envio de Dados ao Sistema Externo (REST)" — step 3.
- "Subfluxo comum: Obter credencial do cofre (candidato a reuso)" — step 4.
- "Fora do escopo aprovado (ADR-028)" — comandos 5 e 6, não convertidos.

## Subfluxo comum sinalizado

O **step_04** corresponde à entrada `obter-credencial-do-cofre`, catalogada
(status `catalogado`, evidência de 2 projetos) em
`reference/subfluxos-comuns.md`. A própria evidência observada ali já cita
este projeto (`a360-excel-vault/input/main.json:4`), antes de uma chamada
`REST.post` (`main.json:3`). Recomendação registrada no catálogo: extrair
para um subflow compartilhado (ex.: `Subflow_ObterCredencialDoCofre`) que
recebe `cfg_credential_reference` como entrada e devolve `out_credential`,
em vez de repetir `Credentials.GetCredential` isolado a cada conversão que
precise de credencial do cofre antes de uma ação autenticada.

Não há dependência `TaskBot.run`/`Flow.RunSubflow` neste projeto —
`dependencies` está vazio em `01-inventory/inventory.json:34` — então essa
sinalização é exclusivamente do catálogo de padrões repetidos entre
processos, não de uma chamada explícita do legado.

## Pendências antes de rodar no designer

- **A4** (`02-docs/risks.md`): `CredentialVault.get` precisa de um plano de
  migração da credencial para o Credential Manager do PAD antes de montar
  `step_04`.
- Valores reais dos atributos `file` (`main.json:1`), `range` (`main.json:2`)
  e a URL de destino de `REST.post` (`main.json:3`) não foram capturados
  pela extração determinística (`01-inventory/inventory.json`,
  `02-docs/data-sources.md`, `02-docs/integrations.md`) — confirmar com um
  analista antes de preencher `cfg_excel_input_folder`,
  `cfg_excel_file_name`, `cfg_excel_range` e `cfg_rest_endpoint_url`.
- `reference/a360-to-pad.md`: a linha "Excel | open" e a linha "Excel |
  read" têm observação explícita de que não está confirmado se o
  `packageName` simples `Excel` (sem "avançado") deste projeto é o mesmo
  pacote AA360 cuja ação PAD foi validada — reavaliar quando houver um
  export real.
- `reference/a360-to-pad.md`: nenhuma sub-ação real de
  `Excel.ReadFromExcel` para intervalo específico (`Start
  column`/`Start row`/`End column`/`End row`) tem evidência direta ainda —
  `step_02` segue `TODO reflow` até confirmação.
- **A1** (`02-docs/risks.md`): `Browser/unmappedAction` (`main.json:6`,
  fora do escopo) pode depender de extensão de navegador específica — só
  relevante se, em revisão futura, esse comando entrar em escopo de
  conversão.

## Comandos fora do escopo aprovado (ADR-028)

`CustomPackage/transform` (`main.json:5`) e `Browser/unmappedAction`
(`main.json:6`) não têm ação PAD mapeada em `reference/a360-to-pad.md`
("sem equivalente" / "pendente de classificação") e estão explicitamente
fora do checkpoint aprovado (`ADR-028`, `docs/decisions.md`). Eles aparecem
em `Main.robin` apenas como `TODO reflow` dentro da Região "Fora do escopo
aprovado (ADR-028)", só para manter a sequência do processo legível —
requerem revisão humana e uma nova entrada na tabela verdade antes de
qualquer conversão futura.

## Teste

Nenhum teste foi executado no PAD ainda. A fase `05-test/` deste projeto
ainda não existe (nunca chegou a essa fase do pipeline) — não há teste
desatualizado a avisar. Antes de gerar `05-test/`, um analista precisa
montar no designer e validar (`[validado PAD: rodou]`) as ações hoje `[não
validado]`: `Excel.ReadFromWorksheet` (variante intervalo específico),
`Web.InvokeRestApi`, `Credentials.GetCredential` e `FlowControl.Region` —
ver `reference/robin-actions.md` → "Como promover uma ação".
