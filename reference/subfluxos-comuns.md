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
convertido.

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
