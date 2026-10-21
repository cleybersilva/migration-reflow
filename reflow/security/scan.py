"""Varredura real (não fictícia) de segredos/PII nos arquivos que seriam versionados.

Checa só o que `git` versionaria (`git ls-files --cached --others --exclude-standard`),
caindo para uma varredura simples de diretório fora de um repositório git.
Uma linha com o marcador `reflow:allow-secret` é pulada; use só para fixtures
sintéticas ou para a própria definição do detector, nunca para mascarar valor real.
Os achados são reportados já mascarados (ver security/masking.py) — o próprio
scan nunca ecoa um segredo real no terminal.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .masking import CNPJ_RE, CPF_RE, SECRET_ASSIGNMENT_RE, is_placeholder_value, mask

IGNORED_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
INTERNAL_DOMAIN_RE = re.compile(r"(?i)\bitau[a-zç]*\b|\.corp\b")  # reflow:allow-secret
ALLOW_MARKER = "reflow:allow-secret"


@dataclass
class Finding:
    file: str
    line: int
    pattern: str
    excerpt: str


def _candidate_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return [root / name for name in result.stdout.splitlines() if name]
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and not any(part in IGNORED_DIR_NAMES for part in path.parts)
        ]


def _scan_line(relative: str, lineno: int, text: str) -> list[Finding]:
    if ALLOW_MARKER in text:
        return []
    findings: list[Finding] = []
    excerpt = mask(text.strip()[:120])
    if CPF_RE.search(text) or CNPJ_RE.search(text):
        findings.append(Finding(relative, lineno, "cpf_cnpj", excerpt))
    if INTERNAL_DOMAIN_RE.search(text):
        findings.append(Finding(relative, lineno, "dominio_interno", excerpt))
    for match in SECRET_ASSIGNMENT_RE.finditer(text):
        if not is_placeholder_value(match.group("value")):
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
    findings: list[Finding] = []
    for path in _candidate_files(root):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative = str(path.relative_to(root)).replace("\\", "/")
        for lineno, line in enumerate(text.splitlines(), start=1):
            findings.extend(_scan_line(relative, lineno, line))
    return findings
