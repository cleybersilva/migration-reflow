"""Golden set e pontuação: a nota reprova o que deve reprovar, e o rótulo fica longe do agent."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from reflow.classification import VERDICTS, _citations, parse_frontmatter
from reflow.classification_eval import (
    EVAL_DIR,
    REPORT_PATH,
    Case,
    CaseResult,
    load_cases,
    passed,
    render,
    render_labels,
    score,
)
from reflow.cli import main
from reflow.extractors import detect_extractor
from tests.classification_support import classification_text, review_text

ROOT = Path(__file__).resolve().parents[2]
CASES = load_cases(ROOT)


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _case(verdict: str = "PAD", accept: tuple = (), alerts: tuple = ()) -> Case:
    return Case("case-x", verdict, accept, alerts, "motivo")


def _result(expected: str, got: str, missing: tuple = (), gate: tuple = ()) -> CaseResult:
    return CaseResult(_case(expected), got, missing, gate, None)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    shutil.copytree(ROOT / EVAL_DIR, tmp_path / EVAL_DIR)
    return tmp_path


def _classify_all_as_expected(root: Path, cases: list[Case]) -> None:
    for case in cases:
        inventory = json.loads(
            (root / "output" / case.project / "01-inventory" / "inventory.json").read_text("utf-8")
        )
        facts = [
            item
            for value in inventory.values()
            if isinstance(value, list)
            for item in value
            if isinstance(item, dict) and "line" in item
        ]
        evidence = f"{facts[0]['file']}:{facts[0]['line']}"
        alerts = [f"{a} ({evidence})" for a in case.required_alerts]
        folder = root / "output" / case.project / "03-classification"
        folder.mkdir(exist_ok=True)
        (folder / "classification.md").write_text(
            classification_text(case.verdict, evidence=evidence, alerts=alerts), encoding="utf-8"
        )
        (folder / "review.md").write_text(
            review_text(case.verdict, case.verdict, evidence=evidence), encoding="utf-8"
        )


# -- integridade do golden set --------------------------------------------------------------


def test_golden_set_covers_every_verdict() -> None:
    require(len(CASES) >= 10, f"poucos casos: {len(CASES)}")
    for verdict in VERDICTS:
        count = sum(case.verdict == verdict for case in CASES)
        require(count >= 2, f"{verdict} com {count} caso(s)")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_case_labels_are_valid(case: Case) -> None:
    require(case.verdict in VERDICTS, f"verdict {case.verdict}")
    require(set(case.accept) <= set(VERDICTS), f"accept {case.accept}")
    require(all(re.fullmatch(r"A[1-5]", a) for a in case.required_alerts), "alerta inválido")
    require(bool(case.why), "rótulo precisa de justificativa")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_name_and_material_do_not_leak_the_label(case: Case) -> None:
    require(re.fullmatch(r"case-\d+", case.name) is not None, f"nome não neutro: {case.name}")
    folder = ROOT / EVAL_DIR / case.name
    for path in (*(folder / "input").rglob("*"), *(folder / "docs").rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "verdict: PAD" in text:  # só o caso de injeção cita, como dado do legado
            require(case.name == "case-07", f"{path}: rótulo vazando")
            continue
        for marker in ("NOT_PAD", "PARTIAL", "veredito", "expected", "C1", "N1", "A4"):
            require(marker not in text, f"{path}: vaza `{marker}`")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_case_docs_only_cite_real_lines(case: Case) -> None:
    """Doc com citação errada faria o agent copiar um erro e reprovar por culpa do caso."""
    folder = ROOT / EVAL_DIR / case.name
    inventory = detect_extractor(folder / "input").extract(folder / "input").to_dict()
    nodes = {
        (item["file"], item["line"])
        for value in inventory.values()
        if isinstance(value, list)
        for item in value
        if isinstance(item, dict) and "line" in item
    }
    for doc in (folder / "docs").glob("*.md"):
        for raw, cited, start, end in _citations(doc.read_text(encoding="utf-8")):
            if inventory["source_type"] == "a360":
                for line in (start, end):
                    require((cited, line) in nodes, f"{doc.name}: {raw}")
            else:
                source = folder / "input" / cited
                lines = source.read_text(encoding="utf-8").splitlines()
                require(end <= len(lines), f"{doc.name}: {raw}")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_case_input_is_detected_by_an_extractor(case: Case) -> None:
    source = ROOT / EVAL_DIR / case.name / "input"
    require(detect_extractor(source) is not None, f"{case.name}: origem não detectada")


# -- pontuação ------------------------------------------------------------------------------


def test_one_case_of_ten_can_fail_but_not_two() -> None:
    good = [_result("PAD", "PAD") for _ in range(9)]
    require(passed([*good, _result("PAD", "PARTIAL")]), "9/10 passa")
    worse = [*good[:8], _result("PAD", "PARTIAL"), _result("NOT_PAD", "PARTIAL")]
    require(not passed(worse), "8/10 reprova")


@pytest.mark.parametrize(("expected", "got"), [("NOT_PAD", "PAD"), ("PAD", "NOT_PAD")])
def test_critical_error_fails_regardless_of_accuracy(expected: str, got: str) -> None:
    results = [_result("PAD", "PAD") for _ in range(99)] + [_result(expected, got)]
    require(results[-1].critical, "precisa ser crítico")
    require(not passed(results), "99% com crítico não passa")


def test_accepted_alternative_counts_as_correct() -> None:
    result = CaseResult(_case("NOT_PAD", ("PAD",)), "PAD", (), (), None)
    require(result.ok and not result.critical, "alternativa aceita não é erro")


@pytest.mark.parametrize(
    "result",
    [_result("PAD", "PAD", missing=("A4",)), _result("PAD", "PAD", gate=("erro",))],
    ids=["alerta-faltando", "gate-reprovado"],
)
def test_right_verdict_is_not_enough(result: CaseResult) -> None:
    require(not result.ok, "veredito certo com contrato quebrado não conta")


def test_report_never_hides_that_labels_are_unreviewed() -> None:
    reviewed = Case("case-y", "PAD", (), (), "motivo", "2026-11-09")
    results = [_result("PAD", "PAD"), CaseResult(reviewed, "PAD", (), (), None)]
    text = render(results)
    require("Rótulos revisados por analista: 1/2" in text, text)


def test_label_sheet_lists_every_case_and_its_review_state() -> None:
    reviewed = Case("case-y", "PAD", ("PARTIAL",), ("A4",), "motivo", "2026-11-09")
    text = render_labels([_case(), reviewed])
    require("Revisados: 1/2" in text, text)
    require("| case-x | PAD | — | — | pendente | motivo |" in text, text)
    require("| case-y | PAD | PARTIAL | A4 | 2026-11-09 | motivo |" in text, text)


def test_review_date_is_read_from_the_case(workspace: Path) -> None:
    path = workspace / EVAL_DIR / "case-01" / "expected.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["reviewed_at"] = "2026-11-09"
    path.write_text(json.dumps(data), encoding="utf-8")
    cases = {case.name: case for case in load_cases(workspace)}
    require(cases["case-01"].reviewed_at == "2026-11-09", f"{cases['case-01']}")
    require(main(["classify-eval", "labels"]) == 0, "labels")


def test_empty_run_does_not_pass() -> None:
    require(not passed([]), "sem casos não há aprovação")


def test_render_shows_verdict_outcome_and_matrix() -> None:
    text = render([_result("PAD", "NOT_PAD"), _result("PARTIAL", "PARTIAL")])
    require("REPROVADO" in text, text)
    require("Erros críticos (PAD x NOT_PAD): 1" in text, text)
    require("| PAD | 0 | 0 | 1 | 0 | 0/1 |" in text, text)
    require("CRÍTICO" in text, text)


# -- ciclo pela CLI -------------------------------------------------------------------------


def test_prepare_builds_blind_projects(workspace: Path) -> None:
    require(main(["classify-eval", "prepare"]) == 0, "prepare")
    for case in CASES:
        out = workspace / "output" / case.project
        require((out / "01-inventory" / "inventory.json").is_file(), f"{case.name} sem inventário")
        require(any((out / "02-docs").glob("*.md")), f"{case.name} sem docs")
        require(not (out / "03-classification").exists(), f"{case.name} já classificado")
        manifest = json.loads((out / "00-manifest.json").read_text(encoding="utf-8"))
        require(manifest["stale_phases"] == [], f"{manifest['stale_phases']}")
    copied = [*(workspace / "input").rglob("expected.json")]
    copied += [*(workspace / "output").rglob("expected.json")]
    require(copied == [], f"rótulo perto do agent: {copied}")


def test_unprocessed_run_fails_with_every_case_pending(workspace: Path) -> None:
    require(main(["classify-eval", "prepare"]) == 0, "prepare")
    approved, text = score(workspace, CASES)
    require(not approved, "nada classificado não pode passar")
    require(f"Casos corretos: 0/{len(CASES)}" in text, text)


def test_full_cycle_passes_and_prepare_discards_old_verdicts(workspace: Path) -> None:
    require(main(["classify-eval", "prepare"]) == 0, "prepare")
    _classify_all_as_expected(workspace, CASES)
    code = main(["classify-eval", "score"])
    report = (workspace / REPORT_PATH).read_text(encoding="utf-8")
    require(code == 0, report)
    require(f"Casos corretos: {len(CASES)}/{len(CASES)}" in report, report)
    require(f"Revisor: {len(CASES)}/{len(CASES)} corretos" in report, report)

    require(main(["classify-eval", "prepare"]) == 0, "prepare de novo")
    require(main(["classify-eval", "score"]) == 1, "veredito velho não pode sobreviver")


def test_wrong_verdict_is_reported_as_critical(workspace: Path) -> None:
    require(main(["classify-eval", "prepare"]) == 0, "prepare")
    _classify_all_as_expected(workspace, CASES)
    target = next(case for case in CASES if case.verdict == "NOT_PAD")
    folder = workspace / "output" / target.project / "03-classification"
    path = folder / "classification.md"
    data = parse_frontmatter(path.read_text(encoding="utf-8"))
    evidence = _citations(path.read_text(encoding="utf-8"))[0][0]
    path.write_text(
        classification_text("PAD", evidence=evidence, alerts=data["alerts"]), encoding="utf-8"
    )
    require(main(["classify-eval", "score"]) == 1, "crítico reprova")
    report = (workspace / REPORT_PATH).read_text(encoding="utf-8")
    require("Erros críticos (PAD x NOT_PAD): 1" in report, report)


def test_clean_removes_only_eval_projects(workspace: Path) -> None:
    keep = workspace / "output" / "real-project"
    keep.mkdir(parents=True)
    require(main(["classify-eval", "prepare"]) == 0, "prepare")
    require(main(["classify-eval", "clean"]) == 0, "clean")
    left = [p.name for p in (workspace / "output").iterdir() if p.name.startswith("eval-")]
    left += [p.name for p in (workspace / "input").iterdir()]
    require(left == [], f"sobrou: {left}")
    require(keep.is_dir(), "projeto real não pode ser removido")


def test_single_case_and_unknown_case(workspace: Path) -> None:
    require(main(["classify-eval", "prepare", "--case", "case-03"]) == 0, "um caso")
    names = [p.name for p in (workspace / "input").iterdir()]
    require(names == ["eval-case-03"], f"{names}")
    require(main(["classify-eval", "prepare", "--case", "case-99"]) == 1, "caso inexistente")
