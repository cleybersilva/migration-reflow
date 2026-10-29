# Subfluxos comuns entre processos

Catálogo de **padrões de passos que se repetem entre processos diferentes**
(não só dentro do mesmo flow) — candidatos naturais a virar um subflow PAD
compartilhado em vez de serem remontados do zero a cada conversão.

Isto é diferente da convenção de dependência entre bots já descrita em
[`robin-conventions.md`](robin-conventions.md) e na ação `Flow.RunSubflow`
de [`robin-actions.md`](robin-actions.md): aquela cobre uma chamada
**explícita** no legado (A360 `TaskBot.run` apontando para outro bot,
registrada em `dependencies` do inventário). Este catálogo cobre o caso
oposto — uma **sequência de ações equivalentes que reaparece em projetos
diferentes**, sem que o legado tenha chamado nada explicitamente; a
repetição só fica visível depois de comparar mais de um projeto já
convertido. Este arquivo também traz, numa seção separada ao final, uma
lista de **nomes de bot/subflow já padronizados na organização e chamados
diretamente pelo legado** — mecanismo e fonte de evidência diferentes, ver
["Subflows padrão já existentes no PAD"](#subflows-padrao-ja-existentes-no-pad-chamados-pelo-nome-do-bot-filho)
abaixo.

## Regra para o `reflow-pad-converter`

1. Antes de converter, confira se algum trecho do flow corresponde a uma
   entrada **catalogada** abaixo (status `catalogado`).
2. Se corresponder, sinalize de forma explícita e profissional no
   `Main.robin` — nunca deixe a repetição implícita dentro de um passo
   comum:
   - Nome do passo com sufixo `_subfluxo_comum_<slug_do_padrao>`.
   - Comentário imediatamente acima do passo citando: o nome do padrão, o
     link para a entrada aqui (`reference/subfluxos-comuns.md#<slug>`) e a
     recomendação de reuso registrada na entrada.
   - Quando possível, envolver o passo na sua própria `FlowControl.Region`
     rotulada `Subfluxo comum: <nome do padrão> (candidato a reuso)`.
   - Registrar o mesmo apontamento em `notas-conversao.md`.
3. **Nunca** sinalize uma entrada com status `proposto` como se já fosse
   `catalogado` — um padrão só é catalogado depois de evidência
   `projeto:arquivo:linha` de pelo menos dois projetos diferentes.
4. Se encontrar uma sequência que se repete com evidência real em dois ou
   mais projetos e que **não** está listada aqui, não edite este arquivo
   (fora do escopo de escrita do agent) — registre em `notas-conversao.md`
   um item "candidato a novo subfluxo comum", citando o padrão e as
   evidências (`projeto:arquivo:linha` de cada ocorrência), para um humano
   avaliar e, se confirmado, adicionar a entrada aqui.

## Regra para o `reflow-robin-reviewer`

Ao auditar um `Main.robin`, confira também se todo passo que corresponde a
uma entrada `catalogado` deste arquivo recebeu a sinalização completa (nome
com sufixo, comentário citando a entrada, Região quando aplicável) — e se
todo "candidato a novo subfluxo comum" citado em `notas-conversao.md` tem
evidência `projeto:arquivo:linha` real, não uma suposição.

## Catálogo

### `obter-credencial-do-cofre`

- **Quando aparece**: um passo que busca uma credencial no cofre
  (A360 `CredentialVault.getCredential`/`get` → PAD
  `Credentials.GetCredential`) antes de uma ação que depende dela (chamada
  HTTP autenticada, login numa aplicação, etc.).
- **Evidência observada**:
  - `a360-browser-rest/input/main.json:3` (`CredentialVault.getCredential`,
    antes de `REST.get` em `main.json:2`).
  - `a360-excel-vault/input/main.json:4` (`CredentialVault.getCredential`,
    usada pela chamada `REST.post` em `main.json:3`).
- **Recomendação de reuso**: extrair para um subflow compartilhado (ex.:
  `Subflow_ObterCredencialDoCofre`) que recebe `cfg_credential_reference`
  como entrada e devolve `out_credential`; qualquer flow que precise de uma
  credencial do cofre antes de uma ação autenticada chama esse subflow em
  vez de repetir o passo `Credentials.GetCredential` isolado.
- **Como sinalizar no `Main.robin`**: nome do passo
  `step_NN_subfluxo_comum_obter_credencial_do_cofre`; comentário citando
  esta entrada e as duas evidências acima; `FlowControl.Region` rotulada
  `Subfluxo comum: Obter credencial do cofre (candidato a reuso)`.
- **Status**: `catalogado` (evidência de 2 projetos).

### `tratamento_erro_padrao` (hipótese — sem evidência confirmada)

- **Quando aparece**: um bloco que envolve uma ação arriscada com captura de
  erro, log da falha e, às vezes, notificação — padrão comum em automações
  RPA em geral.
- **Evidência observada**: nenhuma ainda. A extração determinística atual
  (`01-inventory/inventory.json`) não captura blocos de try/catch do A360
  como um campo próprio, então não há `projeto:arquivo:linha` real para
  citar hoje.
- **Recomendação de reuso**: se e quando aparecer evidência real de dois
  projetos, desenhar um subflow compartilhado de tratamento de erro
  (entrada: identificação do passo que falhou; saída: log gravado e,
  opcionalmente, flag de notificação enviada).
- **Como sinalizar no `Main.robin`**: nenhuma por enquanto — **não**
  promover para `catalogado` sem evidência. Um `reflow-pad-converter` que
  encontrar algo parecido com evidência real deve seguir a regra 4 acima
  (registrar candidato em `notas-conversao.md`, nunca marcar aqui sozinho).
- **Status**: `proposto` (hipótese, aguardando evidência).

### `notificacao_de_falha_por_email` (hipótese — sem evidência confirmada)

- **Quando aparece**: envio de e-mail (ou outro canal) avisando que o
  processo falhou, normalmente no encerramento do flow.
- **Evidência observada**: nenhuma ainda nos três projetos de exemplo
  (`a360-browser-rest`, `a360-excel-vault`, `quote-scraper`).
- **Recomendação de reuso**: mesma lógica da entrada anterior — desenhar
  quando houver evidência real.
- **Status**: `proposto` (hipótese, aguardando evidência).

## Como promover uma entrada de `proposto` para `catalogado`

1. Reúna a evidência `projeto:arquivo:linha` de pelo menos dois projetos
   diferentes (do inventário real, nunca inventada).
2. Edite esta entrada (ou crie uma nova), preenchendo "Evidência observada"
   com as citações reais e trocando o status para `catalogado`.
3. Rode `reflow-convert` de novo nos projetos afetados, se já tiverem
   `Main.robin` gerado sem a sinalização — a conversão antiga não é
   corrigida sozinha, precisa de uma rodada nova.
4. Nunca remover ou reduzir a evidência de uma entrada já `catalogado` sem
   revisão humana (mesma regra de `a360-to-pad.md`, ver
   [`AGENTS.md`](../AGENTS.md)).

## Subflows padrão já existentes no PAD (chamados pelo nome do bot filho)

Lista diferente do catálogo acima: não é um padrão de ação detectado por
repetição entre conversões, é uma **lista de nomes de bot/subflow já
padronizados na organização**, que o legado chama diretamente (A360
`TaskBot.run` com `target`/`botName` igual a um destes nomes, registrado em
`dependencies` de `01-inventory/inventory.json`) e que já têm um subflow
equivalente disponível no PAD — então a conversão não deve tratar essa
dependência como "resolução pendente" genérica, e sim marcar explicitamente
que o subflow padrão já existe e deve ser reaproveitado.

**Fonte da evidência**: confirmação direta do usuário/analista em sessão de
2026-10-29 — fato organizacional, não extraído de `input/<projeto>/`.
Nenhum dos três projetos de exemplo (`a360-browser-rest`,
`a360-excel-vault`, `quote-scraper`) chama algum destes hoje; a lista existe
para quando um export A360 real citar um deles.

| Nome do bot/subflow | Situação | Observação |
| --- | --- | --- |
| `MapearFileServer` | ativo | Subflow padrão para mapear unidade de rede (file server). |
| `DesmapearFileServer` | ativo | Subflow padrão para desmapear unidade de rede. |
| `ConsultarCredencialProducao` | ativo | Subflow padrão para consultar credencial de produção. Relacionado à entrada `obter-credencial-do-cofre` do catálogo acima, mas aqui é um subflow **nomeado e já chamado pelo legado**, não um padrão de ação a ser detectado. |
| `AcessoPainelServico` | ativo | Subflow padrão para acessar painel de serviço. |
| `KillProcessByName` | ativo | Subflow padrão para finalizar processo pelo nome. |
| `Log_Splunk` | **descontinuado** | Substituído pelo Datadog, ferramenta padrão e oficial de observabilidade do banco. Nunca reaproveitar a chamada antiga como se ainda fosse válida. |

### Regra para o `reflow-pad-converter`

1. Para toda dependência (`TaskBot.run`) cujo `target`/`botName` bate com um
   nome **ativo** desta lista: aplicar a convenção já existente de subflow
   (sufixo `_subflow_<nome_do_bot_filho>`, comentário citando o bot filho —
   ver `robin-conventions.md`) e **acrescentar** no comentário, de forma
   explícita: "subflow padrão já disponível no PAD — reaproveitar a chamada
   existente, nunca reimplementar a lógica interna como ação solta".
2. Para `Log_Splunk` (ou qualquer nome futuro marcado **descontinuado**
   nesta tabela): o comentário deve dizer que o bot está descontinuado e
   citar o substituto (hoje: Datadog); o passo em si vira `TODO reflow`
   pedindo ao analista o nome exato do subflow Datadog a chamar — **nunca**
   apontar para `Log_Splunk` como se ainda fosse uma chamada válida, nem
   inventar o nome do subflow substituto sem confirmação.
3. Esta lista é mantida manualmente (edição humana direta no arquivo) — o
   `reflow-pad-converter` nunca adiciona, remove ou muda a `Situação` de uma
   linha sozinho.

### Regra para o `reflow-robin-reviewer`

Ao auditar, confira se toda dependência cujo `target`/`botName` aparece
nesta tabela recebeu a observação extra (subflow padrão já disponível, ou
aviso de descontinuado + substituto) — não só a marcação genérica de
subflow entre bots.
