"""Pré-condições e fechamento de cada agent, o mesmo contrato que as skills impõem.

As skills (`.claude/skills/*/SKILL.md`) são instruções para um harness com shell; o
refold não dá shell ao modelo, então quem roda as checagens e o `phase-done` é este
módulo, chamando o CLI determinístico do `reflow` no mesmo processo.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from reflow import cli as reflow_cli
from reflow.report import read_verdict


class PreconditionError(RuntimeError):
    """O agent não pode rodar agora; a mensagem diz o que falta."""


@dataclass(frozen=True)
class Stage:
    requires: str  # glob relativo a output/<projeto>/ que precisa existir
    phase: str | None  # fase fechada com `reflow phase-done` (None = revisão/curadoria)
    robin: bool = False  # gera Main.robin: normaliza CRLF e passa no lint-robin
    needs_checkpoint: bool = False
    classification_gate: bool = False  # sem phase-done: o gate roda aqui


STAGES = {
    "reflow-documenter": Stage("01-inventory/inventory.json", "02-docs"),
    "reflow-classifier": Stage("02-docs/*.md", "03-classification"),
    "reflow-classification-reviewer": Stage(
        "03-classification/classification.md", None, classification_gate=True
    ),
    "reflow-pad-converter": Stage(
        "03-classification/classification.md", "04-pad", robin=True, needs_checkpoint=True
    ),
    "reflow-robin-reviewer": Stage("04-pad/*/Main.robin", None),
    "reflow-pad-tester": Stage("04-pad/*/Main.robin", "05-test", robin=True),
    "reflow-truth-table-curator": Stage("01-inventory/inventory.json", None),
}


def stage_for(agent: str) -> Stage:
    try:
        return STAGES[agent]
    except KeyError as exc:
        raise PreconditionError(f"{agent}: agent sem contrato no refold (ver STAGES)") from exc


def check(root: Path, agent: str, project: str) -> Stage:
    stage = stage_for(agent)
    if not reflow_cli.PROJECT_NAME_RE.fullmatch(project):
        raise PreconditionError(f"nome de projeto inválido: {project}")
    out_dir = root / "output" / project
    manifest_path = out_dir / "00-manifest.json"
    if not manifest_path.is_file():
        raise PreconditionError(f"{project}: sem manifesto, rode `reflow extract {project}`")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        current = reflow_cli._current_inputs(root / "input" / project)
    except ValueError as exc:
        raise PreconditionError(str(exc)) from exc
    if current != manifest.get("inputs"):
        raise PreconditionError(
            f"{project}: input/ mudou desde o extract, rode `reflow extract {project}` de novo"
        )
    if not any(out_dir.glob(stage.requires)):
        raise PreconditionError(f"{project}: falta output/{project}/{stage.requires}")
    if stage.needs_checkpoint:
        _check_checkpoint(out_dir, manifest, current, project)
    return stage


def _check_checkpoint(out_dir: Path, manifest: dict, current: list, project: str) -> None:
    if read_verdict(out_dir) == "NOT_PAD":
        raise PreconditionError(f"{project}: NOT_PAD não tem conversão")
    checkpoint = manifest.get("checkpoint") or {}
    fingerprint = checkpoint.get("inputs_fingerprint")
    if checkpoint and not fingerprint:
        # Restritivo: o checkpoint legado não prova sobre o que foi aprovado.
        raise PreconditionError(
            f"{project}: checkpoint em formato legado, quem aprova deve regravar com "
            f"`reflow checkpoint {project} --approve`"
        )
    if checkpoint.get("decision") != "approved":
        raise PreconditionError(f"{project}: checkpoint humano não aprovado")
    if fingerprint != reflow_cli._inputs_fingerprint(current):
        raise PreconditionError(f"{project}: fingerprint do checkpoint não confere")


def close(
    agent: str,
    project: str,
    written: list[str],
    run_cli: Callable[[list[str]], int] = reflow_cli.main,
) -> list[str]:
    """Roda os passos determinísticos de fechamento. Devolve as falhas (vazio = ok)."""
    stage = stage_for(agent)
    if not written:
        return [f"{agent} não gravou nenhum arquivo; fase não fechada"]
    if stage.robin:
        if run_cli(["fix-robin-eol", project]) != 0:
            return ["fix-robin-eol falhou; fase não fechada"]
        if run_cli(["lint-robin", project]) != 0:
            return ["lint-robin reprovou o Main.robin; fase não fechada"]
    if stage.classification_gate and run_cli(["classify-check", project]) != 0:
        return ["classify-check reprovou a revisão; ver mensagens acima"]
    if stage.phase and run_cli(["phase-done", project, stage.phase]) != 0:
        return [f"phase-done {stage.phase} recusou; ver mensagem acima"]
    return []
