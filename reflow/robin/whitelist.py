"""Leitura da whitelist Robin e da tabela verdade A360 → PAD (reference/).

Parser simples e deliberadamente ingênuo (linha a linha), suficiente para o
formato fixo dos dois arquivos editáveis — não é um parser de Markdown geral.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROBIN_ACTIONS_PATH = Path("reference") / "robin-actions.md"
A360_TO_PAD_PATH = Path("reference") / "a360-to-pad.md"

_ACTION_HEADING_RE = re.compile(r"^### `([^`]+)`\s*$")
_STATUS_LINE_RE = re.compile(r"^-\s*Status:\s*(\[[^\]]+\])\s*$")
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")


@dataclass
class RobinAction:
    name: str
    status: str

    @property
    def validated(self) -> bool:
        return self.status.lower().startswith("[validado")


def load_whitelist(root: Path) -> dict[str, RobinAction]:
    """Lê `reference/robin-actions.md`: uma ação por seção `### \\`Módulo.Ação\\``."""
    path = root / ROBIN_ACTIONS_PATH
    if not path.is_file():
        return {}

    actions: dict[str, RobinAction] = {}
    current_name: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = _ACTION_HEADING_RE.match(line)
        if heading:
            current_name = heading.group(1)
            continue
        status = _STATUS_LINE_RE.match(line)
        if status and current_name:
            actions[current_name] = RobinAction(name=current_name, status=status.group(1))
            current_name = None
    return actions


def _parse_markdown_table(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for raw_line in text.splitlines():
        match = _TABLE_ROW_RE.match(raw_line.strip())
        if not match:
            continue
        cells = [cell.strip() for cell in match.group(1).split("|")]
        if header is None:
            header = cells
            continue
        if all(set(cell) <= {"-", " "} for cell in cells):
            continue  # linha separadora |---|---|
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells, strict=True)))
    return rows


def load_truth_table(root: Path) -> list[dict[str, str]]:
    """Lê `reference/a360-to-pad.md`: uma linha de tabela Markdown por mapeamento."""
    path = root / A360_TO_PAD_PATH
    if not path.is_file():
        return []
    return _parse_markdown_table(path.read_text(encoding="utf-8"))


_NO_ACTION_MARKERS = frozenset({"", "—", "-"})


def truth_table_action_name(row: dict[str, str]) -> str | None:
    """Extrai o nome da ação Robin de uma linha da tabela verdade (remove `` ` ``)."""
    raw = row.get("Ação PAD equivalente", "").strip().strip("`")
    return None if raw in _NO_ACTION_MARKERS else raw
