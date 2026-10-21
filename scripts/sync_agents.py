"""Gera `.claude/agents/*.md` a partir de `.opencode/agents/*.md` (mesmo corpo).

Fonte da verdade: `.opencode/agents/` (formato OpenCode). `.claude/agents/*.md`
é gerado — não editar à mão. Depois de mudar um agent, rode:

    uv run python scripts/sync_agents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / ".opencode" / "agents"
TARGET_DIR = ROOT / ".claude" / "agents"
CLAUDE_TOOLS = "Read, Grep, Glob, Write"


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


def render_claude_agent(name: str, description: str, body: str) -> str:
    header = f"---\nname: {name}\ndescription: {description}\ntools: {CLAUDE_TOOLS}\n---\n\n"
    return header + body


def sync() -> list[Path]:
    if not SOURCE_DIR.is_dir():
        return []
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source in sorted(SOURCE_DIR.glob("*.md")):
        frontmatter, body = _split_frontmatter(source.read_text(encoding="utf-8"))
        description = _extract_description(frontmatter)
        target = TARGET_DIR / source.name
        target.write_text(render_claude_agent(source.stem, description, body), encoding="utf-8")
        written.append(target)
    return written


def main() -> int:
    for path in sync():
        print(f"gerado: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
