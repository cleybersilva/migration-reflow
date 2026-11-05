"""Varredura real (não fictícia) de segredos/PII nos arquivos que seriam versionados.

Duas varreduras, propositalmente distintas:
- `scan_repository` lê a working tree de tudo que `git` versionaria
  (`git ls-files --cached --others --exclude-standard`), caindo para uma
  varredura simples de diretório fora de um repositório git. Usada por fluxos
  que inspecionam o estado local (ex.: checagens manuais).
- `scan_staged` lê o índice do Git — o blob preparado (stage 0) de cada
  arquivo com mudança pronta para commit —, nunca a working tree. É o que o
  hook de pre-commit precisa: um segredo preparado tem que bloquear mesmo que
  a working tree tenha sido editada depois do `git add`, e um segredo que só
  existe localmente (não preparado) não deve bloquear o commit.

Uma linha com o marcador `reflow:allow-secret` só é pulada dentro de
`tests/` (fixtures/teste sintético) ou dentro dos próprios módulos do
detector (`reflow/security/scan.py`, `reflow/security/masking.py`); fora
disso o marcador é ignorado — nunca é uma forma livre de silenciar um
segredo real em qualquer outro arquivo do repositório.

Única outra isenção, também estreita: os arquivos de terceiros vendorizados
em `reference/vendor/pad-robin-kb/` (KB Robin, CC BY 4.0) são pulados só
enquanto o conteúdo bater byte a byte com o sha256 travado em
`manifest.json` (ver `reflow/robin/kb.py` e ADR-029). Os exemplos de lá
trazem argumentos Robin de senha seguidos de um literal `$'''...'''` de
exemplo, que a regex lê como atribuição de segredo. Qualquer edição no arquivo derruba a isenção e
ele volta a ser varrido normalmente; o manifesto e o README da pasta são
sempre varridos.
Os achados são reportados já mascarados (ver security/masking.py) — o próprio
scan nunca ecoa um segredo real no terminal.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .masking import CNPJ_RE, CPF_RE, SECRET_ASSIGNMENT_RE, is_safe_assignment, mask

IGNORED_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
INTERNAL_DOMAIN_RE = re.compile(r"(?i)\bitau[a-zç]*\b|\.corp\b")  # reflow:allow-secret
ALLOW_MARKER = "reflow:allow-secret"
ALLOW_MARKER_PERMITTED_PREFIXES = ("tests/",)
ALLOW_MARKER_PERMITTED_FILES = frozenset(
    {
        "reflow/security/scan.py",
        "reflow/security/masking.py",
    }
)


@dataclass
class Finding:
    file: str
    line: int
    pattern: str
    excerpt: str


class StagedScanError(RuntimeError):
    """O índice do Git não pôde ser lido — nunca tratar isso como 'sem achados'."""


def _candidate_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],  # noqa: S607
            cwd=root,
            capture_output=True,
            check=True,
        )
        names = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        return [root / name for name in names if name]
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and not any(part in IGNORED_DIR_NAMES for part in path.parts)
        ]


def _run_git(args: list[str], root: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=False,
    )


def _staged_file_names(root: Path) -> list[str]:
    """Nomes (delimitados por NUL) dos arquivos com mudança preparada para commit."""
    result = _run_git(["diff", "--cached", "--name-only", "-z"], root)
    if result.returncode != 0:
        raise StagedScanError(
            "não foi possível ler o índice do Git (git diff --cached falhou); "
            "commit bloqueado em vez de seguir sem verificar."
        )
    names = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return [name for name in names if name]


def _read_staged_blob(root: Path, relative: str) -> bytes | None:
    """Lê o blob preparado (stage 0) de `relative` — nunca a working tree.

    `:relative` nunca começa com `-`, então mesmo um nome de arquivo
    começando com hífen não é interpretado como opção do `git show`.
    Retorna None quando o caminho não está mais no índice (ex.: remoção
    preparada) — não há conteúdo preparado para inspecionar nesse caso.
    """
    result = _run_git(["show", f":{relative}"], root)
    if result.returncode != 0:
        return None
    return result.stdout


def _pinned_vendor_hashes(root: Path) -> dict[str, str]:
    # Import tardio: reflow.robin importa este módulo (Finding).
    from ..robin.kb import pinned_hashes

    return pinned_hashes(root)


def _is_pinned_vendor_file(relative: str, content: bytes, pinned: dict[str, str]) -> bool:
    expected = pinned.get(relative.replace("\\", "/"))
    return expected is not None and hashlib.sha256(content).hexdigest() == expected


def _allow_marker_is_permitted(relative: str) -> bool:
    normalized = relative.replace("\\", "/")
    if normalized in ALLOW_MARKER_PERMITTED_FILES:
        return True
    return normalized.startswith(ALLOW_MARKER_PERMITTED_PREFIXES)


def _scan_line(relative: str, lineno: int, text: str) -> list[Finding]:
    if ALLOW_MARKER in text and _allow_marker_is_permitted(relative):
        return []
    findings: list[Finding] = []
    excerpt = mask(text.strip())[:120]
    if CPF_RE.search(text) or CNPJ_RE.search(text):
        findings.append(Finding(relative, lineno, "cpf_cnpj", excerpt))
    if INTERNAL_DOMAIN_RE.search(text):
        findings.append(Finding(relative, lineno, "dominio_interno", excerpt))
    for match in SECRET_ASSIGNMENT_RE.finditer(text):
        if not is_safe_assignment(text, match):
            findings.append(Finding(relative, lineno, "segredo_atribuido", excerpt))
    return findings


def scan_bytes(content: bytes, file: str) -> list[Finding]:
    """Varre bytes arbitrários (não um arquivo do repositório) pelos mesmos padrões.

    Usado pelo dashboard local para checar uma saída isolada antes de servi-la
    ou gravá-la, sem exigir que o conteúdo já esteja em disco sob `root`.
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return []
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        findings.extend(_scan_line(file, lineno, line))
    return findings


def scan_repository(root: Path) -> list[Finding]:
    """Varre a working tree de tudo que seria versionado — ver módulo para o
    contraste com `scan_staged` (índice)."""
    findings: list[Finding] = []
    pinned = _pinned_vendor_hashes(root)
    for path in _candidate_files(root):
        if not path.is_file():
            continue
        relative = str(path.relative_to(root)).replace("\\", "/")
        try:
            content = path.read_bytes()
            text = content.decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _is_pinned_vendor_file(relative, content, pinned):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            findings.extend(_scan_line(relative, lineno, line))
    return findings


def scan_staged(root: Path) -> list[Finding]:
    """Varre só o conteúdo preparado para o próximo commit (índice do Git).

    Usada pelo hook de pre-commit: um segredo preparado (`git add`) bloqueia
    mesmo que a working tree tenha sido alterada depois; um segredo que só
    existe na working tree, mas nunca foi `git add`, não bloqueia.

    Levanta `StagedScanError` se o índice não puder ser lido — nunca retorna
    `[]` nesse caso, para não dar falso "sem achados".  Conteúdo binário ou
    que não decodifica como UTF-8 gera um achado explícito
    (`conteudo_nao_utf8`) em vez de ser silenciosamente pulado: o commit é
    bloqueado e o humano decide, em vez de o scan alegar que inspecionou algo
    que não leu.
    """
    findings: list[Finding] = []
    pinned = _pinned_vendor_hashes(root)
    for relative in _staged_file_names(root):
        content = _read_staged_blob(root, relative)
        if content is None:
            continue
        if _is_pinned_vendor_file(relative, content, pinned):
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(
                Finding(
                    relative,
                    0,
                    "conteudo_nao_utf8",
                    "binário ou não UTF-8 — conteúdo não inspecionado por este scan",
                )
            )
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            findings.extend(_scan_line(relative, lineno, line))
    return findings
