"""Gate da classificação: cada contrato quebrado precisa virar erro, nunca passar calado."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reflow.classification import (
    check_classification,
    check_project,
    check_review,
    classified_projects,
    errors,
    parse_frontmatter,
)
from reflow.report import build_batch_report
from tests.classification_support import classification_text, review_text

PROJECT = "demo"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _workspace(tmp_path: Path, source_type: str = "python", **facts: list) -> Path:
    out = tmp_path / "output" / PROJECT
    (out / "01-inventory").mkdir(parents=True)
    (out / "03-classification").mkdir()
    (tmp_path / "input" / PROJECT).mkdir(parents=True)
    (tmp_path / "input" / PROJECT / "main.py").write_text("x = 1\n" * 10, encoding="utf-8")
    files = ["main.json"] if source_type == "a360" else ["main.py"]
    inventory = {"source_type": source_type, "files": files, **facts}
    (out / "01-inventory" / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    return tmp_path


def _write(root: Path, name: str, text: str) -> None:
    (root / "output" / PROJECT / "03-classification" / name).write_text(text, encoding="utf-8")


def _classification_errors(root: Path) -> list[str]:
    return [issue.message for issue in errors(check_classification(root, PROJECT))]


def _ui(line: int = 1) -> dict:
    return {"file": "main.json", "line": line}


def test_valid_classification_passes(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text())
    found = _classification_errors(root)
    require(found == [], f"válida não pode ter erro: {found}")


@pytest.mark.parametrize("raw", ['"NOT_PAD"', "NOT_PAD # dúvida", "PAD | PARTIAL", "not_pad", ""])
def test_verdict_outside_the_exact_enum_is_refused(tmp_path: Path, raw: str) -> None:
    root = _workspace(tmp_path)
    text = classification_text("NOT_PAD").replace("verdict: NOT_PAD", f"verdict: {raw}")
    _write(root, "classification.md", text)
    found = _classification_errors(root)
    require(any("verdict inválido" in m for m in found), f"{raw!r} passou: {found}")


@pytest.mark.parametrize(
    "text",
    [
        "# sem frontmatter\n",
        "---\nverdict: PAD\n",
        "---\nverdict: PAD\nverdict: NOT_PAD\n---\n",
        "---\nverdict: PAD\n---\n",
    ],
    ids=["sem-frontmatter", "sem-fechamento", "chave-duplicada", "sem-listas"],
)
def test_malformed_frontmatter_is_refused(tmp_path: Path, text: str) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", text)
    require(_classification_errors(root) != [], "frontmatter ruim passou")


def test_use_cases_must_match_the_verdict(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text("NOT_PAD", use_cases=["UC main.py:8"]))
    require(any("NOT_PAD não pode" in m for m in _classification_errors(root)), "NOT_PAD com UC")
    _write(root, "classification.md", classification_text("PARTIAL", use_cases=[]))
    require(any("sem nenhum" in m for m in _classification_errors(root)), "PARTIAL sem UC")


def test_every_criterion_must_be_evaluated_by_id(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text().replace("| N3 | avaliado |\n", ""))
    found = _classification_errors(root)
    require(any("critérios não avaliados: N3" in m for m in found), f"{found}")


def test_body_cannot_contradict_the_frontmatter(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text() + "\n**Veredito: NOT_PAD.**\n")
    require(any("contradiz" in m for m in _classification_errors(root)), "contradição passou")


@pytest.mark.parametrize(
    ("evidence", "reason"),
    [
        ("main.py:99", "além do fim"),
        ("inexistente.md:1", "não encontrado"),
        ("main.py:5-2", "inválido"),
    ],
)
def test_evidence_must_exist(tmp_path: Path, evidence: str, reason: str) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text("NOT_PAD", evidence=evidence))
    found = _classification_errors(root)
    require(any(reason in m for m in found), f"{evidence} passou: {found}")


def test_classification_without_any_evidence_is_refused(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    text = classification_text("NOT_PAD").replace("Evidência: `main.py:8`.", "")
    _write(root, "classification.md", text)
    require(any("nenhuma evidência" in m for m in _classification_errors(root)), "sem evidência")


def test_bare_inventory_citation_resolves_and_still_checks_the_line(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text("NOT_PAD", evidence="inventory.json:1"))
    require(_classification_errors(root) == [], "inventory.json sem pasta é o do projeto")
    _write(root, "classification.md", classification_text("NOT_PAD", evidence="inventory.json:9"))
    found = _classification_errors(root)
    require(any("além do fim" in m for m in found), f"linha inventada passou: {found}")


def test_a360_line_is_the_node_index_from_the_inventory(tmp_path: Path) -> None:
    root = _workspace(tmp_path, "a360", ui_interactions=[_ui(1), _ui(2)])
    _write(root, "classification.md", classification_text(evidence="main.json:2"))
    require(_classification_errors(root) == [], "nó existente")
    _write(root, "classification.md", classification_text(evidence="main.json:3"))
    found = _classification_errors(root)
    require(any("nó não existe" in m for m in found), f"nó inventado passou: {found}")


def test_source_missing_locally_still_counts_when_in_the_inventory(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "input" / PROJECT / "main.py").unlink()
    _write(root, "classification.md", classification_text("NOT_PAD", evidence="main.py:999"))
    require(_classification_errors(root) == [], "legado real não é versionado")


def test_alert_needs_evidence_and_a_known_id(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text(alerts=["A1 sem evidência"]))
    require(any("alerta sem evidência" in m for m in _classification_errors(root)), "sem citação")
    _write(root, "classification.md", classification_text(alerts=["A9 extra (main.py:8)"]))
    require(any("fora de A1-A5" in m for m in _classification_errors(root)), "A9")


def test_vault_in_the_inventory_requires_a4(tmp_path: Path) -> None:
    root = _workspace(
        tmp_path, "a360", credentials=[_ui(1)], ui_interactions=[_ui(2)], data_sources=[]
    )
    _write(root, "classification.md", classification_text(evidence="main.json:1"))
    require(any("alerta A4" in m for m in _classification_errors(root)), "A4 ausente passou")
    with_alert = classification_text(evidence="main.json:1", alerts=["A4 vault (main.json:1)"])
    _write(root, "classification.md", with_alert)
    require(_classification_errors(root) == [], "A4 presente")


def test_pad_without_ui_blocks_only_where_the_extractor_records_ui(tmp_path: Path) -> None:
    a360 = _workspace(tmp_path / "a", "a360", data_sources=[_ui(1)])
    _write(a360, "classification.md", classification_text(evidence="main.json:1"))
    require(any("sem nenhuma interação" in m for m in _classification_errors(a360)), "A360")

    python = _workspace(tmp_path / "b")
    _write(python, "classification.md", classification_text())
    issues = check_classification(python, PROJECT)
    require(errors(issues) == [], "Python não registra UI: ausência não prova nada")
    require(any("sem nenhuma interação" in i.message for i in issues), "mas precisa avisar")


def test_not_pad_with_majority_ui_only_warns(tmp_path: Path) -> None:
    root = _workspace(tmp_path, "a360", ui_interactions=[_ui(1), _ui(2)], http_calls=[_ui(3)])
    _write(root, "classification.md", classification_text("NOT_PAD", evidence="main.json:1"))
    issues = check_classification(root, PROJECT)
    require(errors(issues) == [], "a regra de nuvem/API pode justificar")
    require(any("UI majoritária" in i.message for i in issues), "precisa avisar")


def test_long_alert_broken_in_two_lines_is_one_item() -> None:
    data = parse_frontmatter('---\nalerts:\n  - "A1 começa\n    e termina (main.py:1)"\n---\n')
    require(data == {"alerts": ["A1 começa e termina (main.py:1)"]}, f"{data}")


def test_missing_review_only_warns(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text())
    issues = check_review(root, PROJECT)
    require(errors(issues) == [] and issues[0].level == "aviso", f"{issues}")


def test_valid_review_passes(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text())
    _write(root, "review.md", review_text())
    found = check_project(root, PROJECT)
    require(errors(found) == [], f"{found}")


@pytest.mark.parametrize(
    ("review", "reason"),
    [
        (review_text("NOT_PAD", "NOT_PAD"), "desatualizada"),
        (review_text("PAD", "NOT_PAD", "concorda"), "agreement"),
        (review_text("PAD", "PAD", "diverge", extra="\n## Por que divirjo\n"), "agreement"),
        (review_text("PAD", "PARTIAL", "diverge"), "Por que divirjo"),
        (review_text("PAD", "PAD", "talvez"), "inválido"),
        (review_text().replace("Minha análise", "Outra"), "Minha análise"),
        (review_text(evidence="main.py:99"), "além do fim"),
    ],
    ids=["stale", "falso-concorda", "falso-diverge", "sem-motivo", "enum", "sem-analise", "prova"],
)
def test_broken_review_is_refused(tmp_path: Path, review: str, reason: str) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text())
    _write(root, "review.md", review)
    found = [issue.message for issue in errors(check_review(root, PROJECT))]
    require(any(reason in m for m in found), f"esperava {reason}: {found}")


def test_real_divergence_is_valid_but_always_flagged(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text())
    extra = "\n## Por que divirjo\n"
    _write(root, "review.md", review_text("PAD", "PARTIAL", "diverge", extra=extra))
    issues = check_review(root, PROJECT)
    require(errors(issues) == [], f"divergência real é válida: {issues}")
    require(any("DIVERGÊNCIA" in i.message for i in issues), "precisa destacar")


def test_eval_projects_stay_out_of_the_gate_batch_and_report(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "classification.md", classification_text())
    folder = root / "output" / "eval-case-01" / "03-classification"
    folder.mkdir(parents=True)
    (folder / "classification.md").write_text("ruim", encoding="utf-8")
    (root / "output" / "eval-case-01" / "00-manifest.json").write_text("{}", encoding="utf-8")
    require(classified_projects(root) == [PROJECT], f"{classified_projects(root)}")
    require("eval-case-01" not in build_batch_report(root), "eval não vai para o relatório")


@pytest.mark.parametrize("project", ["a360-browser-rest", "a360-excel-vault", "quote-scraper"])
def test_real_classifications_in_the_repository_pass(project: str) -> None:
    root = Path(__file__).resolve().parents[2]
    found = errors(check_project(root, project))
    require(found == [], f"{project}: {found}")
