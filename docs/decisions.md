# Decisões de arquitetura

## ADR-001 — Runtime somente stdlib

Python >= 3.12 via uv, sem dependências de runtime ou chamadas de rede. pytest e ruff
são dependências diretas apenas de desenvolvimento; suas transitivas ficam em uv.lock.
A instalação de ferramentas pode precisar de rede; o processamento do legado não.

## ADR-002 — IAra compatível com OpenAI

O endpoint precisa oferecer `/v1/chat/completions`. `IARA_BASE_URL` deve terminar em
`/v1`; `IARA_API_KEY` e `IARA_MODEL` são fornecidos pelo ambiente do processo.
`iara-default` é um alias placeholder; endpoint, compatibilidade e ID real do modelo
permanecem a confirmar. Não selecionar IAra automaticamente enquanto não configurada.

## ADR-003 — OpenCode V2

Ambiente observado: OpenCode 2.0.32. Usar `providers`, `permissions`, `shell` e
`subagent`, em vez dos campos legados do prompt. Usar runtime OpenAI-compatible
nativo do OpenCode. Não usar `doom_loop`: não é ação Core atual do V2.
Fonte: https://opencode.ai/v2/docs/migrate-v1 e guias de providers/permissões.
As permissões completas por agent serão implementadas na Fase 6.

## ADR-004 — Compatibilidade entre harnesses

Skills ficam em `.claude/skills/`, com caminho explícito em `opencode.json` para
descoberta compartilhada. Agents OpenCode são canônicos; espelhos Claude serão
gerados e testados na Fase 6. `AGENTS.md` concentra as regras.

## ADR-005 — Entrada confidencial e evidência mascarada

`input/` fica fora do Git, salvo o exemplo sintético `quote-scraper`.
Os sete materiais preexistentes ficam preservados localmente e ignorados no Git.
Em conflito entre leitura de trechos brutos e inventário mascarado, prevalece a
restrição: agents de negócio só recebem inventário/evidências mascarados.

## ADR-006 — Bloqueio seguro durante a construção

O hook roda scan e validação Robin, mas bloqueia enquanto esses comandos não existem.
Não criar implementações fictícias que retornem sucesso. Não contornar o hook.
O scanner deverá validar conteúdo preparado para commit, não apenas arquivos locais.

## ADR-007 — Robin e checkpoint

Whitelist obrigatória; nenhuma ação presumida validada. Sem snippets reais do PAD,
registrar a pendência sem inventar sintaxe. PAD/PARTIAL requer checkpoint explícito;
NOT_PAD não gera conversão. Testes estáticos não comprovam execução no PAD.

## ADR-008 — Esqueleto incremental

Módulos Python reservados com docstrings; sem comportamento simulado. Referências
e documentos futuros são identificados como pendentes. Nenhum artefato 00–05 é
criado para projeto inexistente; as pastas serão materializadas pelo pipeline.

## ADR-009 — Extração inicial com minimização

Sem exports reais, A360 usa fixtures sintéticas e metadados `packageName`,
`commandName` e nomes dos atributos; valores livres são omitidos, inclusive URLs
e referências brutas do Vault. Uma referência local `arquivo:node:credential-vault`
preserva rastreabilidade sem copiar credenciais. A tabela inicial de comandos
reconhecidos é conservadora e não equivale a uma whitelist Robin.
Python usa AST, resolve aliases de importação e não executa o código. .NET é
explicitamente heurístico. Não declarar cobertura completa de dialetos reais A360.

## ADR-010 — Reextração e manifesto

Cada extração gera hashes SHA256 de todos os arquivos de entrada (ZIP incluído),
data UTC e versão do reflow. Reextração limpa veredito/checkpoint e marca fases
02–05 como desatualizadas; não remove artefatos anteriores. O inventário não tem
timestamp. Projetos inválidos fazem o lote falhar, sem impedir os demais projetos.

## ADR-011 — `opencode.json` e agents: schema V2 real, não o legado

Validado contra o `opencode` 2.0.32 instalado (`opencode debug config`,
`opencode debug agents`, e o `$schema` de `https://opencode.ai/config.json`):
`provider`/`permission` (singular) são campos legados V1; os atuais são
`providers`/`permissions` (plural, `permissions` sempre um array de
`{action, resource, effect}}`), e isso vale tanto no `opencode.json` raiz
quanto no frontmatter de cada `.opencode/agents/*.md`. `doom_loop` não é usado
(ADR-003). Agent markdown **não tem campo `temperature`** —
`additionalProperties: false` no schema rejeitaria/ignoraria silenciosamente.
Corrigido um bug real herdado: a ação `"shell"` não existe; é `"bash"`.

## ADR-012 — Lint Robin nunca interpreta sintaxe Robin

`robin/lint.py` não tenta reconhecer qual ação PAD um `Main.robin` usa —
isso exigiria conhecer a sintaxe interna do Robin, que não está validada
(proibido por `AGENTS.md`). Em vez disso, o lint valida a estrutura que o
próprio pipeline controla: `notas-conversao.md` lista as ações usadas (uma
convenção nossa, em Markdown) e é cruzado contra `reference/robin-actions.md`;
`README.md` do flow precisa de um cabeçalho; o texto puro do `.robin` é
varrido para segredo atribuído e caminho absoluto fora de
`C:\Users\Public\Documents\`. Ação fora da whitelist só é pega se estiver
citada em `notas-conversao.md` — por isso todo agent que gera `Main.robin`
é instruído a manter esse arquivo em dia.

## ADR-013 — Relatório de lote nunca presume fase futura

`reflow/report.py` mostra `—` no veredito e `0` em flows/TODO/ações quando a
fase correspondente ainda não rodou para aquele projeto, em vez de omitir a
coluna ou inventar um valor. Isso é consistente com a regra de não declarar
pronto o que não foi feito — o relatório é honesto sobre o que falta, não só
sobre o que já existe.

## ADR-014 — Segunda opinião na classificação (reflow-classification-reviewer)

A classificação é a decisão mais cara do pipeline: ela decide se um projeto
vai para o PAD ou não. Em vez de confiar num único agent, `reflow-classify-review`
roda um segundo agent que reaplica `classification-rubric.md` do zero, sem ver
o raciocínio do primeiro, e grava a própria opinião em
`03-classification/review.md`. Decisões explícitas:

- O reviewer **nunca** sobrescreve `classification.md` — permissão de edição
  restrita ao arquivo `review.md`, não só à pasta da fase (mais estrita que os
  demais agents, que podem escrever em qualquer arquivo da própria subpasta).
- Divergência (`agreement: diverge`) não bloqueia nada sozinha; ela só precisa
  aparecer com destaque no checkpoint humano, que continua sendo quem decide.
- Rodar sempre, mesmo em `NOT_PAD` — um falso negativo (projeto que deveria
  ir para o PAD e foi classificado como `NOT_PAD`) é tão caro quanto um falso
  positivo.
- Custo aceito: uma chamada de LLM a mais por projeto. Troca-se inferência
  extra por robustez na decisão mais cara do pipeline.

## ADR-015 — Revisor semântico do Robin (reflow-robin-reviewer)

`reflow lint-robin` (ADR-012) só valida o que o próprio pipeline controla —
estrutura, não semântica: segredo atribuído, caminho absoluto fora do
permitido, ação citada em `notas-conversao.md` ausente da whitelist, cabeçalho
do `README.md`. Ele não verifica se o `Main.robin` cobre de fato os
`pad_use_cases`, se há `TODO reflow` demais para o flow ser útil, se a
nomenclatura segue `robin-conventions.md`, nem se `notas-conversao.md`
realmente corresponde ao que está no `.robin`. `reflow-convert-review` cobre
exatamente essa lacuna, como um segundo agent depois do lint, nunca no lugar
dele. Mesmas restrições do ADR-014: só grava o próprio `04-pad/<flow>/review.md`,
nunca `Main.robin`/`README.md`/`notas-conversao.md`, e não aprova nem bloqueia
sozinho — só informa o checkpoint humano antes de `reflow-test`.

## ADR-016 — Copilot como terceiro harness espelhado

O usuário pediu explicitamente que toda evolução de skill/agent apareça nos
três harnesses (Claude Code, OpenCode, GitHub Copilot) — nunca só em um.
Antes desta decisão, `.github/` nem existia. Desenho adotado, caso a caso:

- **Instruções de raiz**: `.github/copilot-instructions.md` é um ponteiro
  para `AGENTS.md`, idêntico em espírito ao `CLAUDE.md` — mesma fonte única
  de verdade, três arquivos finos.
- **Skills → prompt files**: `.github/prompts/<nome>.prompt.md`, um por
  skill (mais `reflow-report.prompt.md`, que espelha o command do OpenCode
  que só roda `reflow report`, sem skill dedicada). Escrito **à mão**, não
  gerado — porque o corpo é só um ponteiro de uma linha para
  `.claude/skills/<nome>/SKILL.md` (que o Copilot, em modo agent, consegue
  abrir e seguir), igual ao padrão já usado em `.opencode/commands/*.md`.
  Isso evita duplicar o conteúdo da skill numa terceira cópia.
- **Agents → chat modes**: `.github/chatmodes/<nome>.chatmode.md`, **gerado**
  por `scripts/sync_copilot.py` a partir de `.opencode/agents/` — mesma fonte
  dos espelhos Claude, mesmo motivo (o corpo de um agent é instrução
  completa, não um ponteiro; copiar manualmente divergiria com o tempo).
- **Honestidade sobre o que o Copilot não impõe**: o Copilot Chat não tem
  `permissions`/`tools` com bloqueio por recurso como o OpenCode — um
  chatmode pode, tecnicamente, editar qualquer arquivo se o modelo decidir
  ignorar a instrução. Por isso `render_chatmode()` **sempre** acrescenta um
  aviso explícito disso no fim de cada arquivo gerado — nunca sugerir ao
  usuário que os três harnesses têm o mesmo nível de imposição técnica.
- `tests/unit/test_copilot.py` trava a paridade (todo skill tem prompt, todo
  agent tem chatmode, todo chatmode carrega o aviso) do mesmo jeito que
  `test_sync_agents.py`/`test_skills.py` já travavam Claude/OpenCode — a
  omissão de um dos três harnesses numa mudança futura vira teste vermelho,
  não um lembrete em documentação que alguém pode esquecer de ler.

Não validado: nenhum destes arquivos foi testado dentro do GitHub Copilot de
verdade (a extensão não está disponível neste ambiente) — o formato segue a
documentação pública de customização do Copilot Chat (prompt files, chat
modes), mas, como o `IARA_MODEL` do ADR-002, o comportamento exato só se
confirma com a ferramenta real instalada.
