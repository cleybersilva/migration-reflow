"""Complexidade P, M ou G: a pior dimensão vence, e só A360 tem confiança alta."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reflow.complexity import assess, read_size, write_assessment


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _facts(count: int) -> list[dict]:
    return [{"file": "main.json", "line": n} for n in range(count)]


def test_small_a360_bot_is_p_with_high_confidence() -> None:
    result = assess({"source_type": "a360", "data_sources": _facts(15)})
    require(result.size == "P" and result.confidence == "alta", f"{result}")
    require(result.drivers == (), f"P não tem motivo para destacar: {result.drivers}")


@pytest.mark.parametrize(
    ("inventory", "size", "driver"),
    [
        ({"data_sources": _facts(16)}, "M", "passos"),
        ({"data_sources": _facts(51)}, "G", "passos"),
        ({"unknown_commands": _facts(1)}, "M", "desconhecidos"),
        ({"unknown_commands": _facts(6)}, "G", "desconhecidos"),
        ({"credentials": _facts(2)}, "M", "credenciais"),
        ({"credentials": _facts(4)}, "G", "credenciais"),
        ({"dependencies": [{"kind": "bot", "target": "a.json"}]}, "M", "bots"),
        ({"dependencies": [{"kind": "bot"} for _ in range(4)]}, "G", "bots"),
        (
            {"ui_interactions": _facts(1), "http_calls": _facts(1), "data_sources": _facts(1)},
            "M",
            "integração",
        ),
    ],
)
def test_worst_dimension_wins(inventory: dict, size: str, driver: str) -> None:
    result = assess({"source_type": "a360", **inventory})
    require(result.size == size, f"{inventory}: {result.size}")
    require(any(driver in item for item in result.drivers), f"{result.drivers}")


def test_imports_are_not_bots_and_non_a360_has_low_confidence() -> None:
    result = assess(
        {"source_type": "python", "dependencies": [{"kind": "import", "module": "csv"}]}
    )
    require(result.metrics["bot_dependencies"] == 0, "import não é bot chamado")
    require(result.confidence == "baixa", "Python não enxerga os passos como o A360")


def test_write_then_read_and_fallback_for_old_output(tmp_path: Path) -> None:
    (tmp_path / "01-inventory").mkdir()
    inventory = {"source_type": "a360", "data_sources": _facts(16)}
    (tmp_path / "01-inventory" / "inventory.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    require(read_size(tmp_path) == "M", "sem complexity.json, calcula do inventário")
    write_assessment(tmp_path, {"source_type": "a360"})
    require(read_size(tmp_path) == "P", "complexity.json gravado vence")
    require(read_size(tmp_path / "nada") == "—", "sem inventário, não presume")
