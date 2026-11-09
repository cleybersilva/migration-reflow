"""Pacote de contexto por agent: só o necessário, montado sem LLM, para gastar menos tokens.

Em vez de cada agent explorar `reference/` turno a turno, recebe um único arquivo com as
seções que o projeto usa. Tudo passa pelo mascaramento antes de chegar a um modelo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .robin.generate import GENERATION_NAME
from .robin.kb import load_action_kb
from .robin.syntax import analyze_robin
from .security.masking import mask

CLASSIFICATION_NAME = "classification.md"
PACK_DIR = "_context"
RUBRIC = "reference/classification-rubric.md"
CONVENTIONS = "reference/robin-conventions.md"
ACTIONS = "reference/robin-actions.md"
CATALOG = "reference/subfluxos-comuns.md"
PACKED_AGENTS = (
    "reflow-documenter",
    "reflow-classifier",
    "reflow-classification-reviewer",
    "reflow-robin-optimizer",
    "reflow-robin-reviewer",
    "reflow-pad-tester",
)
# Ações que o otimizador pode acrescentar sem origem no legado. As de fechamento só entram
# se o projeto usa o módulo; sem elas, o agent conclui que o recurso não tem como fechar.
_CONTROL_ACTIONS = {"SET", "IF", "BLOCK"}
_CLOSING_ACTIONS = {
    "Excel": {"Excel.CloseExcel.Close", "Excel.CloseExcel.CloseAndSave"},
    "WebAutomation": {"WebAutomation.CloseWebBrowser"},
    "Database": {"Database.Close"},
}
_SECTION_RE = re.compile(r"^### `([^`]+)`[^\n]*\n(.*?)(?=^### |^## |\Z)", re.MULTILINE | re.DOTALL)


def _compact_inventory(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = []
    for key in sorted(data):
        value = data[key]
        if isinstance(value, list) and value and isinstance(value[0], dict):
            lines.append(f"{key}:")
            lines.extend(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value)
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines)


def _whitelist_sections(root: Path, actions: set[str]) -> str:
    text = (root / ACTIONS).read_text(encoding="utf-8")
    found = [
        f"### `{name}`\n{body.strip()}"
        for name, body in _SECTION_RE.findall(text)
        if name in actions
    ]
    return "\n\n".join(found)


def _flow_files(out: Path) -> list[Path]:
    return sorted((out / "04-pad").glob("*/Main.robin"))


def _used_actions(root: Path, out: Path) -> set[str]:
    """Ações da base e do flow atual: o otimizador pode ter acrescentado alguma à base."""
    used: set[str] = set()
    for meta in sorted((out / "04-pad").glob(f"*/{GENERATION_NAME}")):
        data = json.loads(meta.read_text(encoding="utf-8"))
        used.update(step["action"] for step in data.get("steps", []) if step.get("action"))
    kb = load_action_kb(root)
    for path in _flow_files(out):
        text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
        used.update(action for _, action in analyze_robin(text, kb)[1])
    return used


def _project_actions(root: Path, out: Path) -> set[str]:
    used = _used_actions(root, out)
    actions = used | _CONTROL_ACTIONS
    for module, closing in _CLOSING_ACTIONS.items():
        if any(action.startswith(f"{module}.") for action in used):
            actions |= closing
    return actions


def _docs(out: Path, names: tuple[str, ...] | None = None) -> list[tuple[str, str]]:
    folder = out / "02-docs"
    files = sorted(folder.glob("*.md")) if names is None else [folder / name for name in names]
    return [
        (f"02-docs/{path.name}", path.read_text(encoding="utf-8"))
        for path in files
        if path.is_file()
    ]


def _inventory_section(out: Path) -> tuple[str, str]:
    return "01-inventory/inventory.json", _compact_inventory(
        out / "01-inventory" / "inventory.json"
    )


def _complexity_section(out: Path) -> list[tuple[str, str]]:
    path = out / "01-inventory" / "complexity.json"
    return (
        [("01-inventory/complexity.json", path.read_text(encoding="utf-8"))]
        if path.is_file()
        else []
    )


def sections(root: Path, project: str, agent: str) -> list[tuple[str, str]]:
    out = root / "output" / project
    read = lambda rel: (root / rel).read_text(encoding="utf-8")  # noqa: E731
    if agent == "reflow-documenter":
        return [_inventory_section(out), *_complexity_section(out)]
    if agent == "reflow-classifier":
        return [(RUBRIC, read(RUBRIC)), _inventory_section(out), *_docs(out)]
    if agent == "reflow-classification-reviewer":
        classification = out / "03-classification" / CLASSIFICATION_NAME
        return [
            (RUBRIC, read(RUBRIC)),
            _inventory_section(out),
            *_docs(out),
            (
                f"03-classification/{CLASSIFICATION_NAME}",
                classification.read_text(encoding="utf-8"),
            ),
        ]
    if agent not in PACKED_AGENTS:
        raise ValueError(f"agent sem pacote de contexto: {agent}")

    flows = [
        (path.relative_to(out).as_posix(), path.read_bytes().decode("utf-8").replace("\r\n", "\n"))
        for path in _flow_files(out)
    ]
    uses = _docs(out, ("use-cases.md", "business-rules.md"))
    whitelist = _whitelist_sections(root, _project_actions(root, out))
    if agent == "reflow-robin-optimizer":
        # Main.robin já traz id, origem e evidência de cada passo: generation.json só repetiria.
        return [
            (CONVENTIONS, read(CONVENTIONS)),
            (f"{ACTIONS} (só as ações deste projeto)", whitelist),
            (CATALOG, read(CATALOG)),
            *uses,
            *flows,
        ]
    if agent == "reflow-robin-reviewer":
        notes = [
            (path.relative_to(out).as_posix(), path.read_text(encoding="utf-8"))
            for path in sorted((out / "04-pad").glob("*/notas-conversao.md"))
        ]
        return [
            (CATALOG, read(CATALOG)),
            (f"{ACTIONS} (só as ações deste projeto)", whitelist),
            *uses,
            *notes,
            *flows,
        ]
    return [
        (CONVENTIONS, read(CONVENTIONS)),
        (f"{ACTIONS} (só as ações deste projeto)", whitelist),
        *uses,
        *flows,
    ]


def build_pack(root: Path, project: str, agent: str) -> str:
    parts = [f"# Contexto de {agent} para {project}", ""]
    for label, content in sections(root, project, agent):
        parts.extend([f"## {label}", "", content.strip(), ""])
    # Sem manter a referência, o agent lê `ConnectionString: ***` e acusa um defeito que não existe.
    return mask("\n".join(parts), keep_references=True)


def write_pack(root: Path, project: str, agent: str) -> Path:
    path = root / "output" / project / PACK_DIR / f"{agent}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_pack(root, project, agent), encoding="utf-8")
    return path
