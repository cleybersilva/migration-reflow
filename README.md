# reflow

Pipeline de migração assistida por IA de robôs A360, Python e .NET para Power Automate
Desktop. Python extrai fatos sem executar o legado; agents documentam, classificam e
propõem conversões, sempre com validação humana.

## Estado atual

Fase 2: extração determinística A360/Python/.NET, manifesto SHA256, relatório inicial e
varredura mínima de segredos/PII (`reflow scan`) e de `.robin` pendente (`reflow lint-robin`).
Masking completo, skills, agents e conversão ainda não foram implementados.
Este projeto ainda não deve processar código confidencial real.

## Preparação

Requer Python >= 3.12, uv e Git. Na raiz do projeto:

```powershell
uv sync
git config core.hooksPath .githooks
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Não há dependências de runtime. `uv.lock` trava as dependências de desenvolvimento.
Nunca grave chaves reais em arquivos versionados. `.env.example` documenta as variáveis;
o processo do OpenCode precisa recebê-las no ambiente. Um arquivo `.env` sozinho não
é garantia de carregamento pelo harness.

O provider `iara` tem endpoint e modelo pendentes de confirmação; nenhum modelo IAra
é selecionado automaticamente. A configuração usa o formato nativo OpenCode V2.

Consulte [AGENTS.md](AGENTS.md), [segurança](SECURITY.md),
[decisões](docs/decisions.md) e [arquitetura](docs/architecture.md).
O guia completo será entregue na Fase 9.

## Extração (dados sintéticos)

Coloque cada projeto em `input/<projeto>/`, com nomes minúsculos, números, hífen ou
underscore. A360 aceita JSONs exportados ou um ZIP dentro dessa pasta; a extração
segura usa pasta temporária local, sem executar arquivos. Em projetos mistos,
A360 tem prioridade sobre .NET, que tem prioridade sobre Python.

```powershell
uv run python -m reflow extract quote-scraper
uv run python -m reflow extract --all
uv run python -m reflow report
```

O resultado fica em `output/<projeto>/00-manifest.json` e
`output/<projeto>/01-inventory/inventory.json`. Reextrair invalida a aprovação
anterior e marca fases posteriores como desatualizadas, sem apagar seus arquivos.
O inventário é estável; o horário do manifesto muda a cada execução.

Limitações atuais: A360 sintético, nomes de atributos sem valores, árvore em
pré-ordem (linha do editor, não linha física do JSON), imports/calls AST para Python
e heurísticas por linha para .NET. Referências de bots só são resolvidas quando
`attributes.botName` corresponde ao nome de um JSON do export. Outros formatos
permanecem não resolvidos. Binários .NET apenas geram aviso para usar ILSpy.
O relatório ainda mostra somente o estado da extração; será ampliado na Fase 8.
