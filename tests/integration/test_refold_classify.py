"""`refold classify` sem rede: classificador, gate, revisor, gate, com modelo falso."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.classification_eval import EVAL_DIR, load_cases
from reflow.cli import main as reflow_main
from refold import cli as refold_cli
from refold.client import Config
from tests.classification_support import classification_text, review_text

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "quote-scraper"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _write_call(path: str, content: str) -> dict:
    use = {
        "type": "tool_use",
        "id": "1",
        "name": "write_file",
        "input": {"path": path, "content": content},
    }
    return {"stop_reason": "tool_use", "content": [use]}


END = {"stop_reason": "end_turn", "content": [{"type": "text", "text": "pronto"}]}


class FakeClient:
    """Responde conforme o agent, reconhecido pelo prompt de sistema."""

    calls: list[str] = []
    classification: dict[str, str] = {}
    review: dict[str, str] = {}

    def __init__(self, config: object) -> None:
        self.config = config

    @classmethod
    def reset(cls, classification: str, review: str) -> None:
        cls.calls = []
        cls.classification = {"*": classification}
        cls.review = {"*": review}

    def create(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        if len(messages) > 1:
            return END
        project = system.split("Projeto: `", 1)[1].split("`", 1)[0]
        is_review = "segunda opinião independente" in system
        self.calls.append(("review" if is_review else "classify") + f":{project}")
        folder = f"output/{project}/03-classification"
        if is_review:
            text = self.review.get(project, self.review["*"])
            return _write_call(f"{folder}/review.md", text)
        text = self.classification.get(project, self.classification["*"])
        return _write_call(f"{folder}/classification.md", text)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    shutil.copytree(ROOT / "input" / PROJECT, tmp_path / "input" / PROJECT)
    shutil.copytree(ROOT / ".opencode" / "agents", tmp_path / ".opencode" / "agents")
    require(reflow_main(["extract", PROJECT]) == 0, "extract")
    docs = tmp_path / "output" / PROJECT / "02-docs"
    docs.mkdir()
    (docs / "use-cases.md").write_text("# UC\n", encoding="utf-8")
    monkeypatch.setattr(refold_cli, "MessagesClient", FakeClient)
    monkeypatch.setattr(refold_cli, "load_config", lambda: Config("http://x", "k", "m"))
    return tmp_path


def _stale(workspace: Path) -> list[str]:
    path = workspace / "output" / PROJECT / "00-manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))["stale_phases"]


def test_classify_runs_both_agents_and_closes_the_phase(workspace: Path) -> None:
    FakeClient.reset(classification_text("NOT_PAD"), review_text("NOT_PAD", "NOT_PAD"))
    require(refold_cli.main(["classify", PROJECT]) == 0, "classify deveria passar")
    require(
        FakeClient.calls == [f"classify:{PROJECT}", f"review:{PROJECT}"],
        f"ordem: {FakeClient.calls}",
    )
    require("03-classification" not in _stale(workspace), f"{_stale(workspace)}")


def test_broken_classification_stops_before_the_reviewer(workspace: Path) -> None:
    FakeClient.reset('---\nverdict: "NOT_PAD"\n---\n', review_text())
    require(refold_cli.main(["classify", PROJECT]) == 1, "gate deveria reprovar")
    require(FakeClient.calls == [f"classify:{PROJECT}"], f"revisor rodou: {FakeClient.calls}")


def test_stale_review_fails_the_run(workspace: Path) -> None:
    FakeClient.reset(classification_text("NOT_PAD"), review_text("PAD", "PAD"))
    require(refold_cli.main(["classify", PROJECT]) == 1, "revisão de outro veredito reprova")


def test_divergent_review_finishes_and_stays_visible(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    extra = "\n## Por que divirjo\n\nN4.\n"
    FakeClient.reset(
        classification_text("NOT_PAD"), review_text("NOT_PAD", "PARTIAL", "diverge", extra=extra)
    )
    require(refold_cli.main(["classify", PROJECT]) == 0, "divergência real não é falha do harness")
    require("DIVERGÊNCIA" in capsys.readouterr().err, "precisa aparecer para o analista")


def test_classify_needs_a_project_or_eval(workspace: Path) -> None:
    require(refold_cli.main(["classify"]) == 1, "sem projeto")


def test_classify_refuses_an_undocumented_project(workspace: Path) -> None:
    shutil.rmtree(workspace / "output" / PROJECT / "02-docs")
    FakeClient.reset(classification_text("NOT_PAD"), review_text("NOT_PAD", "NOT_PAD"))
    require(refold_cli.main(["classify", PROJECT]) == 1, "sem docs")
    require(FakeClient.calls == [], "não pode chamar o modelo")


def test_eval_runs_every_case_and_scores(workspace: Path) -> None:
    shutil.copytree(ROOT / EVAL_DIR, workspace / EVAL_DIR)
    cases = load_cases(workspace)
    FakeClient.reset(classification_text("NOT_PAD"), review_text("NOT_PAD", "NOT_PAD"))
    for case in cases:
        evidence = "Program.cs:9" if case.name == "case-10" else "main.py:8"
        if (ROOT / EVAL_DIR / case.name / "input" / "main.json").is_file():
            evidence = "main.json:1"
        alerts = [f"{a} ({evidence})" for a in case.required_alerts]
        FakeClient.classification[case.project] = classification_text(
            case.verdict, evidence=evidence, alerts=alerts
        )
        FakeClient.review[case.project] = review_text(case.verdict, case.verdict, evidence=evidence)
    code = refold_cli.main(["classify", "--eval"])
    report = (workspace / "output" / "_classification-eval.md").read_text(encoding="utf-8")
    require(code == 0, report)
    require(f"Casos corretos: {len(cases)}/{len(cases)}" in report, report)
    require(len(FakeClient.calls) == 2 * len(cases), f"{FakeClient.calls}")


def test_eval_scores_a_broken_case_without_stopping_the_batch(workspace: Path) -> None:
    shutil.copytree(ROOT / EVAL_DIR, workspace / EVAL_DIR)
    cases = load_cases(workspace)
    FakeClient.reset("lixo", review_text())
    require(refold_cli.main(["classify", "--eval"]) == 1, "tudo quebrado reprova")
    classify_calls = [c for c in FakeClient.calls if c.startswith("classify:")]
    require(len(classify_calls) == len(cases), f"lote parou: {classify_calls}")
