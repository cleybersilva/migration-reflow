"""Complexidade da automação (P, M ou G), calculada só a partir do inventário.

Regra simples e auditável: cada dimensão recebe uma faixa e a pior faixa vence. Os limites
são uma proposta inicial (ADR-035), ainda não calibrados com robôs reais pelo analista.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

COMPLEXITY_NAME = "complexity.json"
_ORDER = {"P": 0, "M": 1, "G": 2}
_INTEGRATIONS = ("ui_interactions", "http_calls", "data_sources", "scripts", "credentials")

# (dimensão, rótulo, maior valor ainda P, maior valor ainda M).
LIMITS = (
    ("steps", "passos", 15, 50),
    ("unknown_commands", "comandos desconhecidos", 0, 5),
    ("bot_dependencies", "bots chamados", 0, 3),
    ("integration_types", "tipos de integração", 2, 5),
    ("credentials", "credenciais", 1, 3),
)


@dataclass(frozen=True)
class Complexity:
    size: str
    confidence: str
    metrics: dict[str, int]
    drivers: tuple[str, ...]
    limits_status: str = "proposta, a calibrar com o analista"


def _band(value: int, small: int, medium: int) -> str:
    if value <= small:
        return "P"
    return "M" if value <= medium else "G"


def assess(inventory: dict) -> Complexity:
    """Classifica um inventário. Só A360 tem confiança alta: o extractor enxerga cada passo.

    Em Python e .NET o inventário registra imports e chamadas conhecidas, não o fluxo nem a
    automação de tela, então o resultado tende a subestimar o tamanho real.
    """
    a360 = inventory.get("source_type") == "a360"
    dependencies = inventory.get("dependencies", [])
    bots = [d for d in dependencies if d.get("kind") != "import"]
    unknown = len(inventory.get("unknown_commands", []))
    used = [name for name in _INTEGRATIONS if inventory.get(name)]
    metrics = {
        "steps": sum(len(inventory.get(name, [])) for name in _INTEGRATIONS) + len(bots) + unknown,
        "unknown_commands": unknown,
        "bot_dependencies": len(bots),
        "integration_types": len(used) + bool(bots),
        "credentials": len(inventory.get("credentials", [])),
    }
    bands = {name: _band(metrics[name], small, medium) for name, _, small, medium in LIMITS}
    size = max(bands.values(), key=_ORDER.__getitem__)
    drivers = tuple(
        f"{label}: {metrics[name]}"
        for name, label, _, _ in LIMITS
        if bands[name] == size and size != "P"
    )
    return Complexity(size, "alta" if a360 else "baixa", metrics, drivers)


def write_assessment(out_dir: Path, inventory: dict) -> Complexity:
    result = assess(inventory)
    path = out_dir / "01-inventory" / COMPLEXITY_NAME
    data = asdict(result)
    data["drivers"] = list(result.drivers)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def read_size(out_dir: Path) -> str:
    """Tamanho gravado, ou calculado na hora para manifesto extraído antes desta fase."""
    saved = out_dir / "01-inventory" / COMPLEXITY_NAME
    if saved.is_file():
        return json.loads(saved.read_text(encoding="utf-8"))["size"]
    inventory = out_dir / "01-inventory" / "inventory.json"
    if not inventory.is_file():
        return "—"
    return assess(json.loads(inventory.read_text(encoding="utf-8"))).size
