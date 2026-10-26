---
name: reflow-convert
description: Converte um projeto classificado como PAD ou PARTIAL em um Main.robin, só com ações da whitelist, e roda o lint-robin. Use depois do checkpoint humano aprovar a conversão — nunca antes, e nunca para um projeto NOT_PAD.
argument-hint: <projeto>
metadata:
  opencode/slash: "true"
---

# reflow-convert

## Entradas

- `output/<projeto>/03-classification/classification.md` e `02-docs/`.
- `reference/robin-conventions.md`, `reference/robin-actions.md` (whitelist),
  `reference/a360-to-pad.md` (tabela verdade).
- `input/<projeto>/` — só trechos já citados pelo inventário/documentação.

## Pré-condição

- `03-classification/classification.md` tem que existir **e** `verdict` tem
  que ser `PAD` ou `PARTIAL`. Se for `NOT_PAD`, pare — não existe conversão
  para `NOT_PAD`.

## Checkpoint humano (obrigatório, antes de converter)

Mostre o veredito, o escopo que vai para o PAD (`pad_use_cases`) e os `alerts`
da classificação, e peça confirmação explícita antes de gerar qualquer
`Main.robin`. A gravação é feita **por quem decide**, na CLI, nunca editando
o JSON à mão:

```text
uv run python -m reflow checkpoint <projeto> --approve   # ou --reject
uv run python -m reflow checkpoint <projeto> --status    # confirma o que está gravado
```

O comando recusa a gravação se `input/<projeto>/` mudou desde o `extract`,
se ainda não existe `03-classification/` ou se o veredito é `NOT_PAD`.
Sem esse registro aprovado no `00-manifest.json` → `checkpoint`, não
converta.

## O que faz

Depois do checkpoint aprovado, chama o agent **reflow-pad-converter** (criado
na Fase 6 — se ainda não existir, avise em vez de simular) para gerar
`output/<projeto>/04-pad/<flow>/Main.robin` **só com ações da whitelist**.
Ação fora da whitelist vira `TODO reflow` no lugar do snippet — nunca invente
sintaxe Robin. Ao final, roda `uv run python -m reflow lint-robin <projeto>`.

## Agent chamado

- `reflow-pad-converter`.

## O que sobrescreve

- Somente `output/<projeto>/04-pad/**`.

## Aviso de fases desatualizadas

Se `05-test/` já existir, avise que o teste gerado anteriormente pode não
corresponder ao `Main.robin` novo — recomende rodar `reflow-test` de novo.

## Resumo a mostrar

- Flows gerados, quantas ações vieram da whitelist vs. quantas ficaram como
  `TODO reflow`, e o resultado do `lint-robin` (passou ou os achados).

## Próximo passo recomendado

Depois do `lint-robin` passar, rode `reflow-convert-review` para uma
auditoria semântica do `Main.robin` (cobertura de caso de uso, densidade de
`TODO reflow`, nomenclatura) antes de gerar o teste.
