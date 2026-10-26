"""Escrita atômica e lock por projeto — stdlib, sem rede.

Duas garantias para os artefatos de `output/<projeto>/`:

1. `write_json_atomic()` nunca deixa arquivo pela metade: grava num
   temporário do mesmo diretório e troca com `os.replace` (atômico no
   Windows e no POSIX). Se o processo morrer no meio, o arquivo anterior
   continua íntegro — nada de manifesto truncado versionado por engano.
2. `project_lock()` impede dois processos de escreverem o mesmo projeto ao
   mesmo tempo (`extract` × `checkpoint`, dois terminais). O lock fica num
   arquivo irmão do diretório de saída (`<nome>.lock`) e é retido pelo
   sistema operacional: se o processo morrer, o lock é liberado sozinho —
   nenhum lock velho trava o projeto para sempre.

Reentrante no mesmo processo: chamar `project_lock` de novo sobre o mesmo
diretório enquanto o lock já está na mão (ex.: `extract_to` dentro de
`_extract_one`) só cede a vez, em vez de se travar.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

if os.name == "nt":
    import msvcrt
else:
    import fcntl

DEFAULT_TIMEOUT_SECONDS = 10.0
_POLL_SECONDS = 0.05

_held_locks: set[str] = set()


class LockError(RuntimeError):
    """Outro processo já está escrevendo neste projeto."""


def write_json_atomic(path: Path, payload: dict) -> None:
    """Grava `payload` como JSON: ou o arquivo novo por inteiro, ou o antigo intacto."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def lock_path_for(out_dir: Path) -> Path:
    """`output/<nome>` → `output/<nome>.lock` (irmão, nunca dentro do projeto)."""
    out_dir = Path(out_dir)
    return out_dir.parent / f"{out_dir.name}.lock"


def _try_lock(handle: IO[bytes]) -> bool:
    """Tenta travar 1 byte sem bloquear. `False` = alguém já tem o lock."""
    try:
        if os.name == "nt":
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(handle: IO[bytes]) -> None:
    try:
        if os.name == "nt":
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(handle, fcntl.LOCK_UN)
    except OSError:
        # O SO libera o lock sozinho quando o handle fecha; nada a fazer aqui.
        return


@contextmanager
def project_lock(out_dir: Path, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> Iterator[None]:
    """Segura o lock de escrita de `out_dir` enquanto o bloco executar.

    Levanta `LockError` se outro processo segurar o lock por mais de
    `timeout` segundos — falha restritiva em vez de escrever por cima.
    """
    out_dir = Path(out_dir)
    key = os.path.abspath(out_dir)
    if key in _held_locks:
        yield
        return

    lock_path = lock_path_for(out_dir)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            if _try_lock(handle):
                acquired = True
                break
            if time.monotonic() >= deadline:
                raise LockError(
                    f"outro processo já está escrevendo em {out_dir} (lock: {lock_path})"
                )
            time.sleep(_POLL_SECONDS)
        _held_locks.add(key)
        try:
            yield
        finally:
            _held_locks.discard(key)
    finally:
        if acquired:
            _unlock(handle)
        handle.close()
