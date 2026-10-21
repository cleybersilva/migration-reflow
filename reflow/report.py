"""Relatório de lote: uma linha por projeto, só com o que já existe.

Nunca presume uma fase futura — projeto ainda não classificado mostra `—` no
veredito, ainda não convertido mostra 0 flows. Isso não declara pronto o que
ainda não foi feito.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .robin.whitelist import load_whitelist

_ACTION_REFERENCE_RE = re.compile(r"^-\s*`([^`]+)`", re.MULTILINE)
_FRONTMATTER_FIELD_RE = re.compile(r"^(\w+):\s*(.+)$")
_HEADER = (
    "| Projeto | Origem | Estado | Veredito | Flows | TODO reflow "
    "| Ações não validadas | Desconhecidos |"
)
_SEPARATOR = "| --- | --- | --- | --- | --- | --- | --- | --- |"


def _read_manifest(project_dir: Path) -> dict | None:
    path = project_dir / "00-manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_unknown_commands_count(project_dir: Path) -> int:
    path = project_dir / "01-inventory" / "inventory.json"
    if not path.is_file():
        return 0
    inventory = json.loads(path.read_text(encoding="utf-8"))
    return len(inventory.get("unknown_commands", []))


def _read_verdict(project_dir: Path) -> str:
    path = project_dir / "03-classification" / "classification.md"
    if not path.is_file():
        return "—"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return "—"
    end = text.find("\n---", 4)
    if end == -1:
        return "—"
    for line in text[4:end].splitlines():
        match = _FRONTMATTER_FIELD_RE.match(line)
        if match and match.group(1) == "verdict":
            return match.group(2).strip()
    return "—"


def _count_flows_and_todos(project_dir: Path) -> tuple[int, int]:
    pad_dir = project_dir / "04-pad"
    if not pad_dir.is_dir():
        return 0, 0
    flows = sorted(pad_dir.glob("*/Main.robin"))
    todo_count = sum(flow.read_text(encoding="utf-8").count("TODO reflow") for flow in flows)
    return len(flows), todo_count


def _count_unvalidated_actions_used(root: Path, project_dir: Path) -> int:
    pad_dir = project_dir / "04-pad"
    if not pad_dir.is_dir():
        return 0
    whitelist = load_whitelist(root)
    used: set[str] = set()
    for notes in pad_dir.glob("*/notas-conversao.md"):
        for match in _ACTION_REFERENCE_RE.finditer(notes.read_text(encoding="utf-8")):
            action = whitelist.get(match.group(1))
            if action is not None and not action.validated:
                used.add(match.group(1))
    return len(used)


def build_batch_report(root: Path) -> str:
    output_dir = root / "output"
    rows: list[str] = []
    if output_dir.is_dir():
        for project_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
            manifest = _read_manifest(project_dir)
            if manifest is None:
                continue
            flows, todos = _count_flows_and_todos(project_dir)
            estado = (
                "Extraído" if manifest.get("status") == "extracted" else manifest.get("status", "—")
            )
            rows.append(
                f"| {manifest['project']} | {manifest['source_type']} | {estado} | "
                f"{_read_verdict(project_dir)} | {flows} | {todos} | "
                f"{_count_unvalidated_actions_used(root, project_dir)} | "
                f"{_read_unknown_commands_count(project_dir)} |"
            )

    lines = ["# Relatório de extração", "", _HEADER, _SEPARATOR, *rows]
    return "\n".join(lines) + "\n"
