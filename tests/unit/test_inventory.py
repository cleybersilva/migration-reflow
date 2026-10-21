"""Schema do inventário: campos padrão, FACT_FIELDS e to_dict()."""

from __future__ import annotations

import pytest

from reflow.inventory import FACT_FIELDS, Inventory


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_fact_fields_are_the_five_categorized_lists() -> None:
    require(
        set(FACT_FIELDS)
        == {"credentials", "data_sources", "dependencies", "http_calls", "ui_interactions"},
        f"FACT_FIELDS inesperado: {FACT_FIELDS}",
    )


def test_default_inventory_has_every_list_empty() -> None:
    inventory = Inventory()
    for field in (*FACT_FIELDS, "files", "unknown_commands", "warnings"):
        require(getattr(inventory, field) == [], f"{field} deveria nascer vazio.")


def test_to_dict_round_trips_every_field() -> None:
    inventory = Inventory(project="demo", source_type="python")
    inventory.http_calls.append({"file": "a.py", "line": 1, "operation": "open"})
    data = inventory.to_dict()
    require(data["project"] == "demo", "project não foi serializado.")
    require(data["source_type"] == "python", "source_type não foi serializado.")
    expected_http_calls = [{"file": "a.py", "line": 1, "operation": "open"}]
    require(data["http_calls"] == expected_http_calls, "http_calls não foi serializado.")
    require(data["schema_version"] == "1.0", "schema_version deveria ter um valor padrão.")
