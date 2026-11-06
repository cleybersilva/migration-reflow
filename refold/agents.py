"""Carrega a definição canônica de um agent (`.opencode/agents/<nome>.md`).

É a mesma fonte que gera `.claude/agents/` e `.github/chatmodes/`: o refold não tem
cópia própria dos prompts, então a paridade com os outros harnesses vem de graça.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

AGENTS_DIR = Path(".opencode") / "agents"
_PERMISSION_RE = re.compile(
    r"\{\s*action:\s*(?P<action>[\w-]+)\s*,\s*resource:\s*\"(?P<resource>[^\"]+)\"\s*,"
    r"\s*effect:\s*(?P<effect>allow|deny)\s*\}"
)
_NAME_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


class AgentError(ValueError):
    """Agent inexistente ou com definição que o refold não sabe aplicar com segurança."""


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    steps: int
    write_globs: tuple[str, ...]
    prompt: str


def _split(text: str) -> tuple[str, str]:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise AgentError("agent sem frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise AgentError("frontmatter sem fechamento `---`")
    return text[4:end], text[end + 4 :].lstrip("\n")


def parse_agent(name: str, text: str) -> AgentSpec:
    frontmatter, body = _split(text)
    description = ""
    steps = 0
    write_globs: list[str] = []
    for line in frontmatter.splitlines():
        if line.startswith("description:"):
            description = line.partition(":")[2].strip().strip('"').strip("'")
        elif line.startswith("steps:"):
            steps = int(line.partition(":")[2].strip())
        elif match := _PERMISSION_RE.search(line):
            if match["action"] == "edit" and match["effect"] == "allow":
                write_globs.append(match["resource"])
            elif match["effect"] == "allow":
                # Só `edit` tem tradução no refold; liberar shell, rede ou delegação
                # num agent exigiria uma decisão nova, não um silêncio aqui.
                raise AgentError(f"{name}: permissão `{match['action']}` allow não suportada")
    if not description or steps <= 0:
        raise AgentError(f"{name}: frontmatter precisa de description e steps > 0")
    return AgentSpec(name, description, steps, tuple(write_globs), body)


def load_agent(root: Path, name: str) -> AgentSpec:
    if not _NAME_RE.fullmatch(name):
        raise AgentError(f"nome de agent inválido: {name}")
    path = root / AGENTS_DIR / f"{name}.md"
    if not path.is_file():
        raise AgentError(f"agent não encontrado: {path}")
    return parse_agent(name, path.read_text(encoding="utf-8"))


def list_agents(root: Path) -> list[AgentSpec]:
    return [load_agent(root, p.stem) for p in sorted((root / AGENTS_DIR).glob("*.md"))]
