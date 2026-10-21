"""Gera `.github/chatmodes/*.chatmode.md` a partir de `.opencode/agents/*.md`.

Fonte da verdade: `.opencode/agents/` (mesma usada por `sync_agents.py` para os
espelhos Claude). `.github/chatmodes/*.chatmode.md` é gerado — não editar à
mão. Depois de mudar um agent, rode:

    uv run python scripts/sync_agents.py
    uv run python scripts/sync_copilot.py

Diferença importante de honestidade: o GitHub Copilot Chat não tem um motor
de permissão por recurso como o OpenCode (`permissions` no frontmatter aqui
não impõe nada no Copilot). Por isso todo chatmode gerado ganha um aviso
explícito de que a restrição de escopo é só por instrução, não por bloqueio
técnico — para nunca sugerir uma garantia que este harness não oferece.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / ".opencode" / "agents"
TARGET_DIR = ROOT / ".github" / "chatmodes"
COPILOT_TOOLS = "['codebase', 'search', 'editFiles']"

SCOPE_WARNING = (
    "\n**Aviso de modo (Copilot):** diferente do OpenCode, o Copilot Chat não "
    "impõe restrição de arquivo por permissão — a única salvaguarda contra "
    "editar fora do escopo descrito acima é esta instrução. Siga-a à risca "
    "mesmo sem bloqueio técnico do harness.\n"
)


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("agent sem frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("frontmatter sem fechamento `---`")
    frontmatter = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    return frontmatter, body


def _extract_description(frontmatter: str) -> str:
    for line in frontmatter.splitlines():
        if line.startswith("description:"):
            return line.partition(":")[2].strip().strip('"').strip("'")
    raise ValueError("agent sem description no frontmatter")


def render_chatmode(description: str, body: str) -> str:
    header = f"---\ndescription: {description}\ntools: {COPILOT_TOOLS}\n---\n\n"
    return header + body.rstrip("\n") + "\n" + SCOPE_WARNING


def sync() -> list[Path]:
    if not SOURCE_DIR.is_dir():
        return []
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source in sorted(SOURCE_DIR.glob("*.md")):
        frontmatter, body = _split_frontmatter(source.read_text(encoding="utf-8"))
        description = _extract_description(frontmatter)
        target = TARGET_DIR / f"{source.stem}.chatmode.md"
        target.write_text(render_chatmode(description, body), encoding="utf-8")
        written.append(target)
    return written


def main() -> int:
    for path in sync():
        print(f"gerado: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
