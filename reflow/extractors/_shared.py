"""Utilitários compartilhados pelos extractors."""

from __future__ import annotations

from pathlib import Path


def all_files(root: Path) -> list[str]:
    """Lista estável (ordenada) de todos os arquivos de um diretório, caminho relativo."""
    return sorted(
        str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file()
    )
