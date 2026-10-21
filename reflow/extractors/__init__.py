"""Registro de extractors e detecção por prioridade: A360 > .NET > Python."""

from __future__ import annotations

from pathlib import Path

from .a360 import A360Extractor
from .dotnet import DotnetExtractor
from .python import PythonExtractor

_PRIORITY = (A360Extractor, DotnetExtractor, PythonExtractor)


def detect_extractor(path: Path):
    for extractor_cls in _PRIORITY:
        instance = extractor_cls()
        if instance.detect(Path(path)):
            return instance
    raise ValueError(f"nenhuma origem suportada em {path}")
