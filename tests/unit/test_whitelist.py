"""reference/robin-actions.md e reference/a360-to-pad.md: leitura e coerência cruzada."""

from __future__ import annotations

from pathlib import Path

import pytest

from reflow.robin import load_truth_table, load_whitelist, truth_table_action_name

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_whitelist_loads_without_error() -> None:
    actions = load_whitelist(ROOT)
    require(len(actions) > 0, "A whitelist deveria ter pelo menos uma ação.")
    require(
        all(action.status.startswith("[") for action in actions.values()),
        "Toda ação precisa de um status entre colchetes.",
    )


def test_truth_table_loads_without_error() -> None:
    rows = load_truth_table(ROOT)
    require(len(rows) > 0, "A tabela verdade deveria ter pelo menos uma linha.")
    require(
        all("Pacote A360" in row and "Status" in row for row in rows),
        "Toda linha precisa das colunas Pacote A360 e Status.",
    )


def test_every_truth_table_action_exists_in_whitelist() -> None:
    actions = load_whitelist(ROOT)
    rows = load_truth_table(ROOT)
    missing = sorted(
        {
            name
            for row in rows
            if (name := truth_table_action_name(row)) is not None and name not in actions
        }
    )
    require(not missing, f"Ações citadas na tabela verdade mas ausentes na whitelist: {missing}")


def _robin_block_after_heading(text: str, name: str) -> str:
    """Pega o primeiro bloco de código robin que vem depois da seção `### name`."""
    heading = f"### `{name}`"
    start = text.index(heading)
    block_start = text.index("```robin", start) + len("```robin")
    block_end = text.index("```", block_start)
    return text[block_start:block_end]


def test_validated_actions_have_a_real_snippet_not_the_generic_placeholder() -> None:
    """`[validado PAD: rodou]` só existe depois de execução real confirmada
    (ver ADR-025/Fase 25) — mas o status sozinho não garante que o snippet
    foi de fato trocado; essa checagem cruza as duas coisas."""
    path = ROOT / "reference" / "robin-actions.md"
    text = path.read_text(encoding="utf-8")
    actions = load_whitelist(ROOT)
    validated = [name for name, action in actions.items() if action.validated]
    require(validated, "Pelo menos uma ação validada é esperada neste ponto do projeto.")
    for name in validated:
        block = _robin_block_after_heading(text, name)
        require(
            "TODO reflow: colar aqui" not in block,
            f"{name} está [validado PAD: rodou] mas o snippet ainda é o placeholder genérico.",
        )
