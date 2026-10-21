"""Extração segura de ZIP, sempre por membro (nunca `extractall` direto)."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

DEFAULT_MAX_FILE_SIZE = 50_000_000
DEFAULT_MAX_TOTAL_SIZE = 200_000_000


def _is_safe_member(name: str) -> bool:
    if not name or name.endswith("/"):
        return True
    if name.startswith("/") or name.startswith("\\"):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    parts = PurePosixPath(name.replace("\\", "/")).parts
    return ".." not in parts


@contextmanager
def safe_zip(
    archive_path: Path,
    dest_dir: Path,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
) -> Iterator[Path]:
    """Valida limites e caminhos do ZIP, extrai em pasta temporária local e limpa ao sair."""
    dest_dir = Path(dest_dir)
    with zipfile.ZipFile(archive_path) as bundle:
        total = 0
        for info in bundle.infolist():
            if not _is_safe_member(info.filename):
                raise ValueError(f"Caminho inseguro no ZIP: {info.filename}")
            if info.file_size > max_file_size:
                raise ValueError(f"Arquivo excede o tamanho máximo permitido: {info.filename}")
            total += info.file_size
            if total > max_total_size:
                raise ValueError("ZIP excede o tamanho total permitido.")

        extract_dir = Path(tempfile.mkdtemp(prefix=".reflow-zip-", dir=dest_dir))
        try:
            for info in bundle.infolist():
                if info.filename.endswith("/"):
                    continue
                target = extract_dir / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, open(target, "wb") as handle:
                    handle.write(source.read())
            yield extract_dir
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)
