"""CLI determinística: extract, report, checkpoint e fix-robin-eol; scan e
lint-robin como gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import __version__, classification_eval
from .classification import (
    EVAL_PREFIX,
    Issue,
    check_classification,
    check_project,
    classified_projects,
    errors,
)
from .extractors import detect_extractor
from .fs import LockError, project_lock, write_json_atomic
from .inventory import Inventory
from .limits import check_input_budget
from .report import build_batch_report, read_verdict
from .robin import fix_robin_eol, lint_robin_files
from .robin.kb import load_action_kb, load_manifest, verify_kb
from .security.paths import reject_unsafe_links
from .security.scan import Finding, StagedScanError, scan_repository, scan_staged

PROJECT_NAME_RE = re.compile(r"[a-z0-9_-]+")
STALE_PHASES = ["02-docs", "03-classification", "04-pad", "05-test"]
CHECKPOINT_LABELS = {"approved": "aprovado", "rejected": "rejeitado"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reflow")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")

    extract = sub.add_parser("extract")
    extract.add_argument("project", nargs="?", default=None)
    extract.add_argument("--all", action="store_true")

    sub.add_parser("report")
    scan = sub.add_parser("scan")
    scan.add_argument(
        "--staged",
        action="store_true",
        help="Varre o índice do Git (conteúdo preparado), não a working tree.",
    )

    lint = sub.add_parser("lint-robin")
    lint.add_argument("project", nargs="?", default=None)
    lint.add_argument("--all", action="store_true")

    kb = sub.add_parser("kb", help="PAD Robin Action KB vendorizada (reference/vendor/).")
    kb_sub = kb.add_subparsers(dest="kb_command", required=True)
    kb_sub.add_parser("verify", help="Confere os hashes da cópia contra manifest.json.")
    kb_show = kb_sub.add_parser("show", help="Mostra o registro de uma ação pelo actionId.")
    kb_show.add_argument("action_id")

    fix_eol = sub.add_parser("fix-robin-eol")
    fix_eol.add_argument("project", nargs="?", default=None)
    fix_eol.add_argument("--all", action="store_true")

    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("project", help="Projeto em input/<projeto>.")
    decision = checkpoint.add_mutually_exclusive_group()
    decision.add_argument(
        "--approve",
        dest="decision",
        action="store_const",
        const="approved",
        help="Grava a aprovação humana no manifesto (exige classificação).",
    )
    decision.add_argument(
        "--reject",
        dest="decision",
        action="store_const",
        const="rejected",
        help="Grava a rejeição humana no manifesto (exige classificação).",
    )
    decision.add_argument(
        "--status",
        dest="decision",
        action="store_const",
        const="status",
        help="Só mostra a decisão atual (padrão quando nenhum outro é dado).",
    )

    phase_done = sub.add_parser(
        "phase-done",
        help="Marca uma fase como em dia no manifesto e as seguintes já existentes como "
        "desatualizadas.",
    )
    phase_done.add_argument("project", help="Projeto em input/<projeto>.")
    phase_done.add_argument("phase", choices=STALE_PHASES)

    classify_check = sub.add_parser(
        "classify-check",
        help="Gate da classificação: contrato, evidência e coerência com o inventário.",
    )
    classify_check.add_argument("project", nargs="?", default=None)
    classify_check.add_argument("--all", action="store_true")

    classify_eval = sub.add_parser(
        "classify-eval", help="Golden set da classificação: prepara os casos e pontua o resultado."
    )
    classify_eval.add_argument("action", choices=["prepare", "score", "clean", "labels"])
    classify_eval.add_argument("--case", action="append", default=None, help="Só este caso.")

    return parser


def _valid_project_name(name: str) -> bool:
    return bool(PROJECT_NAME_RE.fullmatch(name))


def _current_inputs(project_dir: Path) -> list[dict]:
    """SHA256 de cada entrada do projeto — mesmo formato gravado no manifesto.

    Recalculado pelo `checkpoint` para detectar que `input/<projeto>/` mudou
    depois da extração: decisão humana só vale sobre o que foi extraído.
    """
    reject_unsafe_links(project_dir)
    check_input_budget(project_dir)
    inputs = []
    for file in sorted(p for p in project_dir.rglob("*") if p.is_file()):
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        inputs.append(
            {"file": str(file.relative_to(project_dir)).replace("\\", "/"), "sha256": digest}
        )
    return inputs


def _existing_phases(out_dir: Path, phases: list[str] = STALE_PHASES) -> list[str]:
    """Fases que já têm pasta em `output/<projeto>/`: só essas podem estar desatualizadas.

    Fase que ainda não rodou não está "desatualizada", está pendente; marcá-la faria o
    orquestrador ler toda fase como velha e nunca retomar de onde parou.
    """
    return [phase for phase in phases if (out_dir / phase).is_dir()]


def _build_manifest(project_dir: Path, name: str, source_type: str, out_dir: Path) -> dict:
    return {
        "checkpoint": None,
        "extracted_at": datetime.now(UTC).isoformat(),
        "inputs": _current_inputs(project_dir),
        "project": name,
        "reflow_version": __version__,
        "schema_version": "1.0",
        "source_type": source_type,
        "stale_phases": _existing_phases(out_dir),
        "status": "extracted",
        "verdict": None,
    }


def extract_to(project_dir: Path, out_dir: Path) -> tuple[str, Inventory]:
    """Extrai `project_dir` para `out_dir/01-inventory/inventory.json`.

    Só a extração determinística — sem manifesto, sem assumir o layout
    `input/<nome>` → `output/<nome>`. Reaproveitado pelo dashboard local de
    teste isolado (`dashboard/pipeline.py`), que escreve em `.dashboard-runs/`
    em vez de `output/`. A escrita é atômica e sob lock do projeto.
    """
    project_dir = Path(project_dir)
    out_dir = Path(out_dir)
    reject_unsafe_links(project_dir)
    check_input_budget(project_dir)
    extractor = detect_extractor(project_dir)
    with project_lock(out_dir):
        inventory = extractor.extract(project_dir)
        inventory.project = project_dir.name
        write_json_atomic(out_dir / "01-inventory" / "inventory.json", inventory.to_dict())
    return extractor.name, inventory


def _extract_one(root: Path, name: str) -> int:
    project_dir = root / "input" / name
    if not project_dir.is_dir():
        print(f"projeto não encontrado: {name}", file=sys.stderr)
        return 1
    out_dir = root / "output" / name
    try:
        with project_lock(out_dir):
            source_type, inventory = extract_to(project_dir, out_dir)
            write_json_atomic(
                out_dir / "00-manifest.json",
                _build_manifest(project_dir, name, source_type, out_dir),
            )
    except (ValueError, LockError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    counts = (
        f"ui={len(inventory.ui_interactions)} http={len(inventory.http_calls)} "
        f"dados={len(inventory.data_sources)} credenciais={len(inventory.credentials)} "
        f"dependencias={len(inventory.dependencies)} "
        f"desconhecidos={len(inventory.unknown_commands)}"
    )
    print(f"{name}: origem={source_type} {counts}")
    return 0


def _extract_all(root: Path) -> int:
    """Extrai todos os projetos de `input/`, um falhando não derruba os outros.

    Um projeto que lance algo fora de `ValueError` (JSON malformado de forma
    inesperada, disco cheio, `RecursionError` em árvore profunda) é reportado
    e pulado — o lote continua e o exit code fica 1. `KeyboardInterrupt`/`SystemExit`
    não são `Exception`, então interromper o lote continua funcionando.
    """
    input_dir = root / "input"
    if not input_dir.is_dir():
        print("pasta input/ não encontrada", file=sys.stderr)
        return 1
    names = sorted(
        p.name for p in input_dir.iterdir() if p.is_dir() and not p.name.startswith(EVAL_PREFIX)
    )
    exit_code = 0
    failures: list[str] = []
    for name in names:
        try:
            failed = _extract_one(root, name) != 0
        # resiliência de lote: a falha é reportada e o lote segue (ADR-021)
        except Exception as exc:
            print(f"{name}: extração abortou de forma inesperada: {exc!r}", file=sys.stderr)
            failed = True
        if failed:
            exit_code = 1
            failures.append(name)
    if failures:
        print(
            f"lote: {len(names) - len(failures)}/{len(names)} projeto(s) extraído(s); "
            f"falharam: {', '.join(failures)}",
            file=sys.stderr,
        )
    return exit_code


def _cmd_extract(args: argparse.Namespace) -> int:
    root = Path.cwd()
    if args.all:
        return _extract_all(root)
    project = args.project
    if not project or not _valid_project_name(project):
        print(f"nome de projeto inválido: {project}", file=sys.stderr)
        return 1
    return _extract_one(root, project)


def _cmd_report() -> int:
    root = Path.cwd()
    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_batch-report.md").write_text(build_batch_report(root), encoding="utf-8")
    return 0


def _inputs_fingerprint(inputs: list[dict]) -> str:
    """Digest único da lista de entradas — é o que amarra a decisão ao extraído."""
    canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _cmd_checkpoint(args: argparse.Namespace) -> int:
    """Checkpoint humano com vínculo de hash: a decisão só vale sobre o que foi extraído.

    Não é autenticação forte — é rastreabilidade determinística (ver ADR-020):
    a gravação falha se `input/<projeto>/` mudou depois do `extract` ou se
    ainda não existe classificação para decidir.
    """
    root = Path.cwd()
    name = args.project
    if not name or not _valid_project_name(name):
        print(f"nome de projeto inválido: {name}", file=sys.stderr)
        return 1

    project_dir = root / "input" / name
    out_dir = root / "output" / name
    manifest_path = out_dir / "00-manifest.json"
    if not manifest_path.is_file():
        print(
            f"manifesto não encontrado: {manifest_path} — rode `reflow extract {name}` antes.",
            file=sys.stderr,
        )
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    try:
        current_inputs = _current_inputs(project_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if current_inputs != manifest.get("inputs"):
        print(
            f"{name}: entradas mudaram desde a extração — rode `reflow extract {name}` "
            "de novo antes de decidir o checkpoint.",
            file=sys.stderr,
        )
        return 1

    decision = args.decision or "status"
    checkpoint = manifest.get("checkpoint") or {}
    if decision == "status":
        if not checkpoint:
            print(f"{name}: checkpoint pendente (nenhuma decisão gravada).")
            return 0
        label = CHECKPOINT_LABELS.get(checkpoint.get("decision", ""), checkpoint.get("decision"))
        fingerprint = checkpoint.get("inputs_fingerprint")
        if not fingerprint:
            # Gravado à mão antes do ADR-020: sem vínculo de hash, não prova sobre o que
            # a decisão foi tomada. Status informa; só quem decide regrava pela CLI.
            when = checkpoint.get("recorded_at") or checkpoint.get("approved_at") or "data ausente"
            print(
                f"{name}: {label} em {when} (formato legado, sem vínculo de hash; "
                f"quem decide pode regravar com `reflow checkpoint {name} --approve`)."
            )
            return 0
        if fingerprint != _inputs_fingerprint(current_inputs):
            print(
                f"{name}: {label}, mas o fingerprint gravado não confere com as entradas "
                "extraídas — regravar a decisão.",
                file=sys.stderr,
            )
            return 1
        print(
            f"{name}: {label} em {checkpoint.get('recorded_at')} (fingerprint {fingerprint[:12]})"
        )
        return 0

    classification = out_dir / "03-classification" / "classification.md"
    if not classification.is_file():
        print(
            f"{name}: classificação ausente ({classification}) — o checkpoint exige "
            "03-classification antes de qualquer decisão.",
            file=sys.stderr,
        )
        return 1
    verdict = read_verdict(out_dir)
    if decision == "approved" and verdict == "NOT_PAD":
        print(f"{name}: veredito NOT_PAD não tem conversão para aprovar.", file=sys.stderr)
        return 1
    if decision == "approved" and _print_issues(check_project(root, name)):
        print(f"{name}: aprovação recusada, a classificação não passou no gate.", file=sys.stderr)
        return 1

    manifest["checkpoint"] = {
        "classification_sha256": hashlib.sha256(classification.read_bytes()).hexdigest(),
        "decision": decision,
        "inputs_fingerprint": _inputs_fingerprint(current_inputs),
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    try:
        with project_lock(out_dir):
            write_json_atomic(manifest_path, manifest)
    except LockError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"{name}: checkpoint {CHECKPOINT_LABELS[decision]} gravado em {manifest_path}.")
    return 0


# Artefato mínimo que prova que a fase rodou (glob relativo à pasta da fase).
_PHASE_ARTIFACTS = {
    "02-docs": "*.md",
    "03-classification": "classification.md",
    "04-pad": "*/Main.robin",
    "05-test": "*/Main.robin",
}


def _cmd_phase_done(args: argparse.Namespace) -> int:
    """Fecha uma fase no manifesto: sai de `stale_phases`, e as fases seguintes que já
    existem entram (foram geradas a partir da versão anterior desta).

    Chamado pelas skills ao fim de cada fase (os agents não têm shell). Recusa se as
    entradas mudaram desde o `extract` ou se a fase não deixou o artefato esperado.
    """
    root = Path.cwd()
    name = args.project
    if not _valid_project_name(name):
        print(f"nome de projeto inválido: {name}", file=sys.stderr)
        return 1
    out_dir = root / "output" / name
    manifest_path = out_dir / "00-manifest.json"
    if not manifest_path.is_file():
        print(
            f"manifesto não encontrado: {manifest_path} — rode `reflow extract {name}` antes.",
            file=sys.stderr,
        )
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        current_inputs = _current_inputs(root / "input" / name)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if current_inputs != manifest.get("inputs"):
        print(
            f"{name}: entradas mudaram desde a extração — rode `reflow extract {name}` de novo.",
            file=sys.stderr,
        )
        return 1

    phase = args.phase
    if not any((out_dir / phase).glob(_PHASE_ARTIFACTS[phase])):
        print(
            f"{name}: {phase} sem artefato ({_PHASE_ARTIFACTS[phase]}) — a fase não rodou.",
            file=sys.stderr,
        )
        return 1
    if phase == "03-classification" and _print_issues(check_classification(root, name)):
        print(f"{name}: {phase} não fechada, a classificação não passou no gate.", file=sys.stderr)
        return 1

    later = STALE_PHASES[STALE_PHASES.index(phase) + 1 :]
    # Manifesto antigo marcava até fase que nunca rodou: só sobrevive o que existe.
    existing = set(_existing_phases(out_dir))
    stale = {p for p in manifest.get("stale_phases") or [] if p != phase and p in existing}
    stale.update(_existing_phases(out_dir, later))
    manifest["stale_phases"] = [p for p in STALE_PHASES if p in stale]
    try:
        with project_lock(out_dir):
            write_json_atomic(manifest_path, manifest)
    except LockError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    pending = ", ".join(manifest["stale_phases"]) or "nenhuma"
    print(f"{name}: {phase} em dia; fases desatualizadas: {pending}.")
    return 0


def _print_issues(issues: list[Issue]) -> bool:
    """Imprime os achados do gate; True se algum bloqueia."""
    for issue in issues:
        print(f"[{issue.level}] {issue.file}: {issue.message}", file=sys.stderr)
    return bool(errors(issues))


def _cmd_classify_check(args: argparse.Namespace) -> int:
    root = Path.cwd()
    if args.all:
        projects = classified_projects(root)
    elif args.project and _valid_project_name(args.project):
        projects = [args.project]
    else:
        print(f"nome de projeto inválido: {args.project}", file=sys.stderr)
        return 1
    failed = [name for name in projects if _print_issues(check_project(root, name))]
    if failed:
        print(f"classify-check falhou: {', '.join(failed)}.", file=sys.stderr)
        return 2
    print(f"classify-check ok: {len(projects)} projeto(s).")
    return 0


def _cmd_classify_eval(args: argparse.Namespace) -> int:
    root = Path.cwd()
    try:
        cases = classification_eval.load_cases(root, args.case)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not cases:
        print(f"nenhum caso em {classification_eval.EVAL_DIR}", file=sys.stderr)
        return 1
    if args.action == "labels":
        print(classification_eval.render_labels(cases))
        return 0
    if args.action == "prepare":
        result = classification_eval.prepare(root, cases, main)
        if result == 0:
            print(f"{len(cases)} caso(s) prontos: " + ", ".join(c.project for c in cases))
        return result
    if args.action == "clean":
        classification_eval.clean(root, cases)
        print(f"{len(cases)} caso(s) removidos de input/ e output/.")
        return 0
    approved, text = classification_eval.score(root, cases)
    print(text)
    return 0 if approved else 1


def _report_findings(findings: list[Finding], command: str) -> None:
    for finding in findings:
        location = f"{finding.file}:{finding.line}"
        print(f"{location}: {finding.pattern} — {finding.excerpt}", file=sys.stderr)
    print(f"{command} falhou: {len(findings)} achado(s).", file=sys.stderr)


def _cmd_kb(args: argparse.Namespace) -> int:
    root = Path.cwd()
    if args.kb_command == "verify":
        findings = verify_kb(root)
        if findings:
            _report_findings(findings, "kb verify")
            return 2
        manifest = load_manifest(root)
        print(
            f"kb verify ok: {manifest['name']} {manifest['tag']} "
            f"(KB {manifest['kb_version']}, PAD {manifest['pad_build']}), hashes conferem."
        )
        return 0

    action = load_action_kb(root).get(args.action_id.lower())
    if action is None:
        print(f"kb show: ação desconhecida na KB: {args.action_id}", file=sys.stderr)
        return 1
    print(f"actionId:     {action.action_id}  (kind: {action.kind})")
    print(f"exemplo:      {action.golden_example}")
    for param in action.input_params:
        required = "obrigatório" if param.get("required") else "opcional"
        enum = f" valores: {', '.join(param['enumValues'])}" if param.get("enumValues") else ""
        print(f"  entrada     {param['name']}: {param.get('type')} ({required}){enum}")
    for param in action.output_params:
        print(f"  saída       {param['name']}=> {param.get('defaultVariable', '')}")
    print(f"irmãos:       {', '.join(action.sibling_selectors) or '—'}")
    errors = ", ".join(action.errors) or "—"
    print(f"ON ERROR:     {'sim' if action.on_error else 'não'} (erros: {errors})")
    print(f"UI selector:  {'sim (exemplo usa placeholder)' if action.needs_ui_selector else 'não'}")
    print(f"validação:    {action.validation}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"reflow {__version__}")
        raise SystemExit(0)

    if args.command == "scan":
        if args.staged:
            try:
                findings = scan_staged(Path.cwd())
            except StagedScanError as exc:
                print(f"scan --staged falhou: {exc}", file=sys.stderr)
                raise SystemExit(2) from None
        else:
            findings = scan_repository(Path.cwd())
        if findings:
            _report_findings(findings, "scan")
            raise SystemExit(2)
        scope = "índice (staged)" if args.staged else "working tree"
        print(f"scan ok: nenhum padrão sensível encontrado ({scope}).")
        raise SystemExit(0)

    if args.command == "lint-robin":
        findings = lint_robin_files(Path.cwd(), project=args.project)
        if findings:
            _report_findings(findings, "lint-robin")
            raise SystemExit(2)
        print("lint-robin ok: nenhum .robin pendente de validação.")
        raise SystemExit(0)

    if args.command == "fix-robin-eol":
        root = Path.cwd()
        changed = fix_robin_eol(root, project=args.project)
        for path in changed:
            print(f"normalizado para CRLF: {path.relative_to(root)}")
        print(f"fix-robin-eol: {len(changed)} arquivo(s) normalizado(s) para CRLF.")
        return 0

    if args.command == "extract":
        return _cmd_extract(args)

    if args.command == "checkpoint":
        return _cmd_checkpoint(args)

    if args.command == "phase-done":
        return _cmd_phase_done(args)

    if args.command == "report":
        return _cmd_report()

    if args.command == "classify-check":
        return _cmd_classify_check(args)

    if args.command == "classify-eval":
        return _cmd_classify_eval(args)

    if args.command == "kb":
        return _cmd_kb(args)

    parser.print_help()
    return 2
