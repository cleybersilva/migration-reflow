"""CLI do refold.

    uv run python -m refold agents                      # agents e escopo de escrita
    uv run python -m refold check                       # configuração (sem rede)
    uv run python -m refold run <agent> <projeto> --dry-run   # pré-condições + prompt, sem rede
    uv run python -m refold run <agent> <projeto>       # chama a API e fecha a fase
    uv run python -m refold classify <projeto>          # classificador, gate, revisor, gate
    uv run python -m refold classify --eval             # o mesmo no golden set, e pontua
    uv run python -m refold migrate <projeto>           # pipeline com orçamento em dólar
    uv run python -m refold estimate <projeto>          # custo estimado, sem chamar a API

Rodar sempre da raiz do repositório, como o `reflow`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from reflow import classification_eval
from reflow import cli as reflow_cli

from . import __version__, migrate, pipeline
from .agents import AgentError, list_agents, load_agent
from .client import ClientError, MessagesClient, load_config
from .loop import build_system, run_agent
from .tools import Sandbox

RUNS_DIR = ".refold-runs"
CLASSIFICATION_AGENTS = ("reflow-classifier", "reflow-classification-reviewer")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="refold", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"refold {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("agents", help="Lista os agents canônicos e o escopo de escrita.")
    sub.add_parser("check", help="Confere as variáveis de ambiente, sem chamar a API.")
    run = sub.add_parser("run", help="Roda um agent sobre um projeto.")
    run.add_argument("agent")
    run.add_argument("project")
    run.add_argument("--dry-run", action="store_true", help="Não chama a API.")
    classify = sub.add_parser("classify", help="Classifica e revisa um projeto, com gate.")
    classify.add_argument("project", nargs="?", default=None)
    classify.add_argument("--eval", action="store_true", help="Roda no golden set e pontua.")
    budgeted = sub.add_parser("migrate", help="Roda o pipeline com orçamento e para no checkpoint.")
    budgeted.add_argument("project")
    budgeted.add_argument("--budget", type=float, default=migrate.DEFAULT_BUDGET_USD)
    estimate = sub.add_parser("estimate", help="Estima o custo por migração, sem chamar a API.")
    estimate.add_argument("project")
    estimate.add_argument("--model", default=None, help="Padrão: IARA_MODEL.")
    return parser


def _cmd_agents(root: Path) -> int:
    for spec in list_agents(root):
        scope = ", ".join(spec.write_globs) or "(só leitura)"
        print(f"{spec.name}  steps={spec.steps}  escrita: {scope}")
    return 0


def _cmd_check() -> int:
    config = load_config()
    print(f"ok: {config.base_url}/messages, modelo {config.model}, auth {config.auth}")
    return 0


def _cmd_run(root: Path, agent: str, project: str, dry_run: bool) -> int:
    spec = load_agent(root, agent)
    pipeline.check(root, agent, project)
    sandbox = Sandbox(root, project, spec.write_globs)
    if dry_run:
        print(build_system(spec, sandbox))
        print(f"\n[dry-run] pré-condições ok; {spec.steps} turnos no máximo; API não chamada.")
        return 0

    client = MessagesClient(load_config())
    runs = root / RUNS_DIR
    runs.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = runs / f"{stamp}-{agent}-{project}.jsonl"
    with log_path.open("a", encoding="utf-8") as log_file:

        def log(event: dict) -> None:
            log_file.write(json.dumps(event, ensure_ascii=False) + "\n")
            log_file.flush()

        result = run_agent(spec, sandbox, client.create, log)
        log({"result": result.stop_reason, "written": result.written, "usage": result.usage})

    print(result.text)
    print(
        f"\n[refold] {agent} em {project}: {result.stop_reason} após {result.steps} turnos; "
        f"tokens in/out {result.usage.get('input_tokens')}/{result.usage.get('output_tokens')}; "
        f"log em {log_path.relative_to(root).as_posix()}"
    )
    for path in result.written:
        print(f"  gravado: {path}")
    if not result.finished:
        print("[refold] o agent não terminou; fase não fechada.", file=sys.stderr)
        return 1
    failures = pipeline.close(agent, project, result.written)
    for failure in failures:
        print(f"[refold] {failure}", file=sys.stderr)
    return 1 if failures else 0


def _classify_project(root: Path, project: str) -> int:
    """Duas execuções isoladas: o revisor nunca herda a conversa do classificador."""
    for agent in CLASSIFICATION_AGENTS:
        result = _cmd_run(root, agent, project, False)
        if result != 0:
            return result
    return 0


def _cmd_classify_eval(root: Path) -> int:
    cases = classification_eval.load_cases(root)
    if classification_eval.prepare(root, cases, reflow_cli.main) != 0:
        return 1
    for case in cases:
        # Um caso que falha entra na nota como falha; não derruba o resto do lote.
        if _classify_project(root, case.project) != 0:
            print(f"[refold] {case.name}: execução incompleta", file=sys.stderr)
    approved, text = classification_eval.score(root, cases)
    print(text)
    return 0 if approved else 1


def _cmd_classify(root: Path, project: str | None, evaluate: bool) -> int:
    if evaluate:
        return _cmd_classify_eval(root)
    if not project:
        print("refold: informe o projeto ou --eval", file=sys.stderr)
        return 1
    return _classify_project(root, project)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):  # console Windows em cp1252 não imprime "→"
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "agents":
            return _cmd_agents(root)
        if args.command == "check":
            return _cmd_check()
        if args.command == "classify":
            return _cmd_classify(root, args.project, args.eval)
        if args.command == "migrate":
            return migrate.run(root, args.project, args.budget)
        if args.command == "estimate":
            return migrate.estimate(root, args.project, args.model)
        return _cmd_run(root, args.agent, args.project, args.dry_run)
    except (AgentError, ClientError, pipeline.PreconditionError, migrate.BudgetError) as exc:
        print(f"refold: {exc}", file=sys.stderr)
        return 1
