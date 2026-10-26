"""DashboardRunner: listagem de input/ sem symlink/junction e orçamento de entrada."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from dashboard.pipeline import MAX_INPUT_DEPTH, MAX_INPUT_FILE_COUNT, DashboardRunner
from tests.link_support import make_unsafe_link


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_projects_lists_only_valid_directories(tmp_path: Path) -> None:
    (tmp_path / "input" / "robot-one").mkdir(parents=True)
    (tmp_path / "input" / "robot-two").mkdir(parents=True)
    (tmp_path / "input" / "not-a-dir.txt").write_text("x", encoding="utf-8")
    runner = DashboardRunner(tmp_path)
    require(
        runner.projects(None) == ["robot-one", "robot-two"],
        "Deveria listar só os diretórios de projeto válidos.",
    )


def test_projects_returns_empty_without_input_dir(tmp_path: Path) -> None:
    runner = DashboardRunner(tmp_path)
    require(runner.projects(None) == [], "Sem input/, a lista é vazia (não um erro).")


def test_projects_rejects_input_dir_that_is_itself_a_junction(tmp_path: Path) -> None:
    target = tmp_path / "real-input"
    target.mkdir()
    (target / "robot-one").mkdir()
    link = tmp_path / "input"
    make_unsafe_link(link, target)
    runner = DashboardRunner(tmp_path)
    with pytest.raises(ValueError, match="inseguro"):
        runner.projects(None)


def test_projects_excludes_a_project_directory_that_is_a_junction(tmp_path: Path) -> None:
    """Uma subpasta de projeto-junction nunca aparece como disponível, mas os
    outros projetos legítimos continuam listados — um projeto ruim não
    derruba o lote inteiro."""
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "robot-legit").mkdir()
    outside = tmp_path / "outside-sandbox"
    outside.mkdir()
    link = tmp_path / "input" / "robot-leaky"
    make_unsafe_link(link, outside)

    runner = DashboardRunner(tmp_path)
    names = runner.projects(None)
    require("robot-legit" in names, "Projeto legítimo continua listado.")
    require("robot-leaky" not in names, "Projeto-junction não pode aparecer como disponível.")

    with pytest.raises(ValueError, match="não disponível"):
        runner.projects("robot-leaky")


def test_execute_extract_passes_for_small_project_within_budget(tmp_path: Path) -> None:
    (tmp_path / "input" / "robot-small").mkdir(parents=True)
    (tmp_path / "input" / "robot-small" / "main.json").write_text('{"nodes": []}', encoding="utf-8")
    runner = DashboardRunner(tmp_path)
    result = runner.execute("run1", "robot-small", "extract", threading.Event())
    require("detail" in result, "Extração dentro do orçamento deveria concluir normalmente.")


def test_execute_extract_rejects_project_with_too_many_files(tmp_path: Path) -> None:
    project = tmp_path / "input" / "robot-many"
    project.mkdir(parents=True)
    for index in range(MAX_INPUT_FILE_COUNT + 1):
        (project / f"file-{index}.txt").write_text("x", encoding="utf-8")
    runner = DashboardRunner(tmp_path)
    with pytest.raises(ValueError, match="arquivos"):
        runner.execute("run1", "robot-many", "extract", threading.Event())


def test_execute_extract_rejects_project_deeper_than_budget(tmp_path: Path) -> None:
    project = tmp_path / "input" / "robot-deep"
    nested = project
    for level in range(MAX_INPUT_DEPTH + 2):
        nested = nested / f"level{level}"
    nested.mkdir(parents=True)
    (nested / "file.txt").write_text("x", encoding="utf-8")
    runner = DashboardRunner(tmp_path)
    with pytest.raises(ValueError, match="profund"):
        runner.execute("run1", "robot-deep", "extract", threading.Event())


def test_execute_extract_rejects_project_exceeding_byte_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import dashboard.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "MAX_INPUT_TOTAL_BYTES", 100)
    project = tmp_path / "input" / "robot-big"
    project.mkdir(parents=True)
    (project / "big.bin").write_bytes(b"x" * 1000)
    runner = DashboardRunner(tmp_path)
    with pytest.raises(ValueError, match="bytes"):
        runner.execute("run1", "robot-big", "extract", threading.Event())


def test_execute_extract_rejects_junction_inside_the_project(tmp_path: Path) -> None:
    """O orçamento sozinho não basta: uma junction escondida dentro do
    projeto (mesmo que pequeno/raso) ainda tem que ser recusada."""
    project = tmp_path / "input" / "robot-leaky-inside"
    project.mkdir(parents=True)
    (project / "main.json").write_text('{"nodes": []}', encoding="utf-8")
    outside = tmp_path / "outside-sandbox"
    outside.mkdir()
    make_unsafe_link(project / "escape", outside)
    runner = DashboardRunner(tmp_path)
    with pytest.raises(ValueError, match="inseguro"):
        runner.execute("run1", "robot-leaky-inside", "extract", threading.Event())
