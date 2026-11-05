# uc-01-browser-rest

Flow Robin convertido a partir do projeto A360 `a360-browser-rest`, escopo
**UC-01 apenas**: abertura de página no navegador, consulta REST autenticada (no legado, pela
credencial do Credential Vault; no PAD, pela entrada sensível `in_rest_token`) (`main.json:1`, `main.json:2`, `main.json:3`, via
`01-inventory/inventory.json` e `02-docs/use-cases.md`).

UC-02 (`TaskBot.run` → `Excel.read`, `main.json:4` / `child.json:1`) **não** faz parte
deste flow: ficou fora do escopo aprovado no checkpoint
(`output/a360-browser-rest/00-manifest.json` → `checkpoint`), conforme o veredito
`PARTIAL` em `output/a360-browser-rest/03-classification/classification.md`. Aparece no
`Main.robin` só como comentário na Região "Fora do escopo aprovado (UC-02)", sem `CALL`.

## Origem

- Projeto: `a360-browser-rest` (origem A360, `00-manifest.json`).
- Caso de uso: UC-01, "Consulta a serviço externo via navegador e REST com credencial
  do cofre" (`02-docs/use-cases.md`).
- Checkpoint humano: aprovado em `2026-10-21T16:44:33+00:00`
  (`00-manifest.json` → `checkpoint.approved_at`), escopo restrito a UC-01.

## Entradas do flow (declarar no designer)

- `in_target_url`: texto. URL aberta pelo step_01 (valor não capturado pela extração).
- `in_rest_token`: texto, marcada como **sensível**. Token usado no cabeçalho de
  autorização do step_02 (decisão do analista, 2026-11-05). Nunca valor no arquivo.

## Passo a passo convertido

Reconvertido em 2026-11-04 (ADR-029) e corrigido em 2026-11-05 a partir da auditoria
semântica (`review.md`) e das decisões do analista (ver `notas-conversao.md`, seção
"Decisões do analista").

Numeração: step_01 a step_04 ficam presos à ordem do legado (`main.json:1-4`; o 04 é o
`TaskBot.run`, fora do escopo). Passo sem origem no legado recebe o próximo número livre
(05). A ordem de execução segue as Regiões abaixo, não a numeração.

1. **step_01_open_browser**: abre a página no navegador (`main.json:1`, `Browser.open` →
   `WebAutomation.LaunchEdge.LaunchEdge`, `[colado KB: PAD 2.73, não rodado nesta
   instalação]`). Chrome, se for o navegador do legado: irmão
   `WebAutomation.LaunchChrome.LaunchChrome` (alerta A1).
2. **step_03_get_credential_subfluxo_comum_obter_credencial_do_cofre**: só documentação,
   sem ação. A credencial chega por `in_rest_token` (sem ação de cofre: a ação
   `Credentials.GetCredential` é `[não validado]` e não é id Robin real). Vem antes do
   REST porque a chamada depende dela (no legado, `main.json:3` vem depois de
   `main.json:2`). Sinalizado como subfluxo comum catalogado
   `obter-credencial-do-cofre` (`reference/subfluxos-comuns.md`), candidato a reuso.
3. **step_02_call_rest_api**: consulta o serviço externo (`main.json:2`, `REST.get` →
   `Web.InvokeWebService.InvokeWebService` com `Method: Web.Method.Get`, `[colado KB:
   PAD 2.73, não rodado nesta instalação]`). Independente da sessão do navegador, por
   decisão do analista. Autorização montada em `CustomHeaders` juntando
   `cfg_rest_auth_prefix` (esquema já com o espaço final, ou vazio) e `in_rest_token`,
   sem espaço entre os dois.
4. **step_05_close_browser**: fecha o navegador (`WebAutomation.CloseWebBrowser`,
   `[colado KB: PAD 2.73, não rodado nesta instalação]`). Diferença deliberada em
   relação ao legado, que não fecha o navegador.

Regiões, nesta ordem:

- "Abertura do Navegador": step_01.
- "Subfluxo comum: Obter credencial do cofre (candidato a reuso)": step_03.
- "Consulta ao Sistema Externo (REST)": step_02.
- "Encerramento": step_05.
- "Fora do escopo aprovado (UC-02)": step_04, só comentário, não convertido.

## Pendências antes de rodar no designer

- Valores que a extração não capturou (URL do endpoint, `Accept`/`ContentType`, prefixo
  de autorização) são `SET cfg_... TO $''''''` com `# TODO reflow` acima; o valor de
  `in_target_url` é informado na execução.
- Critério de status HTTP (`# TODO reflow` no step_02): com `FailOnErrorStatus: False`,
  4xx/5xx só aparecem em `out_rest_status_code`; nenhum `ON ERROR` foi inventado.
- **A1** (`02-docs/risks.md`): navegador do legado e extensão do PAD no ambiente, antes
  do step_01.
- **A4** (`02-docs/risks.md`): declarar `in_rest_token` como sensível; plano de origem
  da credencial em produção (step_03).

Lista completa em `notas-conversao.md` → "Pendências antes de rodar no designer".

## Teste

Nenhum teste foi executado no PAD ainda. Depois de qualquer alteração no `Main.robin`,
rodar `uv run python -m reflow fix-robin-eol a360-browser-rest` e
`uv run python -m reflow lint-robin a360-browser-rest` antes de colar (ver
`reference/robin-conventions.md`); o estado de cada rodada fica em `review.md` e no
histórico do repositório. O flow de teste (`05-test/`) precisa ser regenerado a partir
desta versão; gerá-lo não depende do designer, **executá-lo** depende: antes, um analista
precisa declarar `in_target_url` e `in_rest_token` (sensível) no designer, preencher as
`cfg_` pendentes e decidir o critério de status HTTP. Só a execução real promove as
ações usadas para `[validado PAD: rodou]` (ver `reference/robin-actions.md` → "Como
promover uma ação").
