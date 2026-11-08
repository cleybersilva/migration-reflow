"""Golden set da classificação: prepara os casos, depois pontua o que os agents gravaram.

O Python continua sem LLM: `prepare` monta `input/eval-<caso>` e `output/eval-<caso>` a partir
de `tests/fixtures/classification/`, qualquer harness roda os agents e `score` compara o
resultado com `expected.json`, que nunca é copiado para perto do agent (rótulo cego).
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .classification import (
    ALERT_ID_RE,
    EVAL_PREFIX,
    VERDICTS,
    check_project,
    errors,
    parse_frontmatter,
)

EVAL_DIR = Path("tests") / "fixtures" / "classification"
REPORT_PATH = Path("output") / "_classification-eval.md"
MIN_ACCURACY = 0.9
# Erro que muda o destino do robô de ponta a ponta: não existe margem para ele.
CRITICAL = {("NOT_PAD", "PAD"), ("PAD", "NOT_PAD")}
NO_VERDICT = "—"


@dataclass(frozen=True)
class Case:
    name: str
    verdict: str
    accept: tuple[str, ...]
    required_alerts: tuple[str, ...]
    why: str
    reviewed_at: str | None = None  # data em que um analista confirmou o rótulo

    @property
    def project(self) -> str:
        return f"{EVAL_PREFIX}{self.name}"


@dataclass(frozen=True)
class CaseResult:
    case: Case
    verdict: str
    missing_alerts: tuple[str, ...]
    gate_errors: tuple[str, ...]
    reviewed: str | None

    @property
    def verdict_ok(self) -> bool:
        return self.verdict in (self.case.verdict, *self.case.accept)

    @property
    def ok(self) -> bool:
        return self.verdict_ok and not self.missing_alerts and not self.gate_errors

    @property
    def critical(self) -> bool:
        return (self.case.verdict, self.verdict) in CRITICAL and not self.verdict_ok


def load_cases(root: Path, only: list[str] | None = None) -> list[Case]:
    cases = []
    for path in sorted((root / EVAL_DIR).glob("*/expected.json")):
        name = path.parent.name
        if only and name not in only:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        cases.append(
            Case(
                name,
                data["verdict"],
                tuple(data.get("accept", ())),
                tuple(data.get("required_alerts", ())),
                data["why"],
                data.get("reviewed_at"),
            )
        )
    if only and len(cases) != len(set(only)):
        known = {case.name for case in cases}
        raise ValueError(f"caso desconhecido: {', '.join(sorted(set(only) - known))}")
    return cases


def _remove_case(root: Path, project: str) -> None:
    if not project.startswith(EVAL_PREFIX):
        raise ValueError(f"recusado: {project} não é projeto do golden set")
    for path in (root / "input" / project, root / "output" / project):
        if path.is_dir():
            shutil.rmtree(path)
    (root / "output" / f"{project}.lock").unlink(missing_ok=True)


def prepare(root: Path, cases: list[Case], run_cli: Callable[[list[str]], int]) -> int:
    """Remonta cada caso do zero, para `score` nunca pontuar veredito de execução anterior."""
    for case in cases:
        source = root / EVAL_DIR / case.name
        _remove_case(root, case.project)
        shutil.copytree(source / "input", root / "input" / case.project)
        if run_cli(["extract", case.project]) != 0:
            return 1
        shutil.copytree(source / "docs", root / "output" / case.project / "02-docs")
        if run_cli(["phase-done", case.project, "02-docs"]) != 0:
            return 1
    return 0


def clean(root: Path, cases: list[Case]) -> None:
    for case in cases:
        _remove_case(root, case.project)
    (root / REPORT_PATH).unlink(missing_ok=True)


def _frontmatter(path: Path) -> dict:
    if not path.is_file():
        return {}
    return parse_frontmatter(path.read_text(encoding="utf-8")) or {}


def score_case(root: Path, case: Case) -> CaseResult:
    folder = root / "output" / case.project / "03-classification"
    data = _frontmatter(folder / "classification.md")
    verdict = data.get("verdict")
    if verdict not in VERDICTS:
        verdict = NO_VERDICT
    alerts = data.get("alerts") if isinstance(data.get("alerts"), list) else []
    found = {match[0] for alert in alerts if (match := ALERT_ID_RE.match(alert))}
    gate = (
        ()
        if verdict == NO_VERDICT
        else tuple(
            f"{issue.file.rsplit('/', 1)[-1]}: {issue.message}"
            for issue in errors(check_project(root, case.project))
        )
    )
    reviewed = _frontmatter(folder / "review.md").get("reviewed_verdict")
    return CaseResult(
        case,
        verdict,
        tuple(a for a in case.required_alerts if a not in found),
        gate,
        reviewed if isinstance(reviewed, str) else None,
    )


def passed(results: list[CaseResult]) -> bool:
    if not results or any(result.critical for result in results):
        return False
    return sum(result.ok for result in results) / len(results) >= MIN_ACCURACY


def render(results: list[CaseResult]) -> str:
    total = len(results)
    hits = sum(result.ok for result in results)
    reviewed = [result for result in results if result.reviewed]
    review_hits = sum(r.reviewed in (r.case.verdict, *r.case.accept) for r in reviewed)
    agreements = sum(result.reviewed == result.verdict for result in reviewed)
    columns = (*VERDICTS, NO_VERDICT)
    lines = [
        "# Eval da classificação",
        "",
        f"Resultado: **{'APROVADO' if passed(results) else 'REPROVADO'}** "
        f"(mínimo {MIN_ACCURACY:.0%} de acerto e nenhum erro crítico).",
        "",
        f"- Casos corretos: {hits}/{total}",
        f"- Erros críticos (PAD x NOT_PAD): {sum(result.critical for result in results)}",
        f"- Rótulos revisados por analista: "
        f"{sum(bool(result.case.reviewed_at) for result in results)}/{total}",
        f"- Revisor: {review_hits}/{len(reviewed)} corretos, "
        f"{agreements}/{len(reviewed)} concordam com o classificador",
        "",
        "## Matriz de confusão (linha = esperado, coluna = obtido)",
        "",
        "| esperado | " + " | ".join(columns) + " | recall |",
        "| --- | " + " | ".join("---" for _ in columns) + " | --- |",
    ]
    for expected in VERDICTS:
        group = [r for r in results if r.case.verdict == expected]
        cells = [str(sum(r.verdict == column for r in group)) for column in columns]
        recall = f"{sum(r.verdict_ok for r in group)}/{len(group)}" if group else "—"
        lines.append(f"| {expected} | " + " | ".join(cells) + f" | {recall} |")
    lines += [
        "",
        "## Casos",
        "",
        "| caso | esperado | obtido | revisor | alertas faltando | gate | resultado |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        gate = "; ".join(r.gate_errors).replace("|", "/") or "ok"
        lines.append(
            f"| {r.case.name} | {r.case.verdict} | {r.verdict} | {r.reviewed or '—'} | "
            f"{', '.join(r.missing_alerts) or '—'} | {gate} | "
            f"{'ok' if r.ok else 'CRÍTICO' if r.critical else 'falhou'} |"
        )
    return "\n".join(lines) + "\n"


def render_labels(cases: list[Case]) -> str:
    """Folha de revisão: o analista confirma cada rótulo gravando `reviewed_at` no caso."""
    lines = [
        "# Rótulos do golden set",
        "",
        f"Revisados: {sum(bool(case.reviewed_at) for case in cases)}/{len(cases)}. Material de "
        f"cada caso em `{EVAL_DIR.as_posix()}/<caso>/`.",
        "",
        "| caso | rótulo | também aceito | alertas | revisado em | por quê |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(
            f"| {case.name} | {case.verdict} | {', '.join(case.accept) or '—'} | "
            f"{', '.join(case.required_alerts) or '—'} | {case.reviewed_at or 'pendente'} | "
            f"{case.why} |"
        )
    return "\n".join(lines) + "\n"


def score(root: Path, cases: list[Case]) -> tuple[bool, str]:
    results = [score_case(root, case) for case in cases]
    text = render(results)
    path = root / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return passed(results), text
