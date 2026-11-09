"""refold ponta a ponta sem rede: pré-condições, loop com modelo falso e fechamento da fase."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.cli import main as reflow_main
from refold import pipeline
from refold.agents import load_agent
from refold.cli import main as refold_main
from refold.loop import run_agent
from refold.tools import Sandbox

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "quote-scraper"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    shutil.copytree(ROOT / "input" / PROJECT, tmp_path / "input" / PROJECT)
    shutil.copytree(ROOT / ".opencode" / "agents", tmp_path / ".opencode" / "agents")
    require(reflow_main(["extract", PROJECT]) == 0, "extract deveria concluir.")
    return tmp_path


def _manifest(workspace: Path) -> dict:
    path = workspace / "output" / PROJECT / "00-manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_documenter_run_closes_the_phase(workspace: Path) -> None:
    (workspace / "output" / PROJECT / "03-classification").mkdir()
    (workspace / "output" / PROJECT / "03-classification" / "classification.md").write_text(
        "velha\n", encoding="utf-8"
    )
    spec = load_agent(workspace, "reflow-documenter")
    pipeline.check(workspace, spec.name, PROJECT)
    sandbox = Sandbox(workspace, PROJECT, spec.write_globs)
    script = [
        {
            "stop_reason": "tool_use",
            "content": [
                {
                    "type": "tool_use",
                    "id": "1",
                    "name": "write_file",
                    "input": {"path": f"output/{PROJECT}/02-docs/README.md", "content": "# D\n"},
                }
            ],
        },
        {"stop_reason": "end_turn", "content": [{"type": "text", "text": "pronto"}]},
    ]
    result = run_agent(spec, sandbox, lambda s, m, t: script.pop(0))
    require(result.finished, f"o agent deveria terminar: {result}")
    require(pipeline.close(spec.name, PROJECT, result.written) == [], "fechamento sem falhas")
    stale = _manifest(workspace)["stale_phases"]
    require(stale == ["03-classification"], f"02-docs em dia e a seguinte velha: {stale}")


def test_close_refuses_when_nothing_was_written(workspace: Path) -> None:
    failures = pipeline.close("reflow-documenter", PROJECT, [])
    require(failures and "não gravou" in failures[0], f"falhas {failures}")


def test_close_runs_robin_gates_before_phase_done() -> None:
    calls: list[list[str]] = []

    def fake_cli(argv: list[str]) -> int:
        calls.append(argv)
        return 1 if argv[0] == "lint-robin" else 0

    failures = pipeline.close("reflow-robin-optimizer", PROJECT, ["x"], run_cli=fake_cli)
    require([c[0] for c in calls] == ["fix-robin-eol", "lint-robin"], f"ordem {calls}")
    require(failures and "lint-robin" in failures[0], "lint reprovado não fecha a fase")


def test_converter_needs_classification_and_hash_checkpoint(workspace: Path) -> None:
    with pytest.raises(pipeline.PreconditionError, match="generation.json"):
        pipeline.check(workspace, "reflow-robin-optimizer", PROJECT)
    out = workspace / "output" / PROJECT
    (out / "04-pad" / "flow-x").mkdir(parents=True)
    (out / "04-pad" / "flow-x" / "generation.json").write_text("{}", encoding="utf-8")
    (out / "03-classification").mkdir()
    (out / "03-classification" / "classification.md").write_text(
        "**Veredito:** PARTIAL\n", encoding="utf-8"
    )
    with pytest.raises(pipeline.PreconditionError, match="não aprovado"):
        pipeline.check(workspace, "reflow-robin-optimizer", PROJECT)

    manifest = _manifest(workspace)
    manifest["checkpoint"] = {"decision": "approved", "approved_at": "2026-10-21"}
    (out / "00-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(pipeline.PreconditionError, match="legado"):
        pipeline.check(workspace, "reflow-robin-optimizer", PROJECT)


def test_changed_input_blocks_any_agent(workspace: Path) -> None:
    target = next(p for p in (workspace / "input" / PROJECT).rglob("*") if p.is_file())
    target.write_text(target.read_text(encoding="utf-8") + "\n# mudou\n", encoding="utf-8")
    with pytest.raises(pipeline.PreconditionError, match="mudou"):
        pipeline.check(workspace, "reflow-documenter", PROJECT)


def test_cli_dry_run_never_calls_the_api(
    workspace: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in ("IARA_BASE_URL", "IARA_API_KEY", "IARA_MODEL"):
        monkeypatch.delenv(key, raising=False)
    require(refold_main(["run", "reflow-documenter", PROJECT, "--dry-run"]) == 0, "dry-run ok")
    out = capsys.readouterr().out
    require("[dry-run]" in out and "Execução no refold" in out, out[-400:])
    require(refold_main(["run", "reflow-documenter", PROJECT]) == 1, "sem env, run falha")
