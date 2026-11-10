"""Gate do otimizador: o LLM pode melhorar a base determinística, nunca desfigurá-la.

Compara `Main.robin` com `Main.generated.robin` e `generation.json`. Erro bloqueia e o
harness restaura a base; aviso só informa. O lint-robin continua cobrindo a sintaxe.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from ..classification import Issue
from .generate import BASE_NAME, GENERATION_NAME
from .kb import load_action_kb
from .syntax import analyze_robin

_SET_CFG_RE = re.compile(r"^SET\s+(cfg_\w+)\s+TO\s+(.*)$", re.MULTILINE)
_EMPTY_TEXT = "$''''''"
_ARG_TEXT_RE = re.compile(r"\w+:\s*\$'''(.*?)'''")
_STEP_NUMBER_RE = re.compile(r"^step_\d+_")
# Texto que o `reflow generate` grava na base; mudou lá, muda aqui (teste cobre os dois).
_OPEN_HANDLE_TODO = "# TODO reflow: instância sem fechamento"


def generated_flows(root: Path, project: str) -> list[Path]:
    return sorted((root / "output" / project / "04-pad").glob(f"*/{GENERATION_NAME}"))


def _text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def check_flow(root: Path, meta_path: Path) -> list[Issue]:
    folder = meta_path.parent
    rel = folder.relative_to(root).as_posix()
    base_path = folder / BASE_NAME
    current_path = folder / "Main.robin"
    if not base_path.is_file() or not current_path.is_file():
        return [Issue("erro", rel, "falta Main.robin ou Main.generated.robin")]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if hashlib.sha256(base_path.read_bytes()).hexdigest() != meta.get("robin_sha256"):
        return [Issue("erro", rel, "a base determinística foi editada; rode reflow generate")]

    base, current = _text(base_path), _text(current_path)
    issues: list[Issue] = []
    for step in meta.get("steps", []):
        number = _STEP_NUMBER_RE.match(step["id"])
        anchor = number.group(0) if number else step["id"]
        if anchor not in current:
            issues.append(Issue("erro", rel, f"passo removido: {step['id']}"))
        if step["evidence"] not in current:
            issues.append(Issue("erro", rel, f"evidência removida: {step['evidence']}"))

    kb = load_action_kb(root)
    base_actions = [action for _, action in analyze_robin(base, kb)[1]]
    current_actions = [action for _, action in analyze_robin(current, kb)[1]]
    for action in sorted(set(base_actions)):
        if current_actions.count(action) < base_actions.count(action):
            issues.append(Issue("erro", rel, f"ação da base removida: {action}"))

    base_values = {value for _, value in _SET_CFG_RE.findall(base)}
    for name, value in _SET_CFG_RE.findall(current):
        # Renomear é permitido; só um valor que a base não tinha é invenção.
        if value not in base_values and value.strip() != _EMPTY_TEXT:
            issues.append(Issue("erro", rel, f"{name}: valor inventado, sem origem no inventário"))
    if current.count("# TODO reflow") < base.count("# TODO reflow"):
        issues.append(Issue("aviso", rel, "há menos TODO reflow que na base; conferir o motivo"))

    known = set(_ARG_TEXT_RE.findall(base))
    for value in _ARG_TEXT_RE.findall(current):
        if value not in known and re.sub(r"%[^%]*%", "", value).strip(" /\\:"):
            issues.append(Issue("aviso", rel, f"literal novo em argumento: {value[:60]}"))
    return issues


def optimization_flows(root: Path, project: str) -> list[str]:
    """Flows cuja base tem o que só o otimizador resolve: recurso aberto sem fechamento.

    Renomear e reagrupar não pagam uma chamada de LLM, e ligar variáveis não aconteceu em
    nenhum dos 3 robôs medidos, porque os casos de uso não provavam a ligação (ADR-036).
    """
    names = []
    for meta_path in generated_flows(root, project):
        base_path = meta_path.parent / BASE_NAME
        if base_path.is_file() and _OPEN_HANDLE_TODO in _text(base_path):
            names.append(meta_path.parent.name)
    return names


def optimization_reasons(root: Path, project: str) -> list[str]:
    """Vazio: o otimizador é pulado e a base determinística segue como resultado."""
    return [f"{name}: recurso aberto sem fechamento" for name in optimization_flows(root, project)]


def check_project(root: Path, project: str) -> list[Issue]:
    issues: list[Issue] = []
    for meta_path in generated_flows(root, project):
        issues.extend(check_flow(root, meta_path))
    return issues


def restore_base(root: Path, project: str) -> list[str]:
    """Devolve a base aos flows: é o resultado garantido quando o LLM falha ou estoura."""
    restored = []
    for meta_path in generated_flows(root, project):
        folder = meta_path.parent
        shutil.copyfile(folder / BASE_NAME, folder / "Main.robin")
        restored.append(folder.name)
    return restored
