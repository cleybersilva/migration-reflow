"""Mascaramento de segredos e PII — última linha de defesa sobre texto livre.

Os extractors evitam capturar valor de atributo (só nomes), mas warnings e
achados do scan podem carregar trechos de texto livre do legado. Este módulo
é a fonte única dos padrões de segredo/PII e de como mascará-los antes que o
texto vá para output/, docs/ ou o terminal (inclusive os achados do próprio
`reflow scan`).
"""

from __future__ import annotations

import re
from typing import Any

SECRET_KEY_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|private[_-]?key"
    r"|token|bearer|authorization|connection[_-]?string)\b"
)
SECRET_ASSIGNMENT_RE = re.compile(
    SECRET_KEY_RE.pattern + r"\s*[:=]\s*(?P<quote>['\"]?)(?P<value>[^'\"\s]+)(?P=quote)"
)

CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\(\d{2}\)\s?9?\d{4}-\d{4}")
BANK_ACCOUNT_RE = re.compile(r"(?i)\b(agência|agencia|conta)(\s*[:=]?\s*)(\d[\d.-]{2,10}\d)")

PLACEHOLDER_VALUES = frozenset({"", "xxx", "changeme", "todo", "placeholder", "***"})


def is_placeholder_value(value: str) -> bool:
    """True quando o valor claramente não é um segredo real (fixture/placeholder)."""
    stripped = value.strip()
    if not stripped or stripped.lower() in PLACEHOLDER_VALUES:
        return True
    if stripped.startswith("{env:") and stripped.endswith("}"):
        return True
    lowered = stripped.lower()
    return "synthetic" in lowered or lowered.startswith("not-a-real")


def mask_secrets(text: str) -> str:
    """Troca o valor atribuído a uma chave sensível por `***`, preservando a chave."""

    def _redact(match: re.Match[str]) -> str:
        return match.group(0).replace(match.group("value"), "***")

    return SECRET_ASSIGNMENT_RE.sub(_redact, text)


def mask_pii(text: str) -> str:
    """Mascara CPF, CNPJ, e-mail, telefone e agência/conta em texto livre."""
    masked = CPF_RE.sub("[CPF mascarado]", text)
    masked = CNPJ_RE.sub("[CNPJ mascarado]", masked)
    masked = EMAIL_RE.sub("[e-mail mascarado]", masked)
    masked = PHONE_RE.sub("[telefone mascarado]", masked)
    masked = BANK_ACCOUNT_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}[mascarado]", masked)
    return masked


def mask(text: str) -> str:
    """Aplica as duas máscaras — segredos e PII — em qualquer texto livre."""
    return mask_pii(mask_secrets(text))


def mask_data(value: Any) -> Any:
    """Aplica `mask()` recursivamente em toda string-folha (e chave) de um valor.

    Usado pelo dashboard local antes de gravar ou emitir qualquer evento/log
    que tenha passado por um JSON do legado ou de um modelo de linguagem.
    """
    if isinstance(value, str):
        return mask(value)
    if isinstance(value, list):
        return [mask_data(item) for item in value]
    if isinstance(value, dict):
        return {
            (mask(key) if isinstance(key, str) else key): mask_data(item)
            for key, item in value.items()
        }
    return value
