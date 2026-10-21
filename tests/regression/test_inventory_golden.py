"""Golden files: a extração não muda sem uma atualização explícita e revisada.

Rode `uv run pytest tests/regression --update-golden` para regravar de
propósito, e revise o diff antes de comitar — isso é mudança de
comportamento, não um bug corrigido na hora.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from reflow.extractors.a360 import A360Extractor
from reflow.extractors.dotnet import DotnetExtractor
from reflow.extractors.python import PythonExtractor
from reflow.inventory import Inventory

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


CASES: list[tuple[str, Callable[[], Inventory]]] = [
    ("a360-browser-rest", lambda: A360Extractor().extract(FIXTURES / "a360" / "browser-rest")),
    ("a360-excel-vault", lambda: A360Extractor().extract(FIXTURES / "a360" / "excel-vault")),
    ("dotnet-fixtures", lambda: DotnetExtractor().extract(FIXTURES / "dotnet")),
    ("quote-scraper", lambda: PythonExtractor().extract(ROOT / "input" / "quote-scraper")),
]


@pytest.mark.parametrize("name, build_inventory", CASES, ids=[case[0] for case in CASES])
def test_inventory_matches_golden(
    name: str, build_inventory: Callable[[], Inventory], request: pytest.FixtureRequest
) -> None:
    actual = build_inventory().to_dict()
    golden_path = GOLDEN_DIR / f"{name}.json"

    if request.config.getoption("--update-golden"):
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pytest.skip(f"golden de {name} atualizado — revise o diff antes de comitar.")

    require(golden_path.is_file(), f"Golden ausente para {name}; rode com --update-golden.")
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    require(
        actual == expected,
        f"{name}: a saída da extração mudou. Se for intencional, rode --update-golden.",
    )
