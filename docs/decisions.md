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
