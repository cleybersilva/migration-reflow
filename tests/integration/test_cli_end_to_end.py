"""CLI ponta a ponta sobre as fixtures: extract --all, scan, lint-robin, report."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reflow.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
PROJECT_NAMES = ("quote-scraper", "browser-rest", "excel-vault", "dotnet-project")


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    inputs = tmp_path / "input"
    shutil.copytree(ROOT / "input" / "quote-scraper", inputs / "quote-scraper")
    shutil.copytree(FIXTURES / "a360" / "browser-rest", inputs / "browser-rest")
    shutil.copytree(FIXTURES / "a360" / "excel-vault", inputs / "excel-vault")
    shutil.copytree(FIXTURES / "dotnet", inputs / "dotnet-project")
    return tmp_path


def test_extract_all_then_report(workspace: Path) -> None:
    require(main(["extract", "--all"]) == 0, "extract --all deveria concluir sem erro.")
    for name in PROJECT_NAMES:
        manifest_path = workspace / "output" / name / "00-manifest.json"
        require(manifest_path.is_file(), f"{name}: manifesto não foi gravado.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        require(manifest["status"] == "extracted", f"{name} deveria estar extraído.")
        require(len(manifest["inputs"][0]["sha256"]) == 64, f"{name}: manifesto exige SHA256.")

    require(main(["report"]) == 0, "report deveria concluir sem erro.")
    batch_report = (workspace / "output" / "_batch-report.md").read_text(encoding="utf-8")
    for name in PROJECT_NAMES:
        require(name in batch_report, f"{name} deveria aparecer em output/_batch-report.md.")


def test_scan_passes_on_the_generated_workspace(workspace: Path) -> None:
    require(main(["extract", "--all"]) == 0, "extract --all deveria concluir sem erro.")
    with pytest.raises(SystemExit) as result:
        main(["scan"])
    require(result.value.code == 0, "scan não deveria achar nada nessas fixtures sintéticas.")


def test_lint_robin_passes_without_any_robin_file(workspace: Path) -> None:
    with pytest.raises(SystemExit) as result:
        main(["lint-robin", "--all"])
    require(result.value.code == 0, "Sem nenhum Main.robin, lint-robin não tem nada a reprovar.")


def test_extract_rejects_project_with_a_junction_escaping_the_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Um projeto em `input/` com uma junction escondida apontando para fora
    do sandbox tem que ser recusado por inteiro — nunca ler o que está do
    outro lado do link nem gravar output parcial."""
    monkeypatch.chdir(tmp_path)
    project = tmp_path / "input" / "leaky-project"
    project.mkdir(parents=True)
    (project / "legit.json").write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside-sandbox"
    outside.mkdir()
    (outside / "secret.txt").write_text("conteudo fora do sandbox", encoding="utf-8")
    link = project / "escape"
    result = subprocess.run(  # noqa: S603
        ["cmd", "/c", "mklink", "/J", str(link), str(outside)],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"não foi possível criar junction neste ambiente: {result.stderr.strip()}")

    exit_code = main(["extract", "leaky-project"])
    require(exit_code == 1, "extract deveria recusar o projeto com junction, não travar.")
    require(
        not (tmp_path / "output" / "leaky-project").exists(),
        "Nenhum output parcial deveria ser gravado para um projeto recusado.",
    )
