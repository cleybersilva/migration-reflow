"""CLI do refold.

    uv run python -m refold agents                      # agents e escopo de escrita
    uv run python -m refold check                       # configuração (sem rede)
    uv run python -m refold run <agent> <projeto> --dry-run   # pré-condições + prompt, sem rede
    uv run python -m refold run <agent> <projeto>       # chama a API e fecha a fase

Rodar sempre da raiz do repositório, como o `reflow`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import __version__, pipeline
from .agents import AgentError, list_agents, load_agent
from .client import ClientError, MessagesClient, load_config
from .loop import build_system, run_agent
from .tools import Sandbox

RUNS_DIR = ".refold-runs"


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
        return _cmd_run(root, args.agent, args.project, args.dry_run)
    except (AgentError, ClientError, pipeline.PreconditionError) as exc:
        print(f"refold: {exc}", file=sys.stderr)
        return 1
