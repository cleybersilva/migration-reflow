"""Gerador determinístico do `Main.robin`: inventário + tabela verdade + KB, sem LLM.

É a base da migração (ADR-035). Toda ação vem do `golden_example` da KB, que colou no PAD,
e entra só se a tabela verdade e a whitelist a permitirem; o resto vira `# TODO reflow`.
O inventário guarda nomes de atributos, nunca valores: todo texto vira `cfg_` vazia.
Nomes vindos do legado são dados, e passam por `_safe` antes de ir para o flow.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .kb import KbAction, load_action_kb
from .syntax import _parse_action, _scan
from .whitelist import load_truth_table, load_whitelist, truth_table_action_name

GENERATOR_VERSION = "1"
BASE_NAME = "Main.generated.robin"
GENERATION_NAME = "generation.json"
CATALOG_PATH = Path("reference") / "subfluxos-comuns.md"
CREDENTIAL_SLUG = "obter-credencial-do-cofre"
_CATEGORIES = {
    "ui_interactions": "Interação com telas",
    "data_sources": "Leitura e gravação de dados",
    "http_calls": "Chamadas externas",
    "credentials": "Credenciais",
    "dependencies": "Subflows",
    "unknown_commands": "Pendências de mapeamento",
}
_COMMENT_UNSAFE_RE = re.compile(r"[^\w .:/-]+")
_NUMBER_RE = re.compile(r"-?\d+")
_ENUM_VALUE_RE = re.compile(r"[A-Za-z]\w*\.[A-Za-z]\w*\.\w+")
_METHOD_RE = re.compile(r"`Method: (Web\.Method\.\w+)`")
_SUBFLOW_RE = re.compile(r"[A-Za-z]\w*")
_TEXT_TYPES = {"String", "EncryptableObject", "FileObject"}
_EMPTY_TEXT = "$''''''"


class GenerateError(ValueError):
    """Projeto que o gerador não consegue processar; a mensagem diz o motivo."""


@dataclass(frozen=True)
class Step:
    file: str
    line: int
    origin: str
    category: str
    package: str = ""
    command: str = ""
    attributes: tuple[str, ...] = ()
    target: str | None = None


@dataclass
class RenderedStep:
    step_id: str
    evidence: str
    origin: str
    region: str
    comments: list[str]
    line: str | None = None
    action: str | None = None
    status: str | None = None
    note: str = ""
    reason: str = ""


@dataclass
class Flow:
    name: str
    source: str
    steps: list[RenderedStep] = field(default_factory=list)
    configs: list[tuple[str, str]] = field(default_factory=list)
    open_handles: list[str] = field(default_factory=list)


def _safe(text: object, limit: int = 60) -> str:
    return _COMMENT_UNSAFE_RE.sub("_", str(text))[:limit]


def _snake(text: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return re.sub(r"[^a-z0-9]+", "_", spaced.lower()).strip("_") or "x"


def collect_steps(inventory: dict) -> list[Step]:
    steps = []
    for category in _CATEGORIES:
        for fact in inventory.get(category, []):
            if fact.get("kind") == "import":
                continue
            package = fact.get("packageName", "")
            command = fact.get("commandName", "")
            origin = f"{package}.{command}" if package else str(fact.get("operation", category))
            steps.append(
                Step(
                    fact.get("file", ""),
                    int(fact.get("line", 0)),
                    _safe(origin),
                    category,
                    package,
                    command,
                    tuple(_safe(name, 40) for name in fact.get("attribute_names", [])),
                    fact.get("target"),
                )
            )
    return sorted(steps, key=lambda step: (step.file, step.line))


class _Mapper:
    def __init__(self, root: Path) -> None:
        self.kb: dict[str, KbAction] = load_action_kb(root)
        self.whitelist = load_whitelist(root)
        self.table = {
            (row["Pacote A360"], row["Comando A360"]): row for row in load_truth_table(root)
        }
        catalog = root / CATALOG_PATH
        self.catalog_text = catalog.read_text(encoding="utf-8") if catalog.is_file() else ""
        self.standard = {}
        for raw in self.catalog_text.splitlines():
            cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
            if len(cells) == 3 and cells[0].startswith("`"):
                self.standard[cells[0].strip("`")] = cells[1].strip("*")

    def credential_is_cataloged(self) -> bool:
        heading = self.catalog_text.find(f"### `{CREDENTIAL_SLUG}`")
        if heading < 0:
            return False
        return "**Status**: `catalogado`" in self.catalog_text[heading:].split("\n### ")[0]


def _todo(step: Step, step_id: str, reason: str, region: str) -> RenderedStep:
    evidence = f"{_safe(step.file)}:{step.line}"
    return RenderedStep(
        step_id,
        evidence,
        step.origin,
        region,
        [f"# {step_id} | origem {step.origin} ({evidence})", f"# TODO reflow: {reason}"],
        reason=reason,
    )


def _render_call(mapper: _Mapper, step: Step, step_id: str, region: str) -> RenderedStep:
    name = (step.target or "").removesuffix(".json")
    if not name or not _SUBFLOW_RE.fullmatch(name):
        return _todo(step, step_id, "bot filho não resolvido no export; localizar o bot", region)
    situation = mapper.standard.get(name)
    if situation == "descontinuado":
        return _todo(
            step,
            step_id,
            f"{name} está descontinuado (ver reference/subfluxos-comuns.md); pedir ao analista "
            "o subflow substituto",
            region,
        )
    subflow_id = f"{step_id}_subflow_{_snake(name)}"
    status = mapper.whitelist["CALL"].status if "CALL" in mapper.whitelist else None
    if status is None or status.lower().startswith("[não validado"):
        return _todo(step, subflow_id, "instrução CALL sem status utilizável na whitelist", region)
    evidence = f"{_safe(step.file)}:{step.line}"
    note = (
        "subflow padrão já disponível no PAD, reaproveitar"
        if situation == "ativo"
        else "criar o subflow no designer e colar o corpo do flow do bot filho"
    )
    return RenderedStep(
        subflow_id,
        evidence,
        step.origin,
        f"Subflow: {name}",
        [f"# {subflow_id} | origem {step.origin} ({evidence}) | status {status}", f"# {note}"],
        line=f"CALL {name}" if situation == "ativo" else f"CALL Subflow_{name}",
        action="CALL",
        status=status,
        note=note,
    )


def _render_action(
    mapper: _Mapper, step: Step, step_id: str, region: str, flow: Flow, outputs: dict[str, str]
) -> RenderedStep:
    row = mapper.table.get((step.package, step.command))
    if row is None:
        return _todo(step, step_id, "comando fora da tabela verdade (a360-to-pad.md)", region)
    action_id = truth_table_action_name(row)
    entry = mapper.whitelist.get(action_id or "")
    if action_id is None or entry is None or entry.status.lower().startswith("[não validado"):
        return _todo(step, step_id, f"{action_id or 'sem ação PAD'} sem sintaxe confirmada", region)
    record = mapper.kb.get(action_id.lower())
    if record is None:
        return _todo(step, step_id, f"{action_id} ausente da KB", region)
    if record.needs_ui_selector:
        return _todo(step, step_id, f"{action_id}: gravar o elemento de UI no designer", region)

    statements, issues = _scan(record.golden_example)
    if issues or len(statements) != 1:
        return _todo(step, step_id, f"{action_id}: exemplo da KB não interpretável", region)
    _, arguments, golden_outputs = _parse_action(statements[0].bare)
    params = {param["name"].lower(): param for param in record.input_params}
    method = _METHOD_RE.search(row.get("Observações", ""))

    configs: list[tuple[str, str]] = []
    parts = [action_id]
    for name, value in arguments:
        param = params.get(name.lower(), {})
        kind = str(param.get("type", ""))
        if name == "Method" and method:
            parts.append(f"{name}: {method.group(1)}")
            continue
        config = f"cfg_{step_id.removeprefix('step_')}_{_snake(name)}"
        # Senha opcional fica vazia: uma cfg_ convidaria a colar o segredo no flow (A4).
        if not param.get("required") and (value == _EMPTY_TEXT or "password" in name.lower()):
            value = _EMPTY_TEXT
            parts.append(f"{name}: {value}")
        elif value.startswith('"') or (kind in _TEXT_TYPES and not _ENUM_VALUE_RE.fullmatch(value)):
            configs.append((config, "$''''''"))
            parts.append(f"{name}: {config}")
        elif _NUMBER_RE.fullmatch(value):
            default = param.get("default", param.get("defaultValue"))
            if default in (None, ""):
                configs.append((config, value))
                parts.append(f"{name}: {config}")
            else:
                parts.append(f"{name}: {value}")
        elif value in {"True", "False"} or _ENUM_VALUE_RE.fullmatch(value):
            parts.append(f"{name}: {value}")
        else:
            source = outputs.get("DataTable" if kind == "Object" else kind)
            if source is None:
                return _todo(
                    step, step_id, f"{action_id}: nenhum passo anterior gera {name}", region
                )
            parts.append(f"{name}: {source}")
            if action_id.split(".")[1].startswith("Close") and source in flow.open_handles:
                flow.open_handles.remove(source)

    produced = {param["name"].lower(): param for param in record.output_params}
    for name, _ in golden_outputs:
        variable = f"out_{step_id.removeprefix('step_')}_{_snake(name)}"
        parts.append(f"{name}=> {variable}")
        kind = str(produced.get(name.lower(), {}).get("type", ""))
        outputs[kind] = variable
        if kind.endswith("Handle"):
            flow.open_handles.append(variable)

    flow.configs.extend(configs)
    evidence = f"{_safe(step.file)}:{step.line}"
    attributes = ", ".join(step.attributes) or "nenhum"
    comments = [
        f"# {step_id} | origem {step.origin} ({evidence}) | atributos: {attributes} | "
        f"status {entry.status}"
    ]
    if configs:
        comments.append(
            "# TODO reflow: preencher "
            + ", ".join(name for name, _ in configs)
            + f" (valores não capturados; {evidence})"
        )
    if {name.lower() for name in step.attributes} & {"authorization", "password", "token"}:
        comments.append("# TODO reflow: segredo nunca literal; usar entrada sensível in_ (A4)")
    return RenderedStep(
        step_id,
        evidence,
        step.origin,
        region,
        comments,
        line=" ".join(parts),
        action=action_id,
        status=entry.status,
        note=row.get("Observações", ""),
    )


def _render_step(
    mapper: _Mapper, step: Step, number: int, flow: Flow, outputs: dict[str, str]
) -> RenderedStep:
    step_id = f"step_{number:02d}_{_snake(step.origin)[:40]}"
    region = _CATEGORIES[step.category]
    if step.category == "credentials":
        cataloged = mapper.credential_is_cataloged()
        slug = _snake(CREDENTIAL_SLUG)
        return _todo(
            step,
            f"{step_id}_subfluxo_comum_{slug}" if cataloged else step_id,
            "origem da credencial a decidir com o analista (entrada sensível in_ ou cofre); "
            "nunca copiar o valor (A4)",
            "Subfluxo comum: Obter credencial do cofre (candidato a reuso)"
            if cataloged
            else region,
        )
    if step.category == "unknown_commands":
        return _todo(step, step_id, "comando desconhecido; requer revisão humana", region)
    if not step.package:
        return _todo(step, step_id, "origem sem mapeamento automático para o PAD", region)
    if step.category == "dependencies":
        return _render_call(mapper, step, step_id, region)
    return _render_action(mapper, step, step_id, region, flow, outputs)


def _render_robin(project: str, flow: Flow) -> str:
    converted = sum(1 for step in flow.steps if step.line)
    lines = [
        f"# {project} / {flow.name}: gerado por reflow generate, sem LLM (origem {flow.source}).",
        f"# Passos: {len(flow.steps)}; com ação: {converted}; pendentes: "
        f"{len(flow.steps) - converted}. Nada aqui foi executado no PAD.",
        "",
    ]
    if flow.configs:
        lines.append("# TODO reflow: a extração não captura valores; preencher com o analista.")
        lines.extend(f"SET {name} TO {value}" for name, value in flow.configs)
        lines.append("")
    current = None
    for step in flow.steps:
        if step.region != current:
            if current is not None:
                lines.extend(["**ENDREGION", ""])
            lines.append(f"**REGION {step.region}")
            current = step.region
        lines.extend(step.comments)
        if step.line:
            lines.append(step.line)
    if current is not None:
        lines.append("**ENDREGION")
    if flow.open_handles:
        lines.extend(
            [
                "",
                "# TODO reflow: instância sem fechamento no legado: "
                f"{', '.join(flow.open_handles)}.",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_notes(flow: Flow, whitelist: dict) -> str:
    used: dict[str, list[str]] = {}
    for step in flow.steps:
        if step.action:
            used.setdefault(step.action, []).append(step.step_id)
    lines = [f"# Notas de conversão: {flow.name}", "", "Geradas por `reflow generate`.", ""]
    for action, steps in sorted(used.items()):
        status = whitelist[action].status if action in whitelist else ""
        lines.append(f"- `{action}`: {', '.join(steps)}; status {status}")
    if flow.configs and "SET" in whitelist:
        lines.append(f"- `SET`: configuração `cfg_`; status {whitelist['SET'].status}")
    return "\n".join(lines) + "\n"


def _render_readme(project: str, flow: Flow, size: str) -> str:
    converted = [step for step in flow.steps if step.line]
    pending = [step for step in flow.steps if not step.line]
    lines = [
        f"# {flow.name}",
        "",
        f"Flow gerado de forma determinística para `{project}` (origem `{flow.source}`).",
        f"Complexidade: **{size}**. Passos: {len(flow.steps)}; com ação: {len(converted)}; "
        f"pendentes: {len(pending)}.",
        "",
        "## Pendências",
        "",
    ]
    lines.extend(f"- `{step.step_id}` ({step.evidence}): {step.reason}" for step in pending)
    if not pending:
        lines.append("- Nenhum passo sem ação; os valores `cfg_` ainda precisam ser preenchidos.")
    lines.extend(
        [
            "",
            "## Teste",
            "",
            "Colar no PAD Designer depois de preencher as `cfg_`. Nenhum resultado PASS/FAIL "
            "existe até um analista rodar o flow.",
        ]
    )
    return "\n".join(lines) + "\n"


def _crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def build_flows(root: Path, inventory: dict) -> tuple[list[Flow], dict]:
    mapper = _Mapper(root)
    groups: dict[str, list[Step]] = {}
    a360 = inventory.get("source_type") == "a360"
    for step in collect_steps(inventory):
        groups.setdefault(step.file if a360 else "legado", []).append(step)
    flows = []
    used_names: set[str] = set()
    for source, steps in sorted(groups.items()):
        stem = re.sub(r"[^a-z0-9]+", "-", Path(source).stem.lower()).strip("-") or "main"
        name = f"flow-{stem}"
        while name in used_names:
            name += "-x"
        used_names.add(name)
        flow = Flow(name, _safe(source))
        outputs: dict[str, str] = {}
        for number, step in enumerate(steps, 1):
            flow.steps.append(_render_step(mapper, step, number, flow, outputs))
        flows.append(flow)
    return flows, mapper.whitelist


def generate_project(
    root: Path, project: str, inventory: dict, fingerprint: str, size: str, force: bool = False
) -> list[Flow]:
    """Grava cada flow em `04-pad/<flow>/`. Recusa sobrescrever o que já foi otimizado."""
    flows, whitelist = build_flows(root, inventory)
    if not flows:
        raise GenerateError(f"{project}: inventário sem passos para gerar")
    pad = root / "output" / project / "04-pad"
    for flow in flows:
        target = pad / flow.name / "Main.robin"
        meta = pad / flow.name / GENERATION_NAME
        if target.is_file() and not force:
            pinned = (
                json.loads(meta.read_text("utf-8")).get("robin_sha256") if meta.is_file() else ""
            )
            if hashlib.sha256(target.read_bytes()).hexdigest() != pinned:
                raise GenerateError(
                    f"{project}: {flow.name}/Main.robin foi alterado depois da geração; "
                    "use --force para descartar essas mudanças"
                )
    for flow in flows:
        folder = pad / flow.name
        folder.mkdir(parents=True, exist_ok=True)
        robin = _crlf(_render_robin(project, flow))
        (folder / BASE_NAME).write_bytes(robin)
        (folder / "Main.robin").write_bytes(robin)
        (folder / "README.md").write_text(_render_readme(project, flow, size), encoding="utf-8")
        (folder / "notas-conversao.md").write_text(_render_notes(flow, whitelist), encoding="utf-8")
        metadata = {
            "generator_version": GENERATOR_VERSION,
            "inputs_fingerprint": fingerprint,
            "project": project,
            "flow": flow.name,
            "robin_sha256": hashlib.sha256(robin).hexdigest(),
            "configs": [name for name, _ in flow.configs],
            "steps": [
                {
                    "id": step.step_id,
                    "evidence": step.evidence,
                    "origin": step.origin,
                    "action": step.action,
                    "status": step.status,
                    "note": step.note,
                }
                for step in flow.steps
            ],
        }
        (folder / GENERATION_NAME).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return flows
