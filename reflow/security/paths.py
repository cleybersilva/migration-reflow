"""Contenção de caminho — fonte única para symlink/junction e caminho UNC.

Usado antes de ler ou gravar conteúdo de um projeto em `input/<projeto>`
(extractors, manifesto) e pela listagem de projetos do dashboard. Em
qualquer dúvida, falha de forma restritiva (ver AGENTS.md): nunca segue um
link para fora do diretório esperado, nunca ignora em silêncio.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

UNC_PREFIX_RE = re.compile(r"^(?:\\\\|//)[^\\/]+")


class UnsafePathError(ValueError):
    """Caminho fora do sandbox esperado: symlink/junction ou UNC."""


def is_unc_path(raw: str) -> bool:
    """`\\\\server\\share\\...` ou `//server/share/...` — nunca é um caminho local."""
    return bool(UNC_PREFIX_RE.match(raw))


def is_unsafe_link(path: Path) -> bool:
    """True se `path` for um symlink ou uma junction (reparse point do Windows)."""
    try:
        return path.is_symlink() or path.is_junction()
    except OSError:
        # Não dá para classificar com segurança: trata como inseguro.
        return True


def reject_unsafe_links(root: Path) -> None:
    """Levanta `UnsafePathError` se `root`, ou qualquer entrada abaixo dele,
    for symlink/junction. Nunca segue o link para decidir depois — recusa
    o projeto inteiro, que é a opção restritiva e simples de auditar.
    """
    root = Path(root)
    if is_unsafe_link(root):
        raise UnsafePathError(f"symlink/junction inseguro: {root}")
    if not root.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        for name in (*dirnames, *filenames):
            candidate = current / name
            if is_unsafe_link(candidate):
                raise UnsafePathError(f"symlink/junction inseguro: {candidate}")
