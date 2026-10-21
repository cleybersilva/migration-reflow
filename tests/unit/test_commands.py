"""Commands do OpenCode: um wrapper fino por skill de fase, mais o relatório."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_DIR = ROOT / ".opencode" / "commands"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _has_frontmatter_description(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end == -1:
        return False
    return any(line.startswith("description:") for line in text[4:end].splitlines())


def test_every_phase_skill_has_a_command_wrapper() -> None:
    expected = {
        "reflow",
        "reflow-extract",
        "reflow-document",
        "reflow-classify",
        "reflow-convert",
        "reflow-test",
        "reflow-truth-table",
        "reflow-report",
    }
    found = {p.stem for p in COMMANDS_DIR.glob("*.md")} if COMMANDS_DIR.is_dir() else set()
    missing = expected - found
    require(not missing, f"Commands ausentes: {sorted(missing)}")


@pytest.mark.parametrize(
    "command_file",
    sorted(COMMANDS_DIR.glob("*.md")) if COMMANDS_DIR.is_dir() else [],
    ids=lambda p: p.stem,
)
def test_command_has_description(command_file: Path) -> None:
    require(
        _has_frontmatter_description(command_file),
        f"{command_file.name}: frontmatter sem `description`.",
    )


def test_phase_commands_pass_through_arguments_as_the_project_name() -> None:
    phase_commands = [
        "reflow.md",
        "reflow-extract.md",
        "reflow-document.md",
        "reflow-classify.md",
        "reflow-convert.md",
        "reflow-test.md",
        "reflow-truth-table.md",
    ]
    for name in phase_commands:
        body = (COMMANDS_DIR / name).read_text(encoding="utf-8")
        require(
            "$ARGUMENTS" in body,
            f"{name}: não repassa $ARGUMENTS como nome do projeto para a skill.",
        )
