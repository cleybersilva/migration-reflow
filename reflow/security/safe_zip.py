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
DEFAULT_MAX_FILE_COUNT = 10_000

# CON/PRN/AUX/NUL/COM1-9/LPT1-9 são reservados pelo Windows mesmo com
# extensão (`con.txt` tropeça igual a `con`) — nunca um nome de arquivo de
# verdade extraível.
RESERVED_WINDOWS_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{digit}" for digit in range(1, 10)}
    | {f"lpt{digit}" for digit in range(1, 10)}
)


def _is_safe_member(name: str) -> bool:
    if not name or name.endswith("/"):
        return True
    if name.startswith("/") or name.startswith("\\"):
        return False
    if ":" in name:
        # Cobre caminho absoluto com letra de unidade (`C:\...`) e Alternate
        # Data Stream do NTFS (`arquivo.txt:oculto`) — nenhum dos dois é um
        # nome de arquivo real dentro do ZIP.
        return False
    parts = PurePosixPath(name.replace("\\", "/")).parts
    if ".." in parts:
        return False
    for part in parts:
        stem = part.split(".", 1)[0].strip().lower()
        if stem in RESERVED_WINDOWS_NAMES:
            return False
        # Espaço/ponto no final de um componente: o Windows ignora na hora de
        # criar o arquivo, então dois membros diferentes no ZIP (um com, um
        # sem) podem colidir no mesmo arquivo real na extração.
        if part != part.rstrip(". "):
            return False
    return True


def _windows_collision_key(name: str) -> str:
    """Chave de colisão no Windows: comparação por componente, sem
    diferenciar maiúsc./minúsc. (NTFS/Windows são case-insensitive, o ZIP
    não é — dois membros diferentes no arquivo podem ser o mesmo arquivo na
    extração)."""
    parts = PurePosixPath(name.replace("\\", "/")).parts
    return "/".join(part.lower() for part in parts)


@contextmanager
def safe_zip(
    archive_path: Path,
    dest_dir: Path,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
    max_file_count: int = DEFAULT_MAX_FILE_COUNT,
) -> Iterator[Path]:
    """Valida limites e caminhos do ZIP, extrai em pasta temporária local e limpa ao sair."""
    dest_dir = Path(dest_dir)
    with zipfile.ZipFile(archive_path) as bundle:
        members = bundle.infolist()
        if len(members) > max_file_count:
            raise ValueError(
                f"ZIP excede a quantidade máxima de arquivos permitida: {len(members)}"
            )
        total = 0
        seen_collision_keys: dict[str, str] = {}
        for info in members:
            if not _is_safe_member(info.filename):
                raise ValueError(f"Caminho inseguro no ZIP: {info.filename}")
            if not info.filename.endswith("/"):
                collision_key = _windows_collision_key(info.filename)
                previous = seen_collision_keys.get(collision_key)
                if previous is not None and previous != info.filename:
                    raise ValueError(
                        "Colisão de nomes no Windows (case-insensitive) no ZIP: "
                        f"{previous!r} e {info.filename!r}"
                    )
                seen_collision_keys[collision_key] = info.filename
            if info.file_size > max_file_size:
                raise ValueError(f"Arquivo excede o tamanho máximo permitido: {info.filename}")
            total += info.file_size
            if total > max_total_size:
                raise ValueError("ZIP excede o tamanho total permitido.")

        extract_dir = Path(tempfile.mkdtemp(prefix=".reflow-zip-", dir=dest_dir))
        try:
            for info in members:
                if info.filename.endswith("/"):
                    continue
                target = extract_dir / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, open(target, "wb") as handle:
                    handle.write(source.read())
            yield extract_dir
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)
