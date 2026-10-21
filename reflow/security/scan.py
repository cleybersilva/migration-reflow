"""Varredura real (não fictícia) de segredos/PII nos arquivos que seriam versionados.

Checa só o que `git` versionaria (`git ls-files --cached --others --exclude-standard`),
caindo para uma varredura simples de diretório fora de um repositório git.
Uma linha com o marcador `reflow:allow-secret` é pulada; use só para fixtures
sintéticas ou para a própria definição do detector, nunca para mascarar valor real.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

IGNORED_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}

CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
INTERNAL_DOMAIN_RE = re.compile(r"(?i)\bitau[a-zç]*\b|\.corp\b")  # reflow:allow-secret
ASSIGNED_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|private[_-]?key"
    r"|token|bearer|authorization|connection[_-]?string)\b"
    r"\s*[:=]\s*(?P<quote>['\"]?)(?P<value>[^'\"\s]+)(?P=quote)"
)
PLACEHOLDER_VALUES = {"", "xxx", "changeme", "todo", "placeholder"}


@dataclass
class Finding:
    file: str
    line: int
    pattern: str
    excerpt: str


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped or stripped.lower() in PLACEHOLDER_VALUES:
        return True
    if stripped.startswith("{env:") and stripped.endswith("}"):
        return True
    lowered = stripped.lower()
    return "synthetic" in lowered or lowered.startswith("not-a-real")


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


ALLOW_MARKER = "reflow:allow-secret"


def _scan_line(relative: str, lineno: int, text: str) -> list[Finding]:
    if ALLOW_MARKER in text:
        return []
    findings: list[Finding] = []
    excerpt = text.strip()[:120]
    if CPF_RE.search(text) or CNPJ_RE.search(text):
        findings.append(Finding(relative, lineno, "cpf_cnpj", excerpt))
    if INTERNAL_DOMAIN_RE.search(text):
        findings.append(Finding(relative, lineno, "dominio_interno", excerpt))
    for match in ASSIGNED_SECRET_RE.finditer(text):
        if not _is_placeholder(match.group("value")):
            findings.append(Finding(relative, lineno, "segredo_atribuido", excerpt))
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
