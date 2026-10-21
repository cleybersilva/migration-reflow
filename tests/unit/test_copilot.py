"""Paridade com o Copilot: terceiro harness espelhado, igual ao OpenCode/Claude.

`.github/copilot-instructions.md` aponta para AGENTS.md (mesmo padrão de
`CLAUDE.md`); `.github/prompts/*.prompt.md` é o espelho manual das skills
(fonte da verdade continua em `.claude/skills/`); `.github/chatmodes/*.chatmode.md`
é gerado a partir de `.opencode/agents/` por `scripts/sync_copilot.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sync_copilot import _extract_description, _split_frontmatter, render_chatmode

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".claude" / "skills"
SOURCE_AGENTS_DIR = ROOT / ".opencode" / "agents"
CHATMODES_DIR = ROOT / ".github" / "chatmodes"
PROMPTS_DIR = ROOT / ".github" / "prompts"
COPILOT_INSTRUCTIONS = ROOT / ".github" / "copilot-instructions.md"

# Única skill sem agent/skill dedicado (é um wrapper fino da CLI `reflow report`).
EXTRA_PROMPTS_WITHOUT_A_SKILL = {"reflow-report"}


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _has_frontmatter_field(path: Path, field: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end == -1:
        return False
    return any(line.startswith(f"{field}:") for line in text[4:end].splitlines())


def test_copilot_instructions_file_points_to_agents_md() -> None:
    require(COPILOT_INSTRUCTIONS.is_file(), ".github/copilot-instructions.md não existe.")
    text = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    require(
        "AGENTS.md" in text,
        ".github/copilot-instructions.md precisa apontar para AGENTS.md (fonte da verdade).",
    )


def test_every_skill_has_a_copilot_prompt() -> None:
    skill_names: set[str] = set()
    if SKILLS_DIR.is_dir():
        skill_names = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    expected = skill_names | EXTRA_PROMPTS_WITHOUT_A_SKILL
    found = (
        {p.name.removesuffix(".prompt.md") for p in PROMPTS_DIR.glob("*.prompt.md")}
        if PROMPTS_DIR.is_dir()
        else set()
    )
    missing = expected - found
    require(not missing, f"Prompts do Copilot ausentes: {sorted(missing)}")


@pytest.mark.parametrize(
    "prompt_file",
    sorted(PROMPTS_DIR.glob("*.prompt.md")) if PROMPTS_DIR.is_dir() else [],
    ids=lambda p: p.name,
)
def test_prompt_has_description_and_points_to_its_skill(prompt_file: Path) -> None:
    require(
        _has_frontmatter_field(prompt_file, "description"),
        f"{prompt_file.name}: frontmatter sem `description`.",
    )
    name = prompt_file.name.removesuffix(".prompt.md")
    if name in EXTRA_PROMPTS_WITHOUT_A_SKILL:
        return
    text = prompt_file.read_text(encoding="utf-8")
    require(
        f".claude/skills/{name}/SKILL.md" in text,
        f"{prompt_file.name}: não aponta para a skill correspondente (fonte da verdade).",
    )


def _source_agents() -> list[Path]:
    if not SOURCE_AGENTS_DIR.is_dir():
        return []
    return sorted(SOURCE_AGENTS_DIR.glob("*.md"))


@pytest.mark.parametrize("source", _source_agents(), ids=lambda p: p.stem)
def test_chatmode_mirrors_opencode_source(source: Path) -> None:
    target = CHATMODES_DIR / f"{source.stem}.chatmode.md"
    require(
        target.is_file(),
        f"Falta o chatmode do Copilot para {source.name}; rode scripts/sync_copilot.py.",
    )
    frontmatter, body = _split_frontmatter(source.read_text(encoding="utf-8"))
    description = _extract_description(frontmatter)
    expected = render_chatmode(description, body)
    actual = target.read_text(encoding="utf-8")
    require(actual == expected, f"{target.name} desatualizado; rode scripts/sync_copilot.py.")


@pytest.mark.parametrize("source", _source_agents(), ids=lambda p: p.stem)
def test_chatmode_discloses_the_missing_permission_engine(source: Path) -> None:
    target = CHATMODES_DIR / f"{source.stem}.chatmode.md"
    require(target.is_file(), f"Falta o chatmode do Copilot para {source.name}.")
    text = target.read_text(encoding="utf-8")
    require(
        "Aviso de modo (Copilot)" in text,
        f"{target.name}: falta o aviso de que o Copilot não impõe permissão por recurso.",
    )
