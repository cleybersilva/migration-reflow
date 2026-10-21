"""Opção --update-golden: regrava os golden files em vez de comparar com eles."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regrava os golden files de tests/regression/golden/ em vez de comparar.",
    )
