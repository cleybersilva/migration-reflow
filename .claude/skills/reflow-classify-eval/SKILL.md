---
name: reflow-classify-eval
description: Mede a qualidade da classificação rodando reflow-classifier e reflow-classification-reviewer no golden set sintético de tests/fixtures/classification/ e pontuando contra o rótulo esperado, com matriz de confusão e erros críticos. Use depois de mudar a rubrica, um prompt de classificação ou o modelo, ou quando o usuário pedir para validar a classificação.
metadata:
  opencode/slash: "true"
---

# reflow-classify-eval

## Entradas

- `tests/fixtures/classification/<caso>/`: `input/`, `docs/` e `expected.json`.

## O que faz

1. `uv run python -m reflow classify-eval prepare`: remonta `input/eval-<caso>` e
   `output/eval-<caso>` do zero (extração + `02-docs/` do caso).
2. Para cada `eval-<caso>`, chame o agent **reflow-classifier** e depois o
   **reflow-classification-reviewer**, cada um em contexto novo, com o nome do
   projeto como única informação sobre o caso.
3. `uv run python -m reflow classify-eval score`: compara com `expected.json`,
   aplica o gate em cada caso e grava `output/_classification-eval.md`.
4. `uv run python -m reflow classify-eval clean` depois de registrar o resultado.

No `refold`, `uv run python -m refold classify --eval` faz os passos 1 a 3.

## Regras

- **Rótulo cego:** nunca leia nem mostre `expected.json` ou `tests/fixtures/classification/`
  a um agent, e nunca cite o resultado esperado no pedido. Os nomes dos casos são neutros
  de propósito.
- Falha é resultado, não algo a contornar: não ajuste rótulo, rubrica ou prompt só para o
  score passar. Divergência entre rótulo e agents vai para o analista decidir.
- Os casos são sintéticos e os rótulos são propostos até um analista revisar. O score mede
  a aplicação da rubrica nesses casos, não prova acerto em robô real.

## O que sobrescreve

- Somente `input/eval-*`, `output/eval-*` e `output/_classification-eval.md`, fora do Git.

## Resumo a mostrar

- Resultado, casos corretos, erros críticos (`PAD` x `NOT_PAD`), matriz de confusão e cada
  caso que falhou com o motivo. Nunca declarar validado com caso pendente ou erro crítico.
