"""Extractor .NET: heurísticas por linha em .cs/.vb; binário exige ILSpy antes."""

from __future__ import annotations

from pathlib import Path

from ..inventory import Inventory
from ..patterns import (
    DOTNET_BINARY_SUFFIXES,
    DOTNET_HTTP_MARKERS,
    DOTNET_IO_MARKERS,
    DOTNET_SOURCE_SUFFIXES,
)
from ._shared import all_files


class DotnetExtractor:
    name: str = "dotnet"

    def detect(self, path: Path) -> bool:
        path = Path(path)
        if not path.is_dir():
            return False
        if any(path.rglob("*.cs")) or any(path.rglob("*.vb")):
            return True
        return any(
            p.suffix.lower() in DOTNET_BINARY_SUFFIXES for p in path.rglob("*") if p.is_file()
        )

    def extract(self, path: Path) -> Inventory:
        path = Path(path)
        inventory = Inventory(source_type="dotnet")
        inventory.files = all_files(path)

        sources = sorted(
            p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in DOTNET_SOURCE_SUFFIXES
        )
        for source in sources:
            relative = str(source.relative_to(path)).replace("\\", "/")
            for lineno, text in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
                if any(marker in text for marker in DOTNET_HTTP_MARKERS):
                    inventory.http_calls.append(
                        {"file": relative, "line": lineno, "operation": "HttpClient"}
                    )
                if any(marker in text for marker in DOTNET_IO_MARKERS):
                    inventory.data_sources.append(
                        {"file": relative, "line": lineno, "operation": "File I/O"}
                    )

        binaries = sorted(
            p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in DOTNET_BINARY_SUFFIXES
        )
        for binary in binaries:
            relative = str(binary.relative_to(path)).replace("\\", "/")
            inventory.warnings.append(
                {"file": relative, "line": 1, "message": "decompile com ILSpy antes"}
            )
        return inventory
