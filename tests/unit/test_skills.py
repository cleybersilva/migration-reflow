"""Frontmatter de .claude/skills/<nome>/SKILL.md: name == pasta, regex, description."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".claude" / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_DESCRIPTION_LENGTH = 1024


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"{path}: SKILL.md precisa começar com frontmatter `---`.")
    end = text.find("\n---", 4)
    require(end != -1, f"{path}: frontmatter sem fechamento `---`.")
    block = text[4:end]
    data: dict[str, str] = {}
    for line in block.splitlines():
        if not line or line[0] in " \t" or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _skill_dirs() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())


@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda p: p.name)
def test_skill_frontmatter_is_valid(skill_dir: Path) -> None:
    skill_file = skill_dir / "SKILL.md"
    require(skill_file.is_file(), f"{skill_dir.name}: falta SKILL.md.")

    frontmatter = _read_frontmatter(skill_file)

    require("name" in frontmatter, f"{skill_dir.name}: frontmatter sem `name`.")
    require(
        frontmatter["name"] == skill_dir.name,
        f"{skill_dir.name}: name ({frontmatter['name']!r}) tem que ser igual à pasta.",
    )
    require(
        bool(NAME_RE.fullmatch(frontmatter["name"])),
        f"{skill_dir.name}: name não bate com ^[a-z0-9]+(-[a-z0-9]+)*$.",
    )

    require("description" in frontmatter, f"{skill_dir.name}: frontmatter sem `description`.")
    description = frontmatter["description"]
    require(bool(description), f"{skill_dir.name}: description vazia.")
    require(
        len(description) <= MAX_DESCRIPTION_LENGTH,
        f"{skill_dir.name}: description com {len(description)} caracteres, acima do máximo.",
    )


def test_at_least_the_seven_phase_skills_exist() -> None:
    expected = {
        "reflow",
        "reflow-extract",
        "reflow-document",
        "reflow-classify",
        "reflow-convert",
        "reflow-test",
        "reflow-truth-table",
    }
    found = {p.name for p in _skill_dirs()}
    missing = expected - found
    require(not missing, f"Skills de fase ausentes: {sorted(missing)}")
