"""Orçamento de entrada da extração real — `reflow.limits` (Fase 4 de segurança)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reflow import limits


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_budget_passes_for_a_normal_project(tmp_path: Path) -> None:
    (tmp_path / "main.json").write_text("{}", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "child.json").write_text("{}", encoding="utf-8")
    limits.check_input_budget(tmp_path)  # não deve levantar nada


def test_budget_refuses_too_many_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for index in range(5):
        (tmp_path / f"f{index}.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(limits, "MAX_INPUT_FILE_COUNT", 3)
    with pytest.raises(ValueError, match="arquivos"):
        limits.check_input_budget(tmp_path)
    require(limits.MAX_INPUT_FILE_COUNT == 3, "monkeypatch precisa valer em tempo de chamada.")


def test_budget_refuses_too_deep_a_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (nested / "main.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(limits, "MAX_INPUT_DEPTH", 2)
    with pytest.raises(ValueError, match="profundidade"):
        limits.check_input_budget(tmp_path)


def test_budget_refuses_a_single_huge_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "huge.bin").write_bytes(b"x" * 1024)
    monkeypatch.setattr(limits, "MAX_INPUT_FILE_BYTES", 100)
    with pytest.raises(ValueError, match="bytes por arquivo"):
        limits.check_input_budget(tmp_path)


def test_budget_refuses_the_total_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for index in range(4):
        (tmp_path / f"f{index}.bin").write_bytes(b"x" * 512)
    monkeypatch.setattr(limits, "MAX_INPUT_TOTAL_BYTES", 1000)
    with pytest.raises(ValueError, match="bytes no total"):
        limits.check_input_budget(tmp_path)
