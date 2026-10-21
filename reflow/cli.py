"""CLI determinística: extract/report prontos; scan/lint-robin falham de forma restritiva."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .extractors import detect_extractor
from .inventory import Inventory
from .report import build_batch_report
from .robin import lint_robin_files
from .security.scan import Finding, scan_repository

PROJECT_NAME_RE = re.compile(r"[a-z0-9_-]+")
STALE_PHASES = ["02-docs", "03-classification", "04-pad", "05-test"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reflow")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")

    extract = sub.add_parser("extract")
    extract.add_argument("project", nargs="?", default=None)
    extract.add_argument("--all", action="store_true")

    sub.add_parser("report")
    sub.add_parser("scan")

    lint = sub.add_parser("lint-robin")
    lint.add_argument("project", nargs="?", default=None)
    lint.add_argument("--all", action="store_true")

    return parser


def _valid_project_name(name: str) -> bool:
    return bool(PROJECT_NAME_RE.fullmatch(name))


def _build_manifest(project_dir: Path, name: str, source_type: str) -> dict:
    inputs = []
    for file in sorted(p for p in project_dir.rglob("*") if p.is_file()):
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        inputs.append(
            {"file": str(file.relative_to(project_dir)).replace("\\", "/"), "sha256": digest}
        )
    return {
        "checkpoint": None,
        "extracted_at": datetime.now(UTC).isoformat(),
        "inputs": inputs,
        "project": name,
        "reflow_version": __version__,
        "schema_version": "1.0",
        "source_type": source_type,
        "stale_phases": list(STALE_PHASES),
        "status": "extracted",
        "verdict": None,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def extract_to(project_dir: Path, out_dir: Path) -> tuple[str, Inventory]:
    """Extrai `project_dir` para `out_dir/01-inventory/inventory.json`.

    Só a extração determinística — sem manifesto, sem assumir o layout
    `input/<nome>` → `output/<nome>`. Reaproveitado pelo dashboard local de
    teste isolado (`dashboard/pipeline.py`), que escreve em `.dashboard-runs/`
    em vez de `output/`.
    """
    extractor = detect_extractor(project_dir)
    inventory = extractor.extract(project_dir)
    inventory.project = project_dir.name
    _write_json(out_dir / "01-inventory" / "inventory.json", inventory.to_dict())
    return extractor.name, inventory


def _extract_one(root: Path, name: str) -> int:
    project_dir = root / "input" / name
    if not project_dir.is_dir():
        print(f"projeto não encontrado: {name}", file=sys.stderr)
        return 1
    out_dir = root / "output" / name
    try:
        source_type, inventory = extract_to(project_dir, out_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _write_json(out_dir / "00-manifest.json", _build_manifest(project_dir, name, source_type))

    counts = (
        f"ui={len(inventory.ui_interactions)} http={len(inventory.http_calls)} "
        f"dados={len(inventory.data_sources)} credenciais={len(inventory.credentials)} "
        f"dependencias={len(inventory.dependencies)} "
        f"desconhecidos={len(inventory.unknown_commands)}"
    )
    print(f"{name}: origem={source_type} {counts}")
    return 0


def _extract_all(root: Path) -> int:
    input_dir = root / "input"
    if not input_dir.is_dir():
        print("pasta input/ não encontrada", file=sys.stderr)
        return 1
    names = sorted(p.name for p in input_dir.iterdir() if p.is_dir())
    exit_code = 0
    for name in names:
        if _extract_one(root, name) != 0:
            exit_code = 1
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


def _report_findings(findings: list[Finding], command: str) -> None:
    for finding in findings:
        location = f"{finding.file}:{finding.line}"
        print(f"{location}: {finding.pattern} — {finding.excerpt}", file=sys.stderr)
    print(f"{command} falhou: {len(findings)} achado(s).", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"reflow {__version__}")
        raise SystemExit(0)

    if args.command == "scan":
        findings = scan_repository(Path.cwd())
        if findings:
            _report_findings(findings, "scan")
            raise SystemExit(2)
        print("scan ok: nenhum padrão sensível encontrado.")
        raise SystemExit(0)

    if args.command == "lint-robin":
        findings = lint_robin_files(Path.cwd(), project=args.project)
        if findings:
            _report_findings(findings, "lint-robin")
            raise SystemExit(2)
        print("lint-robin ok: nenhum .robin pendente de validação.")
        raise SystemExit(0)

    if args.command == "extract":
        return _cmd_extract(args)

    if args.command == "report":
        return _cmd_report()

    parser.print_help()
    return 2
