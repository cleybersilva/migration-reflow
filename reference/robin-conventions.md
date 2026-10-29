# Convenções Robin — base inicial

- Um `Main.robin` por flow, pronto para colar no PAD, sem configuração externa.
- Prefixos `step_`, `in_`, `out_`, `cfg_`; nomes em snake_case minúsculo.
- Saídas somente em `C:\Users\Public\Documents\`.
- Documentação do flow deve incluir seção “Teste” e evidências `arquivo:linha`.
- Nunca inventar sintaxe. Usar somente a whitelist de `robin-actions.md`.
- Sem validação real no PAD, marcar `[não validado]`; pendências são TODO reflow.
- Separar os passos do mesmo estágio do processo com `FlowControl.Region`
  (ação de controle de fluxo do Power Automate Desktop) — um bloco por
  estágio (ex.: "Leitura da Base de Entrada e Logs", "Processamento",
  "Gravação de Saída", "Encerramento"), com rótulo igual ao nome do estágio
  usado em `02-docs/use-cases.md`/`architecture.md`. Região organiza
  visualmente; não troca nem reduz os comentários `step_`/`in_`/`out_`/`cfg_`
  já exigidos.
- Chamada a outro Task Bot/subflow (A360 `TaskBot.run` → PAD
  `Flow.RunSubflow`) nunca fica implícita dentro de um passo comum: nome do
  passo com sufixo `_subflow_<nome_do_bot_filho>`, comentário citando o bot
  filho (campo `target`/`botName` de `dependencies` em
  `01-inventory/inventory.json`) e, quando possível, Região própria rotulada
  `Subflow: <nome do bot filho>` para separar visualmente do fluxo principal.
- Subfluxo **comum entre processos diferentes** (não é uma chamada explícita
  do legado — é uma sequência de passos que se repete em mais de um projeto
  já convertido, catalogada em
  [`subfluxos-comuns.md`](subfluxos-comuns.md)): quando o passo corresponder
  a uma entrada com status `catalogado` nesse arquivo, sinalize também de
  forma explícita e profissional, nunca implícita — nome do passo com
  sufixo `_subfluxo_comum_<slug_do_padrao>`, comentário citando a entrada
  catalogada e a recomendação de reuso registrada lá, e, quando possível,
  Região própria rotulada `Subfluxo comum: <nome do padrão> (candidato a
  reuso)`. Entrada `proposto` (sem evidência de dois projetos) nunca é
  sinalizada como se fosse `catalogado`; veja o procedimento completo (e o
  que fazer ao notar um novo padrão repetido) em `subfluxos-comuns.md`.

Whitelist completa: [`robin-actions.md`](robin-actions.md). Tabela verdade A360 → PAD:
[`a360-to-pad.md`](a360-to-pad.md). Critérios de classificação PAD/PARTIAL/NOT_PAD:
[`classification-rubric.md`](classification-rubric.md). Padrões recorrentes
entre processos: [`subfluxos-comuns.md`](subfluxos-comuns.md).
