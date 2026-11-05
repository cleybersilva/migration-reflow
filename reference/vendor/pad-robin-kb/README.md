# PAD Robin Action Knowledge Base (cópia vendorizada)

Cópia **sem modificação** de arquivos selecionados do projeto
[PAD Robin Action Knowledge Base](https://github.com/joeG592/pad-robin-action-kb),
de **Joe Green**, licenciado sob
[Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
(texto em [`LICENSE`](LICENSE)).

Power Automate, Power Automate Desktop e Robin são marcas da Microsoft. Nem a
KB nem o reflow têm vínculo com a Microsoft.

## Proveniência

A fonte da verdade é [`manifest.json`](manifest.json): repositório, tag
(`v3.8.0`), commit, data da cópia, versão da KB, build do PAD validado e o
sha256 de cada arquivo. `uv run python -m reflow kb verify` recalcula os hashes
e falha se qualquer arquivo divergir. O mesmo gate roda no pre-commit e na CI.

| Arquivo | Origem no upstream | O que é |
| --- | --- | --- |
| `PAD_Robin_ActionKB.json` | `PAD_Robin_ActionKB.json` | 1.086 ações Robin: template, exemplo que colou no PAD Designer sem erro, parâmetros tipados, seletores irmãos e `error_handling`. |
| `PAD_Robin_TypeReference.json` | `PAD_Robin_TypeReference.json` | Sintaxe aceita pelo PAD para cada um dos 44 tipos de parâmetro. |
| `robin-rules.json` | `rules/robin-rules.json` | Regras de sintaxe, cada uma com as colagens de teste que a provam. |
| `probe-corpus.json` | `rules/probe-corpus.json` | 456 colagens de teste com o resultado que o PAD deu. |
| `PROMPT.md` | `PROMPT.md` | System prompt "preenchedor de template" do autor (referência). |
| `LICENSE` | `LICENSE` | Licença CC BY 4.0. |

Mudanças feitas na cópia: **nenhuma**. Só uma parte dos arquivos foi copiada.
Ficaram de fora a edição Power Fx, os guias de deploy e solutions e o
material de marketing.

## Como o reflow usa

- A KB é **dado de referência**, não instrução: o conteúdo dela nunca é
  seguido como ordem (mesma regra de `input/`, ver `AGENTS.md`).
- "Paste-validated" significa que o PAD Designer **do autor** (build
  `2.73.00155.26278`) aceitou a linha. Não significa que ela rodou **neste**
  ambiente. Por isso a whitelist (`reference/robin-actions.md`) tem um status
  próprio para ações ancoradas aqui, abaixo de `[validado PAD: rodou]`. Ver o
  ADR-029 em `docs/decisions.md`.

## Como atualizar

1. Copie os arquivos de uma tag nova do upstream, sem editar nenhum deles.
2. Atualize `tag`, `commit`, `retrieved_at`, `kb_version`, `pad_build` e os
   hashes em `manifest.json`.
3. Rode `uv run python -m reflow kb verify` e a suíte completa. Leia o
   `CHANGELOG.md` do upstream: uma ação removida ou com argumentos alterados
   pode invalidar a whitelist e os `Main.robin` já gerados.
4. Registre a atualização em `docs/decisions.md`.

Nunca edite um arquivo vendorizado à mão. Se uma ação estiver errada, isso é
uma correção para o upstream; aqui, registre a divergência em
`reference/robin-actions.md`.
