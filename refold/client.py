"""Cliente mínimo da API Anthropic Messages (`POST {IARA_BASE_URL}/messages`), só stdlib.

Configuração por ambiente, mesmos nomes do OpenCode (ADR-002), nunca por arquivo:
- `IARA_BASE_URL`: termina em `/v1`; https obrigatório (http só para loopback).
- `IARA_API_KEY`: chave; nunca é impressa nem gravada.
- `IARA_MODEL`: modelo exposto pelo endpoint.
- `REFOLD_AUTH` (opcional): `x-api-key` (padrão, API Anthropic) ou `bearer` (proxy).
- `REFOLD_MAX_TOKENS` (opcional, padrão 8192).
- `REFOLD_PROMPT_CACHE=1` (opcional): pede cache do prompt; ligue só se o endpoint aceitar.
- `REFOLD_EFFORT` (opcional): `low`, `medium`, `high` ou `xhigh`; idem.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

from reflow.security.masking import mask

ANTHROPIC_VERSION = "2023-06-01"
RETRY_STATUS = {408, 429, 500, 502, 503, 504, 529}
MAX_ATTEMPTS = 4
TIMEOUT_SECONDS = 300

# (url, headers, corpo) -> (status, corpo da resposta). Injetável para testes sem rede.
Transport = Callable[[str, dict[str, str], bytes], tuple[int, bytes]]


class ClientError(RuntimeError):
    """Falha de configuração ou de chamada; a mensagem nunca contém a chave."""


@dataclass(frozen=True)
class Config:
    base_url: str
    key: str
    model: str
    auth: str = "x-api-key"
    max_tokens: int = 8192
    prompt_cache: bool = False
    effort: str | None = None

    def __repr__(self) -> str:  # nunca vazar a chave em log/traceback
        return f"Config(base_url={self.base_url!r}, model={self.model!r}, auth={self.auth!r})"


def load_config(env: Mapping[str, str] | None = None) -> Config:
    env = os.environ if env is None else env
    missing = [k for k in ("IARA_BASE_URL", "IARA_API_KEY", "IARA_MODEL") if not env.get(k)]
    if missing:
        raise ClientError(f"variáveis de ambiente ausentes: {', '.join(missing)}")
    base_url = env["IARA_BASE_URL"].rstrip("/")
    parsed = urlparse(base_url)
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise ClientError("IARA_BASE_URL precisa ser https (http só para loopback)")
    auth = env.get("REFOLD_AUTH", "x-api-key")
    if auth not in {"x-api-key", "bearer"}:
        raise ClientError("REFOLD_AUTH deve ser `x-api-key` ou `bearer`")
    try:
        max_tokens = int(env.get("REFOLD_MAX_TOKENS", "8192"))
    except ValueError as exc:
        raise ClientError("REFOLD_MAX_TOKENS deve ser inteiro") from exc
    effort = env.get("REFOLD_EFFORT") or None
    if effort not in {None, "low", "medium", "high", "xhigh"}:
        raise ClientError("REFOLD_EFFORT deve ser low, medium, high ou xhigh")
    return Config(
        base_url,
        env["IARA_API_KEY"],
        env["IARA_MODEL"],
        auth,
        max_tokens,
        env.get("REFOLD_PROMPT_CACHE") == "1",
        effort,
    )


def urllib_transport(url: str, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310 (esquema validado em load_config)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, str(exc).encode("utf-8")


class MessagesClient:
    def __init__(
        self,
        config: Config,
        transport: Transport = urllib_transport,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.transport = transport
        self.sleep = sleep

    def _headers(self) -> dict[str, str]:
        headers = {"content-type": "application/json", "anthropic-version": ANTHROPIC_VERSION}
        if self.config.auth == "bearer":
            headers["authorization"] = f"Bearer {self.config.key}"
        else:
            headers["x-api-key"] = self.config.key
        return headers

    def create(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        payload: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": messages,
            "tools": tools,
        }
        if self.config.prompt_cache:
            payload["cache_control"] = {"type": "ephemeral"}
        if self.config.effort:
            payload["output_config"] = {"effort": self.config.effort}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        url = f"{self.config.base_url}/messages"
        status, raw = 0, b""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            status, raw = self.transport(url, self._headers(), body)
            if status == 200:
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ClientError("resposta da API não é JSON") from exc
            if status not in RETRY_STATUS and status != 0:
                break
            if attempt < MAX_ATTEMPTS:
                self.sleep(min(2**attempt, 30))
        detail = _error_text(raw).replace(self.config.key, "***")
        raise ClientError(f"API respondeu {status or 'sem conexão'}: {detail}")


def _error_text(raw: bytes) -> str:
    try:
        payload = json.loads(raw)
        message = payload.get("error", {}).get("message") or str(payload)
    except (json.JSONDecodeError, AttributeError):
        message = raw.decode("utf-8", errors="replace")
    return mask(message[:300])
