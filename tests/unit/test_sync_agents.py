"""Paridade entre .opencode/agents/ (fonte da verdade) e .claude/agents/ (gerado)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sync_agents import _extract_description, _split_frontmatter, render_claude_agent

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / ".opencode" / "agents"
TARGET_DIR = ROOT / ".claude" / "agents"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _source_agents() -> list[Path]:
    if not SOURCE_DIR.is_dir():
        return []
    return sorted(SOURCE_DIR.glob("*.md"))


@pytest.mark.parametrize("source", _source_agents(), ids=lambda p: p.stem)
def test_claude_mirror_matches_opencode_source(source: Path) -> None:
    target = TARGET_DIR / source.name
    require(
        target.is_file(), f"Falta o espelho Claude de {source.name}; rode scripts/sync_agents.py."
    )

    frontmatter, body = _split_frontmatter(source.read_text(encoding="utf-8"))
    description = _extract_description(frontmatter)
    expected = render_claude_agent(source.stem, description, body)
    actual = target.read_text(encoding="utf-8")
    require(actual == expected, f"{target.name} desatualizado; rode scripts/sync_agents.py.")


def test_every_opencode_agent_has_minimal_permissions() -> None:
    required_denies = {"bash", "webfetch", "websearch", "external_directory", "task"}
    for source in _source_agents():
        frontmatter, _ = _split_frontmatter(source.read_text(encoding="utf-8"))
        denied = {
            action
            for action in required_denies
            if f'action: {action}, resource: "*", effect: deny' in frontmatter
        }
        missing = required_denies - denied
        require(not missing, f"{source.name}: faltam denies de permissão: {missing}.")


def test_every_opencode_agent_restricts_edit_to_its_own_phase() -> None:
    for source in _source_agents():
        frontmatter, _ = _split_frontmatter(source.read_text(encoding="utf-8"))
        require(
            'action: edit, resource: "*", effect: deny' in frontmatter,
            f"{source.name}: edit não começa negado por padrão.",
        )


def test_the_five_phase_agents_exist() -> None:
    expected = {
        "reflow-documenter",
        "reflow-classifier",
        "reflow-pad-converter",
        "reflow-pad-tester",
        "reflow-truth-table-curator",
    }
    found = {p.stem for p in _source_agents()}
    missing = expected - found
    require(not missing, f"Agents ausentes: {sorted(missing)}")
