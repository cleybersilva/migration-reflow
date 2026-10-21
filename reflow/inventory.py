"""Esquema estável do inventário gerado pela extração determinística."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

FACT_FIELDS: tuple[str, ...] = (
    "credentials",
    "data_sources",
    "dependencies",
    "http_calls",
    "ui_interactions",
)


@dataclass
class Inventory:
    project: str = ""
    source_type: str = ""
    schema_version: str = "1.0"
    files: list[str] = field(default_factory=list)
    credentials: list[dict] = field(default_factory=list)
    data_sources: list[dict] = field(default_factory=list)
    dependencies: list[dict] = field(default_factory=list)
    http_calls: list[dict] = field(default_factory=list)
    ui_interactions: list[dict] = field(default_factory=list)
    unknown_commands: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
