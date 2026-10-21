"""Sanity checks for the phase 1 scaffold."""

import json
import tomllib
from pathlib import Path

import pytest

from reflow import __version__
from reflow.cli import main

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_dependencies_are_empty() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if config["project"]["dependencies"] != []:
        pytest.fail("O runtime deve usar somente stdlib.")
    if config["project"]["version"] != __version__:
        pytest.fail("Versão do pacote e pyproject divergentes.")


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as result:
        main(["--version"])
    if result.value.code != 0 or f"reflow {__version__}" not in capsys.readouterr().out:
        pytest.fail("A CLI não apresentou a versão esperada.")


def test_scan_passes_on_clean_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text('{"apiKey": "{env:IARA_API_KEY}"}\n', encoding="utf-8")
    with pytest.raises(SystemExit) as result:
        main(["scan"])
    if result.value.code != 0:
        pytest.fail("O scan não deveria falhar em placeholders conhecidos.")


def test_scan_fails_closed_on_assigned_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    leaked = 'API_KEY="sk-real-secret-value"\n'  # reflow:allow-secret
    (tmp_path / "leak.env").write_text(leaked, encoding="utf-8")
    with pytest.raises(SystemExit) as result:
        main(["scan"])
    if result.value.code != 2:
        pytest.fail("Um segredo atribuído não pode passar no scan.")


def test_lint_robin_passes_without_robin_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as result:
        main(["lint-robin", "--all"])
    if result.value.code != 0:
        pytest.fail("Sem .robin no repo não há nada a reprovar.")


def test_lint_robin_fails_closed_without_whitelist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Main.robin").write_text("// placeholder\n", encoding="utf-8")
    with pytest.raises(SystemExit) as result:
        main(["lint-robin", "--all"])
    if result.value.code != 2:
        pytest.fail("Um .robin sem whitelist não pode ser presumido validado.")


def test_opencode_uses_native_v2_configuration() -> None:
    config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    if "provider" in config or "permission" in config:
        pytest.fail("Usar configuração nativa OpenCode V2.")
    if config["providers"]["iara"]["settings"]["apiKey"] != "{env:IARA_API_KEY}":
        pytest.fail("A chave deve vir exclusivamente do ambiente.")
    for instruction in config["instructions"]:
        if not (ROOT / instruction).is_file():
            pytest.fail(f"Instrução ausente: {instruction}")
