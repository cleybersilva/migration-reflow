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

_SENSITIVE_KEY_WORDS = (
    r"password|passwd|pwd|secret|api[_-]?key|access[_-]?key|private[_-]?key"
    r"|token|bearer|authorization|connection[_-]?string"
)
SECRET_KEY_RE = re.compile(rf"(?i)\b(?:{_SENSITIVE_KEY_WORDS})\b")
SECRET_ASSIGNMENT_RE = re.compile(
    # Duas formas de "chave", a mesma cauda `[:=] valor` para as duas:
    # - chave nua (estilo env/Python, ex. variável igual valor);  # reflow:allow-secret
    # - chave JSON com aspas exatamente ao redor da palavra.
    # Sem a segunda forma, o padrão nunca batia com uma chave JSON entre
    # aspas seguida de `: "valor"`  # reflow:allow-secret
    # (a aspa que fecha a chave vem antes do `:`, e a primeira forma não
    # admite nada entre a chave e `[:=]`). A aspa exata (não um `['"]?`
    # solto depois da chave) evita casar o sufixo de uma chave JSON maior
    # como `X-Reflow-Token` (que contém a palavra "Token" mas não é, ela
    # mesma, uma chave sensível isolada).
    rf"(?i)(?:\b(?:{_SENSITIVE_KEY_WORDS})\b|[\"'](?:{_SENSITIVE_KEY_WORDS})[\"'])"
    # O valor também para numa crase (`` ` ``, fora do set de aspas acima):
    # sem isto, uma menção em Markdown tipo "`id-token: write` (permissão
    # OIDC)" engolia a crase de fechamento do span de código inteiro como se
    # fosse parte do valor ("write`"), nunca batendo com um valor-placeholder
    # de uma palavra só — reprovando prosa que só documenta a própria chave
    # sensível, não um segredo. Crase nunca é delimitador de string em
    # nenhuma linguagem que este scanner varre (Python, JSON, YAML, .env),
    # então excluí-la do valor nunca perde a detecção de um segredo real.
    r"\s*[:=]\s*(?P<quote>['\"]?)(?P<value>[^'\"\s`]+)(?P=quote)"
)

# Cabeçalho de autorização por token (ou a mesma palavra solta em texto livre):
# sem isto, SECRET_ASSIGNMENT_RE captura a palavra-chave do esquema como se
# fosse o valor (porque é o primeiro token sem espaço após o `:`) e deixa o
# token real intacto depois dela. Aplicado antes de SECRET_ASSIGNMENT_RE em
# mask_secrets() para consumir o par "palavra-chave + token" inteiro.
BEARER_TOKEN_RE = re.compile(r"(?i)\bbearer\s+[^'\"\s]+")

CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\(\d{2}\)\s?9?\d{4}-\d{4}")
BANK_ACCOUNT_RE = re.compile(r"(?i)\b(agência|agencia|conta)(\s*[:=]?\s*)(\d[\d.-]{2,10}\d)")

PLACEHOLDER_VALUES = frozenset(
    {
        "",
        "xxx",
        "changeme",
        "todo",
        "placeholder",
        "***",
        # Vocabulário fechado do bloco "permissions" do GitHub Actions (YAML).
        # Uma chave como "id-token" contém a palavra sensível "token", mas o
        # valor atribuído a ela nunca é um segredo — é um escopo de permissão
        # de um conjunto fixo e documentado pelo GitHub.
        "read",
        "write",
        "none",
    }
)


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

    # Bearer primeiro: remove "bearer <token>" por inteiro para que a passada de
    # SECRET_ASSIGNMENT_RE (que roda depois) só veja "Authorization: ***" e não
    # tente capturar a palavra "Bearer" como valor.
    masked = BEARER_TOKEN_RE.sub("***", text)
    return SECRET_ASSIGNMENT_RE.sub(_redact, masked)


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

    Além de mascarar segredo/PII dentro do próprio texto de uma string (via
    `mask()`), também mascara pelo nome da chave: numa estrutura JSON a chave
    sensível (`password`, `token`, `api_key`, `authorization`,
    `connection_string`, ...) e o valor são strings separadas, então
    `mask_secrets` sozinho (que só reconhece `chave: valor` dentro do mesmo
    texto) nunca veria a associação — um dict com essa chave e um valor real
    passava intacto.
    """
    return _mask_data(value, key_is_sensitive=False)


def _mask_data(value: Any, *, key_is_sensitive: bool) -> Any:
    if isinstance(value, str):
        if key_is_sensitive and not is_placeholder_value(value):
            return "***"
        return mask(value)
    if isinstance(value, list):
        return [_mask_data(item, key_is_sensitive=key_is_sensitive) for item in value]
    if isinstance(value, dict):
        return {
            (mask(key) if isinstance(key, str) else key): _mask_data(
                item,
                key_is_sensitive=isinstance(key, str) and bool(SECRET_KEY_RE.search(key)),
            )
            for key, item in value.items()
        }
    return value
