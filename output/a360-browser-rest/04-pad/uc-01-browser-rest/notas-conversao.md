# Notas de conversão — uc-01-browser-rest

Ações Robin usadas em `Main.robin`, todas da whitelist
`reference/robin-actions.md`, com o id Robin real (ancorado na PAD Robin Action KB
vendorizada, ADR-029). Mapeamento de origem em `reference/a360-to-pad.md`. Escopo
restrito a UC-01 (`main.json:1-3`), aprovado no checkpoint
(`00-manifest.json:2-7`). Nenhuma ação abaixo está `[validado PAD: rodou]` ainda.

Reconvertido em 2026-11-04: a versão anterior não colava no PAD (comentários `//`,
linhas `cfg_x: "..."` e placeholders soltos derrubavam a colagem inteira) e usava nomes
que não existem no PAD (Browser.LaunchNewBrowser, Web.InvokeRestApi).

Corrigido em 2026-11-05 a partir da auditoria semântica
(`04-pad/uc-01-browser-rest/review.md`: R1-1, R4-1, R4-2, R5-1, R7-1, R8-1, R8-2, R8-3)
e das decisões do analista listadas abaixo.

- `WebAutomation.LaunchEdge.LaunchEdge` — step_01_open_browser; equivalente a `Browser.open` (`main.json:1`); status `[colado KB: PAD 2.73, não rodado nesta instalação]`; depende da extensão do PAD no navegador do ambiente (alerta A1 em `02-docs/risks.md`); se o legado usar Chrome, trocar pelo irmão `WebAutomation.LaunchChrome.LaunchChrome` (TODO no passo). URL vem da entrada `in_target_url` (valor não capturado pela extração). Erros declarados pela KB (`InvalidUrlError`, `LaunchEdgeError`) sem `ON ERROR`, junto com o critério de R8-3.
- `Web.InvokeWebService.InvokeWebService` — step_02_call_rest_api; equivalente a `REST.get` (`main.json:2`) com `Method: Web.Method.Get`; status `[colado KB: PAD 2.73, não rodado nesta instalação]`; sem instância de navegador, por decisão do analista (R8-2); `CustomHeaders` (opcional no seletor, `PAD_Robin_ActionKB.json:52291-52296`) monta o cabeçalho `Authorization` juntando `cfg_rest_auth_prefix` (vazia, TODO) e a entrada sensível `in_rest_token`, sem espaço entre as duas expressões (R1-1); `Accept`/`ContentType` são obrigatórios no seletor e vêm de `cfg_rest_accept`/`cfg_rest_content_type` vazias com TODO, sem afirmar JSON (R7-1); URL em `cfg_rest_endpoint_url`, não capturada pela extração; critério de status HTTP em TODO, sem `ON ERROR` (R8-3).
- `WebAutomation.CloseWebBrowser` — step_05_close_browser; **sem origem no legado** (não há `Browser.close` em `main.json:1-4`): diferença deliberada em relação ao legado (R8-1), fecha o navegador aberto no step_01 ao fim do flow, na Região "Encerramento"; consome `out_browser` (R4-2); numerado 05 por não ter origem no legado (regra do R3-1 do piloto); status `[colado KB: PAD 2.73, não rodado nesta instalação]`; erro declarado pela KB `CloseWebBrowserError`, sem `ON ERROR`.
- `**REGION` — organiza os estágios do flow, na ordem "Abertura do Navegador", "Subfluxo comum: Obter credencial do cofre (candidato a reuso)", "Consulta ao Sistema Externo (REST)", "Encerramento", "Fora do escopo aprovado (UC-02)"; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.
- `SET` — configuração `cfg_` no topo; status `[colado KB: PAD 2.73, não rodado nesta instalação]`.

Credentials.GetCredential (seção `[não validado]` da whitelist, não é id Robin real)
**não é usada** nem como placeholder: o step_03 documenta que a credencial chega por
entrada sensível `in_`, sem ação de cofre.

## Decisões do analista (Cleyber, 2026-11-05)

1. **Sessão do navegador (R8-2)**: a API REST é **independente** da sessão do
   navegador (não depende de cookie nem de login web). O UC-01 continua no PAD com
   `Web.InvokeWebService.InvokeWebService` sem instância de navegador. O aninhamento de
   `REST.get` e `CredentialVault.getCredential` como filhos de `Browser.open` em
   `input/a360-browser-rest/main.json:4-12` **não implica dependência**. Observação para
   revisão humana: `03-classification/classification.md:72-74` sugeria reavaliar UC-01
   para NOT_PAD nesse caso; a decisão do analista mantém UC-01 no PAD. O registro dessa
   decisão no manifesto/classificação fica com o humano (fora do escopo de escrita
   desta conversão).
2. **Autenticação do REST (R1-1)**: a credencial de `main.json:3` autentica o
   `REST.get`, por **token no cabeçalho**. Mesmo padrão do piloto `a360-excel-vault`
   (ADR-030): entrada sensível `in_rest_token`, declarada no designer; cabeçalho
   `Authorization` em `CustomHeaders` juntando `%cfg_rest_auth_prefix%` e
   `%in_rest_token%` sem espaço entre as duas expressões. `cfg_rest_auth_prefix` fica
   vazia com TODO: o esquema seguido de espaço, ou vazio para token puro. A Região da
   credencial passa a vir **antes** do REST; os nomes `step_NN` continuam presos à
   ordem do legado (`main.json:1-4`), com o motivo comentado no topo do `Main.robin` e
   no step_03.
3. **Status HTTP (R8-3)**: critério a **confirmar com o analista**. `# TODO reflow`
   explícito no step_02, sem `ON ERROR` inventado; o TODO cita que, com
   `FailOnErrorStatus: False`, 4xx/5xx só aparecem em `out_rest_status_code`.
4. **Accept/ContentType (R7-1)**: viram `cfg_rest_accept`/`cfg_rest_content_type` vazias
   com TODO; o formato JSON não é afirmado (o default da KB é `application/xml`,
   `PAD_Robin_ActionKB.json:52487-52498`, e o legado não registra formato).

## Achados da auditoria tratados

- **R1-1**: autenticação por `in_rest_token` em `CustomHeaders` do step_02; Região da
  credencial movida para antes do REST, motivo comentado no topo e no step_03
  (decisão 2).
- **R4-1**: `README.md` do flow reescrito para a versão atual: ids reais, status
  `[colado KB: PAD 2.73, não rodado nesta instalação]`, pendências A1/A4 apontando para
  os passos atuais, regra fixa de rodar `fix-robin-eol` e `lint-robin` depois de
  qualquer alteração, sem estado datado dos gates.
- **R4-2**: `cfg_output_folder` removida (UC-01 não grava arquivo);
  `cfg_credential_reference` removida (credencial por entrada sensível; a referência
  `main.json:3:credential-vault` fica só como comentário de rastreio no step_03);
  `out_browser` agora é consumida pelo step_05.
- **R5-1**: step_03 renomeado para
  `step_03_get_credential_subfluxo_comum_obter_credencial_do_cofre`, na Região
  "Subfluxo comum: Obter credencial do cofre (candidato a reuso)", com comentário citando
  `reference/subfluxos-comuns.md#obter-credencial-do-cofre`, as duas evidências e a
  recomendação de reuso (ver seção abaixo).
- **R7-1**: `Accept`/`ContentType` em `cfg_` vazias com TODO (decisão 4).
- **R8-1**: `WebAutomation.CloseWebBrowser` acrescentado como step_05_close_browser, na
  Região "Encerramento", como diferença deliberada em relação ao legado.
- **R8-2**: decisão 1 registrada no comentário do step_02 e aqui; flow inalterado
  quanto à instância de navegador.
- **R8-3**: TODO de critério de status HTTP no step_02 (decisão 3), citando os erros
  declarados pela KB para o step_01, o step_02 e o step_05, sem `ON ERROR`.

## Subfluxo comum sinalizado

O **step_03** corresponde à entrada `obter-credencial-do-cofre`, catalogada (status
`catalogado`) em `reference/subfluxos-comuns.md#obter-credencial-do-cofre`, com as
evidências `a360-browser-rest/input/main.json:3` (este passo) e
`a360-excel-vault/input/main.json:4`. Recomendação registrada no catálogo: extrair para
um subflow compartilhado (ex.: Subflow_ObterCredencialDoCofre) que recebe a referência
da credencial (`cfg_credential_reference`) e devolve a credencial (`out_credential`), em
vez de repetir o passo isolado a cada conversão. Com a decisão de entrada sensível,
essas variáveis não existem neste flow; a recomendação continua válida para quando
houver cofre no PAD. Alternativa já padronizada, se a entrada sensível não servir em
produção: o subflow padrão ativo `ConsultarCredencialProducao` (tabela "Subflows padrão
já existentes no PAD" do mesmo arquivo), não aplicado aqui sem decisão do analista.

Observação para revisão humana (o conversor não edita o catálogo): a entrada do
catálogo descreve esta evidência como "antes de `REST.get` em `main.json:2`"
(`reference/subfluxos-comuns.md:62-63`), mas no legado a credencial vem **depois** do
REST (`01-inventory/inventory.json:2-13` e :42-51); só no flow PAD ela passou a vir antes.

Nenhum candidato a novo subfluxo comum identificado. Nenhuma entrada `proposto`
sinalizada como `catalogado`.

## Dependência entre bots (fora do escopo)

A única dependência do inventário é `TaskBot.run` (`main.json:4`, target `child.json`,
resolution `resolvida`, `01-inventory/inventory.json:25-37`), que é o UC-02, fora do
escopo aprovado. Aparece no `Main.robin` só como comentário
`step_04_out_of_scope_subflow_child` na Região "Fora do escopo aprovado (UC-02)", sem
`CALL`. O nome não bate com nenhum subflow padrão (ativo ou descontinuado) de
`reference/subfluxos-comuns.md`.

## Variáveis de entrada a declarar no designer

- Entrada `in_target_url`: texto. URL aberta pelo step_01 (valor não capturado pela
  extração).
- Entrada `in_rest_token`: texto, **sensível**. Token usado no cabeçalho
  `Authorization` do step_02.

## Pendências antes de rodar no designer

- **Valores não capturados** pela extração determinística (`01-inventory/inventory.json`,
  `02-docs/integrations.md`): preencher com o analista `cfg_rest_endpoint_url`,
  `cfg_rest_accept`, `cfg_rest_content_type` e `cfg_rest_auth_prefix` (esquema seguido
  de espaço, ou vazio); valor de `in_target_url` na execução.
- **Critério de sucesso HTTP** (R8-3), incluindo um 401 por prefixo errado, visível só
  em `out_rest_status_code`.
- **A1** (`02-docs/risks.md`): navegador do legado (Edge ou Chrome) e extensão do PAD no
  ambiente, antes de rodar o step_01.
- **A4** (`02-docs/risks.md`): `in_rest_token` declarada como sensível; plano de origem
  da credencial em produção.
- O flow de teste em `05-test/test_uc-01-browser-rest/` precisa ser regenerado depois
  desta rodada (cita ids e comportamentos da versão antiga, `review.md`, Conclusão).
