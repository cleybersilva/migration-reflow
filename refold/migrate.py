"""Migração com orçamento: cada estágio de LLM recebe um teto em dólar, medido pela API.

Antes do checkpoint humano roda documentação, classificação e revisão, e para. Depois dele,
a base é gerada sem LLM e o resto só a melhora. Estourou o teto de um estágio opcional? Ele é
pulado ou descartado e a base determinística segue valendo: o orçamento nunca derruba o
piso de qualidade, nem pula o gate ou o checkpoint. Só o refold impõe este orçamento.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from reflow import cli as reflow_cli
from reflow import context_pack
from reflow.fs import write_json_atomic
from reflow.robin import optimize

from . import pipeline
from .agents import load_agent
from .client import MessagesClient, load_config
from .loop import RunResult, build_system, run_agent
from .pricing import USAGE_KEYS, Price, resolve_price
from .tools import TOOL_SCHEMAS, Sandbox

DEFAULT_BUDGET_USD = 1.00
LEDGER_NAME = "cost.json"
MIN_STAGE_USD = 0.02
CHARS_PER_TOKEN = 3.5
OPTIMIZER = "reflow-robin-optimizer"


class BudgetError(RuntimeError):
    """A migração não pode começar ou continuar; a mensagem diz o motivo."""


@dataclass(frozen=True)
class BudgetStage:
    agent: str
    share: float
    steps: int
    required: bool
    done: str  # glob relativo a output/<projeto>/: existe = estágio já feito
    assumed_output_tokens: int  # só para `refold estimate`


BEFORE_CHECKPOINT = (
    BudgetStage("reflow-documenter", 0.20, 10, True, "02-docs/*.md", 5000),
    BudgetStage("reflow-classifier", 0.15, 6, True, "03-classification/classification.md", 1800),
    BudgetStage(
        "reflow-classification-reviewer",
        0.10,
        6,
        False,
        "03-classification/review.md",
        1200,
    ),
)
AFTER_CHECKPOINT = (
    BudgetStage(OPTIMIZER, 0.25, 6, False, "", 2500),
    BudgetStage("reflow-robin-reviewer", 0.10, 5, False, "04-pad/*/review.md", 800),
    BudgetStage("reflow-pad-tester", 0.20, 8, False, "05-test/*/Main.robin", 3000),
)
Create = Callable[[str, list[dict], list[dict]], dict]


def _ledger_path(root: Path, project: str) -> Path:
    return root / "output" / project / LEDGER_NAME


def _load_ledger(root: Path, project: str, budget: float, model: str) -> dict:
    path = _ledger_path(root, project)
    if path.is_file():
        ledger = json.loads(path.read_text(encoding="utf-8"))
        ledger["budget_usd"] = budget
        return ledger
    return {"budget_usd": budget, "model": model, "total_usd": 0.0, "stages": []}


def _record(
    root: Path, project: str, ledger: dict, stage: str, status: str, result: RunResult | None
) -> None:
    usage = result.usage if result else dict.fromkeys(USAGE_KEYS, 0)
    cost = result.cost_usd if result else 0.0
    ledger["total_usd"] = round(ledger["total_usd"] + cost, 6)
    ledger["stages"].append(
        {
            "agent": stage,
            "status": status,
            "cost_usd": round(cost, 6),
            "steps": result.steps if result else 0,
            "usage": usage,
            "at": datetime.now(UTC).isoformat(),
        }
    )
    write_json_atomic(_ledger_path(root, project), ledger)
    print(f"[refold] {stage}: {status}, US$ {cost:.4f} (total US$ {ledger['total_usd']:.4f})")


def _stage_limit(
    budget: float, spent: float, stage: BudgetStage, pending: list[BudgetStage]
) -> float:
    """O que sobrou, dividido pelas cotas do que falta: economia num estágio passa adiante."""
    shares = sum(item.share for item in pending)
    return max(budget - spent, 0.0) * stage.share / shares if shares else 0.0


def _run_stage(
    root: Path,
    project: str,
    stage: BudgetStage,
    create: Create,
    price: Price,
    limit: float,
) -> RunResult:
    pipeline.check(root, stage.agent, project)
    spec = replace(load_agent(root, stage.agent), steps=stage.steps)
    context = context_pack.build_pack(root, project, stage.agent)
    sandbox = Sandbox(root, project, spec.write_globs)
    return run_agent(spec, sandbox, create, context=context, price=price, limit_usd=limit)


def _done(root: Path, project: str, stage: BudgetStage, ledger: dict) -> bool:
    finished = any(
        item["agent"] == stage.agent and item["status"] in {"ok", "descartado"}
        for item in ledger["stages"]
    )
    out = root / "output" / project
    return finished or bool(stage.done and any(out.glob(stage.done)))


def _run_group(
    root: Path,
    project: str,
    stages: tuple[BudgetStage, ...],
    create: Create,
    price: Price,
    ledger: dict,
    run_cli: Callable[[list[str]], int],
) -> bool:
    """Devolve False só quando um estágio obrigatório não terminou."""
    budget = ledger["budget_usd"]
    pending = [stage for stage in stages if not _done(root, project, stage, ledger)]
    later = AFTER_CHECKPOINT if stages is BEFORE_CHECKPOINT else ()
    while pending:
        stage = pending.pop(0)
        limit = _stage_limit(budget, ledger["total_usd"], stage, [stage, *pending, *later])
        if limit < MIN_STAGE_USD:
            _record(root, project, ledger, stage.agent, "sem orçamento", None)
            if stage.required:
                return False
            continue
        print(f"[refold] {stage.agent}: teto US$ {limit:.4f}")
        result = _run_stage(root, project, stage, create, price, limit)
        # O teto pode parar o agent logo depois de gravar: o flow já foi pago, e o gate decide
        # se ele fica. Só o otimizador tem gate sobre o arquivo inteiro para isso ser seguro.
        paid_write = stage.agent == OPTIMIZER and result.stop_reason == "budget" and result.written
        complete = result.finished or bool(paid_write)
        failures = pipeline.close(stage.agent, project, result.written, run_cli) if complete else []
        if complete and not failures:
            _record(root, project, ledger, stage.agent, "ok", result)
            continue
        for failure in failures:
            print(f"[refold] {failure}", file=sys.stderr)
        if stage.agent == OPTIMIZER:
            # O que foi pago não volta, mas otimização reprovada não chega ao analista.
            optimize.restore_base(root, project)
            run_cli(["phase-done", project, "04-pad"])
            _record(root, project, ledger, stage.agent, "descartado", result)
            continue
        _record(root, project, ledger, stage.agent, f"falhou ({result.stop_reason})", result)
        if stage.required:
            return False
    return True


def _summary(root: Path, project: str, ledger: dict) -> None:
    total, budget = ledger["total_usd"], ledger["budget_usd"]
    print(f"[refold] custo de {project}: US$ {total:.4f} de US$ {budget:.2f}")
    print(f"[refold] ledger: output/{project}/{LEDGER_NAME}")


def run(
    root: Path,
    project: str,
    budget: float = DEFAULT_BUDGET_USD,
    create: Create | None = None,
    model: str | None = None,
    run_cli: Callable[[list[str]], int] = reflow_cli.main,
) -> int:
    if budget <= 0:
        raise BudgetError("o orçamento precisa ser positivo")
    if create is None:
        config = load_config()
        create, model = MessagesClient(config).create, config.model
    price = resolve_price(model or "")
    if price is None:
        raise BudgetError(
            f"preço do modelo {model} desconhecido; defina REFOLD_PRICE_INPUT e "
            "REFOLD_PRICE_OUTPUT (US$ por milhão de tokens)"
        )
    if not (root / "output" / project / "00-manifest.json").is_file():
        raise BudgetError(f"{project}: sem manifesto, rode `reflow extract {project}`")
    ledger = _load_ledger(root, project, budget, model or "")

    if not _run_group(root, project, BEFORE_CHECKPOINT, create, price, ledger, run_cli):
        _summary(root, project, ledger)
        print(f"[refold] {project}: estágio obrigatório incompleto.", file=sys.stderr)
        return 1

    out = root / "output" / project
    manifest = json.loads((out / "00-manifest.json").read_text(encoding="utf-8"))
    current = reflow_cli._current_inputs(root / "input" / project)
    if problem := reflow_cli.checkpoint_problem(out, manifest, current):
        _summary(root, project, ledger)
        print(f"[refold] parado no checkpoint humano: {problem}")
        return 0

    if not optimize.generated_flows(root, project):
        if run_cli(["generate", project]) != 0:
            return 1
        if run_cli(["fix-robin-eol", project]) != 0 or run_cli(["lint-robin", project]) != 0:
            print(f"[refold] {project}: a base gerada não passou no lint.", file=sys.stderr)
            return 1
        if run_cli(["phase-done", project, "04-pad"]) != 0:
            return 1
    _run_group(root, project, AFTER_CHECKPOINT, create, price, ledger, run_cli)
    _summary(root, project, ledger)
    return 0


def _pack_tokens(root: Path, project: str, stage: BudgetStage) -> int | None:
    spec = load_agent(root, stage.agent)
    sandbox = Sandbox(root, project, spec.write_globs)
    fixed = len(build_system(spec, sandbox)) + len(json.dumps(TOOL_SCHEMAS))
    try:
        return int(
            (fixed + len(context_pack.build_pack(root, project, stage.agent))) / CHARS_PER_TOKEN
        )
    except FileNotFoundError:
        return None


def estimate(root: Path, project: str, model: str | None) -> int:
    """Conta os caracteres que cada estágio realmente receberia e aplica o preço.

    É estimativa: supõe dois turnos por estágio (gravar e encerrar), e não enxerga o thinking,
    cobrado como saída. O número que vale é o `cost.json` de uma execução real.
    """
    if model is None:
        model = load_config().model
    price = resolve_price(model)
    if price is None:
        raise BudgetError(f"preço do modelo {model} desconhecido; defina REFOLD_PRICE_*")
    total = 0.0
    print(f"Estimativa para {project}, modelo {model} (não medida):")
    for stage in (*BEFORE_CHECKPOINT, *AFTER_CHECKPOINT):
        tokens = _pack_tokens(root, project, stage)
        if tokens is None:
            print(f"- {stage.agent}: falta artefato anterior, sem como estimar")
            continue
        output = stage.assumed_output_tokens
        cost = price.cost({"input_tokens": tokens * 2 + output, "output_tokens": output})
        total += cost
        print(f"- {stage.agent}: entrada {tokens} tokens por turno, US$ {cost:.3f}")
    print(f"Total estimado: US$ {total:.2f}")
    return 0
