"""Contrato comum: detect() decide a origem, extract() nunca executa o legado."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..inventory import Inventory


@runtime_checkable
class Extractor(Protocol):
    name: str

    def detect(self, path: Path) -> bool: ...

    def extract(self, path: Path) -> Inventory: ...
