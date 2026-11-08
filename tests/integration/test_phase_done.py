"""`stale_phases` no manifesto: o `extract` marca só fases que existem e `reflow phase-done`
fecha uma fase, propagando a desatualização para as seguintes já geradas (Fase 33)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.cli import main
from tests.classification_support import classification_text

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "quote-scraper"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    shutil.copytree(ROOT / "input" / PROJECT, tmp_path / "input" / PROJECT)
    return tmp_path


def _out(workspace: Path) -> Path:
    return workspace / "output" / PROJECT


def _stale(workspace: Path) -> list[str]:
    manifest = json.loads((_out(workspace) / "00-manifest.json").read_text(encoding="utf-8"))
    return manifest["stale_phases"]


def _make(workspace: Path, relative: str) -> None:
    path = _out(workspace) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n", encoding="utf-8")


def test_first_extract_marks_nothing_stale(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    require(_stale(workspace) == [], f"fase que não rodou não é desatualizada: {_stale(workspace)}")


def test_re_extract_marks_only_existing_phases(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    _make(workspace, "02-docs/overview.md")
    _make(workspace, "03-classification/classification.md")
    require(main(["extract", PROJECT]) == 0, "reextração deveria concluir.")
    require(
        _stale(workspace) == ["02-docs", "03-classification"],
        f"só as fases existentes: {_stale(workspace)}",
    )


def test_phase_done_clears_the_phase_and_marks_later_existing_ones(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    _make(workspace, "02-docs/overview.md")
    _make(workspace, "04-pad/uc-01/Main.robin")
    require(main(["phase-done", PROJECT, "02-docs"]) == 0, "phase-done deveria gravar.")
    require(
        _stale(workspace) == ["04-pad"],
        f"02-docs em dia, 04-pad (já existente) desatualizada: {_stale(workspace)}",
    )
    require(main(["phase-done", PROJECT, "04-pad"]) == 0, "phase-done de 04-pad.")
    require(_stale(workspace) == [], f"tudo em dia: {_stale(workspace)}")


def test_phase_done_drops_legacy_entries_for_phases_that_never_ran(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    manifest_path = _out(workspace) / "00-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["stale_phases"] = ["02-docs", "03-classification", "04-pad", "05-test"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _make(workspace, "02-docs/overview.md")
    require(main(["phase-done", PROJECT, "02-docs"]) == 0, "phase-done deveria gravar.")
    require(_stale(workspace) == [], f"fases inexistentes não ficam: {_stale(workspace)}")


def test_phase_done_refuses_a_phase_without_artifact(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    (_out(workspace) / "04-pad").mkdir(parents=True)
    require(main(["phase-done", PROJECT, "04-pad"]) == 1, "sem Main.robin a fase não rodou.")


def test_phase_done_refuses_changed_inputs(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    _make(workspace, "02-docs/overview.md")
    (workspace / "input" / PROJECT / "novo.json").write_text("{}", encoding="utf-8")
    require(main(["phase-done", PROJECT, "02-docs"]) == 1, "entrada nova exige reextração.")


def test_phase_done_without_manifest_is_an_error(workspace: Path) -> None:
    require(main(["phase-done", PROJECT, "02-docs"]) == 1, "sem extract não há manifesto.")


def test_classification_phase_only_closes_through_the_gate(workspace: Path) -> None:
    require(main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    _make(workspace, "03-classification/classification.md")
    require(main(["extract", PROJECT]) == 0, "reextração marca a fase existente.")
    require(main(["phase-done", PROJECT, "03-classification"]) == 1, "stub não fecha a fase.")
    require(_stale(workspace) == ["03-classification"], f"continua velha: {_stale(workspace)}")

    path = _out(workspace) / "03-classification" / "classification.md"
    path.write_text(classification_text("NOT_PAD"), encoding="utf-8")
    require(main(["phase-done", PROJECT, "03-classification"]) == 0, "válida fecha a fase.")
    require(_stale(workspace) == [], f"em dia: {_stale(workspace)}")
