"""Extractor A360: lê o JSON exportado (ou ZIP), nunca executa o legado."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..inventory import Inventory
from ..patterns import A360_REGISTRY
from ..security.safe_zip import safe_zip
from ._shared import all_files


def _attribute_names(attributes: Any) -> list[str]:
    if isinstance(attributes, dict):
        return list(attributes.keys())
    if isinstance(attributes, list):
        return [item.get("name", "") for item in attributes if isinstance(item, dict)]
    return []


def _attribute_value(attributes: Any, name: str) -> str | None:
    if isinstance(attributes, dict):
        value = attributes.get(name)
        return value if isinstance(value, str) else None
    if isinstance(attributes, list):
        for item in attributes:
            if isinstance(item, dict) and item.get("name") == name:
                value = item.get("value")
                return value if isinstance(value, str) else None
    return None


def _preorder(nodes: list[dict]) -> Iterator[dict]:
    for node in nodes:
        yield node
        yield from _preorder(node.get("children") or [])


class A360Extractor:
    name: str = "a360"

    def detect(self, path: Path) -> bool:
        path = Path(path)
        if path.is_file():
            return path.suffix.lower() == ".zip"
        if not path.is_dir():
            return False
        return any(path.glob("*.json")) or any(path.glob("*.zip"))

    def extract(self, path: Path) -> Inventory:
        path = Path(path)
        if path.is_file() and path.suffix.lower() == ".zip":
            with safe_zip(path, path.parent) as extracted:
                return self._extract_dir(extracted)
        if path.is_dir():
            if any(path.glob("*.json")):
                return self._extract_dir(path)
            zips = sorted(path.glob("*.zip"))
            if zips:
                with safe_zip(zips[0], path) as extracted:
                    return self._extract_dir(extracted)
            return self._extract_dir(path)
        raise ValueError(f"origem A360 inválida: {path}")

    def _extract_dir(self, directory: Path) -> Inventory:
        inventory = Inventory(source_type="a360")
        inventory.files = all_files(directory)
        json_files = sorted(path.name for path in directory.glob("*.json"))

        for filename in json_files:
            document = json.loads((directory / filename).read_text(encoding="utf-8"))
            nodes = document.get("nodes", [])
            for line, node in enumerate(_preorder(nodes), start=1):
                package = node.get("packageName", "")
                command = node.get("commandName", "")
                attributes = node.get("attributes", {})
                base_fact = {
                    "attribute_names": _attribute_names(attributes),
                    "commandName": command,
                    "file": filename,
                    "line": line,
                    "packageName": package,
                }
                category = A360_REGISTRY.get((package, command))
                if category is None:
                    inventory.unknown_commands.append(base_fact)
                    continue
                if category == "credentials":
                    fact = dict(base_fact)
                    fact["reference"] = f"{filename}:{line}:credential-vault"
                    inventory.credentials.append(fact)
                elif category == "dependencies":
                    bot_name = _attribute_value(attributes, "botName")
                    target = f"{bot_name}.json" if bot_name else None
                    resolved = bool(target) and target in json_files
                    fact = dict(base_fact)
                    fact["resolution"] = "resolvida" if resolved else "não resolvida"
                    fact["target"] = target if resolved else None
                    inventory.dependencies.append(fact)
                else:
                    getattr(inventory, category).append(base_fact)
        return inventory
