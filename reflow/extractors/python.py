"""Extractor Python: só AST, resolve aliases de import, nunca executa o código."""

from __future__ import annotations

import ast
from pathlib import Path

from ..inventory import Inventory
from ._shared import all_files

HTTP_OPERATIONS = {
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "requests.patch",
    "requests.head",
    "requests.options",
    "httpx.get",
    "httpx.post",
    "httpx.put",
    "httpx.delete",
    "urllib.request.urlopen",
    "http.client.HTTPConnection",
}
DATA_SOURCE_OPERATIONS = {
    "open",
    "csv.writer",
    "csv.reader",
    "sqlite3.connect",
    "pandas.read_csv",
    "pandas.read_excel",
    "openpyxl.load_workbook",
}


class PythonExtractor:
    name = "python"

    def detect(self, path: Path) -> bool:
        path = Path(path)
        return path.is_dir() and any(path.rglob("*.py"))

    def extract(self, path: Path) -> Inventory:
        path = Path(path)
        inventory = Inventory(source_type="python")
        inventory.files = all_files(path)

        sources = sorted(p for p in path.rglob("*.py") if p.is_file())
        for source in sources:
            relative = str(source.relative_to(path)).replace("\\", "/")
            text = source.read_text(encoding="utf-8")
            try:
                tree = ast.parse(text, filename=relative)
            except SyntaxError as exc:
                inventory.warnings.append(
                    {"file": relative, "line": exc.lineno or 1, "message": "sintaxe inválida"}
                )
                continue
            self._scan(tree, relative, inventory)

        inventory.dependencies.sort(key=lambda item: item["line"])
        inventory.http_calls.sort(key=lambda item: item["line"])
        inventory.data_sources.sort(key=lambda item: item["line"])
        return inventory

    def _scan(self, tree: ast.AST, relative: str, inventory: Inventory) -> None:
        alias_map: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name
                    alias_map[local] = alias.name
                    inventory.dependencies.append(
                        {
                            "file": relative,
                            "line": node.lineno,
                            "kind": "import",
                            "module": alias.name,
                        }
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    full = f"{node.module}.{alias.name}"
                    alias_map[local] = full
                    inventory.dependencies.append(
                        {"file": relative, "line": node.lineno, "kind": "import", "module": full}
                    )

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            operation = self._resolve(node, alias_map)
            if operation is None:
                continue
            entry = {"file": relative, "line": node.lineno, "operation": operation}
            if operation in HTTP_OPERATIONS:
                inventory.http_calls.append(entry)
            elif operation in DATA_SOURCE_OPERATIONS:
                inventory.data_sources.append(entry)

    @staticmethod
    def _resolve(node: ast.Call, alias_map: dict[str, str]) -> str | None:
        func = node.func
        if isinstance(func, ast.Name):
            if func.id == "open":
                return "open"
            return alias_map.get(func.id)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            base = alias_map.get(func.value.id)
            if base:
                return f"{base}.{func.attr}"
        return None
