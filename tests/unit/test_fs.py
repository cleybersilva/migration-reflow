"""Escrita atômica e lock por projeto — `reflow.fs` (Fase 3 de segurança)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from reflow.fs import LockError, lock_path_for, project_lock, write_json_atomic

ROOT = Path(__file__).resolve().parents[2]

HOLDER_SCRIPT = """
import sys
import time
from pathlib import Path

from reflow.fs import project_lock

with project_lock(Path(sys.argv[1]), timeout=5.0):
    print("held", flush=True)
    time.sleep(1.5)
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_write_json_atomic_replaces_content_and_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "00-manifest.json"
    write_json_atomic(target, {"status": "extracted"})
    write_json_atomic(target, {"status": "aprovado"})

    payload = json.loads(target.read_text(encoding="utf-8"))
    require(payload == {"status": "aprovado"}, "O conteúdo novo tem que substituir o antigo.")
    leftovers = sorted(p.name for p in target.parent.iterdir() if p.name != target.name)
    require(leftovers == [], f"Nenhum temporário pode sobrar da escrita atômica: {leftovers}.")


def test_project_lock_is_reentrant_and_stays_out_of_the_project(tmp_path: Path) -> None:
    out_dir = tmp_path / "output" / "quote-scraper"
    with project_lock(out_dir):
        with project_lock(out_dir, timeout=0.1):
            pass
        require(
            lock_path_for(out_dir) == tmp_path / "output" / "quote-scraper.lock",
            "O lock fica num arquivo irmão do diretório de saída.",
        )
        require(
            not (out_dir / "quote-scraper.lock").exists(),
            "O lock nunca é criado dentro do projeto em si.",
        )
    require(lock_path_for(out_dir).is_file(), "O arquivo de lock existe depois do uso.")


def test_project_lock_rejects_a_second_process(tmp_path: Path) -> None:
    """O lock tem que valer entre processos — dois terminais no mesmo projeto."""
    out_dir = tmp_path / "output" / "quote-scraper"
    process = subprocess.Popen(  # noqa: S603
        [sys.executable, "-c", HOLDER_SCRIPT, str(out_dir)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        line = process.stdout.readline()
        require(line.strip() == "held", f"O processo filho não conseguiu segurar o lock: {line!r}")
        with pytest.raises(LockError), project_lock(out_dir, timeout=0.3):
            pytest.fail("Não deveria adquirir o lock enquanto outro processo o segura.")
    finally:
        process.wait(timeout=15)
