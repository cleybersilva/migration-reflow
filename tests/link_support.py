"""Helper de teste: criar o link mais forte que o ambiente permite.

Junction via `cmd /c mklink /J` só existe no Windows. Como a CI roda também
em Linux (`ubuntu-latest`), o helper cria um **symlink** em POSIX — o
código testado (`is_unsafe_link()` usa `is_symlink() or is_junction()`)
acaba coberto nos dois caminhos, em vez de o teste quebrar por `cmd` não
existir.

Se o ambiente não permitir nenhum dos dois (ex.: Windows sem privilégio e
sem junction), o teste pula com `pytest.skip` — nunca falha por motivo
alheio ao código testado.

Compartilhado pelos testes de junction/symlink: uma implementação só
(reflow/extractors/a360.py, reflow/security/paths.py, dashboard/pipeline.py
dependem do mesmo comportamento).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def make_unsafe_link(link: Path, target: Path) -> None:
    """Aponta `link` para `target` como junction (Windows) ou symlink (POSIX)."""
    if os.name != "nt":
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"não foi possível criar symlink neste ambiente: {exc}")
        return
    result = subprocess.run(  # noqa: S603
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"não foi possível criar junction neste ambiente: {result.stderr.strip()}")
