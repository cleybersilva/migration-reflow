"""Lint Robin mínimo e real: sem `.robin` no repo, não há nada a presumir validado."""

from __future__ import annotations

from pathlib import Path

from .security.scan import Finding

WHITELIST_PATH = Path("reference") / "robin-actions.md"


def lint_robin_files(root: Path) -> list[Finding]:
    robin_files = sorted(root.rglob("*.robin"))
    if not robin_files:
        return []
    whitelist = root / WHITELIST_PATH
    if not whitelist.is_file():
        return [
            Finding(
                str(WHITELIST_PATH).replace("\\", "/"),
                1,
                "whitelist_ausente",
                "reference/robin-actions.md não existe; nenhuma ação Robin pode ser validada",
            )
        ]
    return []
