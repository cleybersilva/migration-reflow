"""Lint real do `Main.robin` gerado — sem nunca interpretar a sintaxe interna do
Robin, que não está validada (ver AGENTS.md: "nunca inventar sintaxe Robin").

As checagens olham só o que o próprio pipeline controla:
- `notas-conversao.md` (lista as ações usadas) cruzado contra a whitelist;
- `README.md` do flow (precisa de um cabeçalho `# <nome do flow>`);
- o texto puro do `Main.robin`, para segredo atribuído, caminho UNC (nunca
  permitido) e caminho absoluto fora de `C:\\Users\\Public\\Documents\\`
  depois de resolver `..` **textualmente** (sem tocar o filesystem real —
  é só o texto do flow sendo lido, nunca um caminho sendo acessado), para
  que `C:\\Users\\Public\\Documents\\..\\..\\Windows\\...` não escape o
  prefixo permitido só porque a string começa com ele.
"""

from __future__ import annotations

import ntpath
import re
from pathlib import Path

from ..security.masking import SECRET_ASSIGNMENT_RE, is_placeholder_value, mask
from ..security.scan import Finding
from .whitelist import RobinAction, load_whitelist

WHITELIST_PATH = Path("reference") / "robin-actions.md"
ALLOWED_OUTPUT_PREFIX = "c:\\users\\public\\documents\\"
ABSOLUTE_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s\"'<>]*")
UNC_PATH_RE = re.compile(r"\\\\[^\s\"'<>\\]+\\[^\s\"'<>]*")
ACTION_REFERENCE_RE = re.compile(r"^-\s*`([^`]+)`", re.MULTILINE)
HEADER_RE = re.compile(r"^#\s+\S")


def _relative(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _check_secrets(relative: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in SECRET_ASSIGNMENT_RE.finditer(line):
            if not is_placeholder_value(match.group("value")):
                findings.append(
                    Finding(relative, lineno, "segredo_no_robin", mask(line.strip())[:120])
                )
    return findings


def _is_allowed_output_path(raw: str) -> bool:
    """True só se `raw`, depois de resolver `..` textualmente, continuar
    dentro de `C:\\Users\\Public\\Documents\\`. Comparação por componente de
    caminho (via `ntpath.normpath`), nunca por prefixo de string bruta —
    senão `...Documents\\..\\..\\Windows\\...` passava, porque a string
    começa com o prefixo permitido antes de o `..` ser interpretado."""
    normalized = ntpath.normpath(raw).lower()
    return (normalized + "\\").startswith(ALLOWED_OUTPUT_PREFIX)


def _check_absolute_paths(relative: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in ABSOLUTE_PATH_RE.finditer(line):
            if not _is_allowed_output_path(match.group(0)):
                findings.append(
                    Finding(relative, lineno, "caminho_fora_do_permitido", match.group(0))
                )
        for match in UNC_PATH_RE.finditer(line):
            findings.append(Finding(relative, lineno, "caminho_unc_nao_permitido", match.group(0)))
    return findings


def _check_actions_against_whitelist(
    root: Path, notes_path: Path, whitelist: dict[str, RobinAction]
) -> list[Finding]:
    if not notes_path.is_file():
        return [
            Finding(
                _relative(root, notes_path),
                1,
                "notas_conversao_ausente",
                "notas-conversao.md é obrigatório ao lado de Main.robin, listando as ações usadas",
            )
        ]
    relative = _relative(root, notes_path)
    text = notes_path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for match in ACTION_REFERENCE_RE.finditer(text):
        name = match.group(1)
        if name not in whitelist:
            findings.append(
                Finding(
                    relative,
                    1,
                    "acao_fora_da_whitelist",
                    f"ação citada em notas-conversao.md mas ausente da whitelist: {name}",
                )
            )
    return findings


def _check_flow_header(root: Path, readme_path: Path) -> list[Finding]:
    if not readme_path.is_file():
        return [
            Finding(
                _relative(root, readme_path),
                1,
                "cabecalho_ausente",
                "README.md do flow é obrigatório, começando com `# <nome do flow>`",
            )
        ]
    lines = [line for line in readme_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or not HEADER_RE.match(lines[0]):
        return [
            Finding(
                _relative(root, readme_path),
                1,
                "cabecalho_ausente",
                "README.md precisa começar com um cabeçalho `# <nome do flow>`",
            )
        ]
    return []


def _lint_one(root: Path, robin_file: Path, whitelist: dict[str, RobinAction]) -> list[Finding]:
    relative = _relative(root, robin_file)
    text = robin_file.read_text(encoding="utf-8")
    findings = _check_secrets(relative, text) + _check_absolute_paths(relative, text)
    findings += _check_actions_against_whitelist(
        root, robin_file.parent / "notas-conversao.md", whitelist
    )
    findings += _check_flow_header(root, robin_file.parent / "README.md")
    return findings


def lint_robin_files(root: Path, project: str | None = None) -> list[Finding]:
    scope = root / "output" / project if project else root
    robin_files = sorted(scope.rglob("Main.robin")) if scope.is_dir() else []
    if not robin_files:
        return []

    whitelist = load_whitelist(root)
    if not whitelist:
        return [
            Finding(
                str(WHITELIST_PATH).replace("\\", "/"),
                1,
                "whitelist_ausente",
                "reference/robin-actions.md não existe ou está vazia; nenhuma ação é validável",
            )
        ]

    findings: list[Finding] = []
    for robin_file in robin_files:
        findings.extend(_lint_one(root, robin_file, whitelist))
    return findings
