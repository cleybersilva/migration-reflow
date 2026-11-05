"""Leitura da PAD Robin Action KB vendorizada (`reference/vendor/pad-robin-kb/`).

A KB é dado de referência de terceiros (CC BY 4.0), copiada sem modificação e
travada por hash em `manifest.json`. Este módulo só lê JSON: nunca executa nada
da KB nem faz rede. `verify_kb` é um gate: qualquer arquivo ausente, extra ou
com hash divergente vira achado, e quem chama falha de forma restritiva.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from ..security.scan import Finding

KB_DIR = Path("reference") / "vendor" / "pad-robin-kb"
MANIFEST_NAME = "manifest.json"
ACTION_KB_NAME = "PAD_Robin_ActionKB.json"
TYPE_REFERENCE_NAME = "PAD_Robin_TypeReference.json"
RULES_NAME = "robin-rules.json"
PROBE_CORPUS_NAME = "probe-corpus.json"

# Conjunto fechado: o manifesto não pode passar a "abençoar" outro arquivo
# qualquer (a isenção do scan depende dele, ver security/scan.py).
VENDORED_FILES = frozenset(
    {
        ACTION_KB_NAME,
        TYPE_REFERENCE_NAME,
        RULES_NAME,
        PROBE_CORPUS_NAME,
        "PROMPT.md",
        "LICENSE",
    }
)
# Arquivos do próprio reflow dentro da pasta, fora do manifesto (e escaneados normalmente).
LOCAL_FILES = frozenset({MANIFEST_NAME, "README.md"})


@dataclass(frozen=True)
class KbAction:
    action_id: str
    module: str
    kind: str
    template: str
    golden_example: str
    input_params: tuple[dict, ...] = ()
    output_params: tuple[dict, ...] = ()
    sibling_selectors: tuple[str, ...] = ()
    needs_ui_selector: bool = False
    on_error: bool = True
    errors: tuple[str, ...] = ()
    validation: str = ""
    constraints: dict = field(default_factory=dict)

    @property
    def input_names(self) -> frozenset[str]:
        return frozenset(p["name"].lower() for p in self.input_params)

    @property
    def output_names(self) -> frozenset[str]:
        return frozenset(p["name"].lower() for p in self.output_params)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(root: Path) -> dict:
    path = root / KB_DIR / MANIFEST_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def pinned_hashes(root: Path) -> dict[str, str]:
    """`{caminho relativo ao repo (com /): sha256}` dos arquivos vendorizados.

    Só entra arquivo do conjunto fechado `VENDORED_FILES`; manifesto ausente
    ou ilegível devolve `{}` (nenhuma isenção, nunca o contrário)."""
    try:
        manifest = load_manifest(root)
    except (OSError, ValueError):
        return {}
    prefix = str(KB_DIR).replace("\\", "/")
    pinned: dict[str, str] = {}
    for entry in manifest.get("files", []):
        name = entry.get("path")
        digest = entry.get("sha256")
        if name in VENDORED_FILES and isinstance(digest, str):
            pinned[f"{prefix}/{name}"] = digest
    return pinned


def verify_kb(root: Path) -> list[Finding]:
    """Confere a cópia vendorizada contra o manifesto. Lista vazia = íntegra."""
    kb_dir = root / KB_DIR
    rel = str(KB_DIR).replace("\\", "/")
    manifest_rel = f"{rel}/{MANIFEST_NAME}"
    try:
        manifest = load_manifest(root)
    except (OSError, ValueError) as exc:
        return [Finding(manifest_rel, 1, "kb_manifesto_invalido", str(exc)[:120])]

    findings: list[Finding] = []
    if manifest.get("modified") is not False:
        findings.append(
            Finding(manifest_rel, 1, "kb_modificada", "a cópia vendorizada tem que ser sem edição")
        )
    listed = {entry.get("path"): entry for entry in manifest.get("files", [])}
    for name in sorted(set(listed) ^ VENDORED_FILES):
        findings.append(
            Finding(manifest_rel, 1, "kb_lista_de_arquivos", f"arquivo fora do conjunto: {name}")
        )
    for name in sorted(VENDORED_FILES & set(listed)):
        path = kb_dir / name
        if not path.is_file():
            findings.append(Finding(f"{rel}/{name}", 1, "kb_arquivo_ausente", name))
        elif _sha256(path) != listed[name].get("sha256"):
            findings.append(
                Finding(f"{rel}/{name}", 1, "kb_hash_divergente", "sha256 difere do manifesto")
            )
    if kb_dir.is_dir():
        for path in sorted(kb_dir.iterdir()):
            if path.name not in VENDORED_FILES | LOCAL_FILES:
                findings.append(
                    Finding(f"{rel}/{path.name}", 1, "kb_arquivo_extra", "fora do manifesto")
                )
    return findings


def _to_action(record: dict) -> KbAction:
    handling = record.get("error_handling") or {}
    return KbAction(
        action_id=record["actionId"],
        module=record.get("module", ""),
        kind=record.get("kind", "Action"),
        template=record.get("template", ""),
        golden_example=record.get("golden_example", ""),
        input_params=tuple(record.get("input_params") or ()),
        output_params=tuple(record.get("output_params") or ()),
        sibling_selectors=tuple(record.get("sibling_selectors") or ()),
        needs_ui_selector=bool(record.get("needs_ui_selector")),
        on_error=bool(handling.get("on_error", True)),
        errors=tuple(handling.get("errors") or ()),
        validation=record.get("validation", ""),
        constraints=dict(record.get("constraints") or {}),
    )


def load_action_kb(root: Path) -> dict[str, KbAction]:
    """Índice `{actionId em minúsculas: KbAction}` (Robin não diferencia caixa)."""
    data = json.loads((root / KB_DIR / ACTION_KB_NAME).read_text(encoding="utf-8"))
    return {record["actionId"].lower(): _to_action(record) for record in data["actions"]}


def kb_modules(actions: dict[str, KbAction]) -> frozenset[str]:
    """Módulos conhecidos (em minúsculas): distingue `Excel.X` (ação) de `Obj.prop`."""
    return frozenset(action.action_id.split(".")[0].lower() for action in actions.values())
