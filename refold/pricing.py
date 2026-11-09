"""Preço por modelo, em dólar por milhão de tokens, para impor o orçamento da migração.

A tabela cobre os modelos públicos da Anthropic. O preço da IAra não é conhecido aqui: quando
o modelo não está na tabela, ele vem de `REFOLD_PRICE_*`. Sem preço não há orçamento, então
`refold migrate` recusa rodar em vez de fingir que controla o custo.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)
_ENV = ("REFOLD_PRICE_INPUT", "REFOLD_PRICE_OUTPUT")
_CACHE_WRITE_FACTOR = 1.25
_CACHE_READ_FACTOR = 0.1


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float
    cache_write: float

    def cost(self, usage: Mapping[str, int]) -> float:
        return (
            usage.get("input_tokens", 0) * self.input
            + usage.get("output_tokens", 0) * self.output
            + usage.get("cache_read_input_tokens", 0) * self.cache_read
            + usage.get("cache_creation_input_tokens", 0) * self.cache_write
        ) / 1_000_000


PRICES = {
    "claude-fable-5-1": Price(10.0, 50.0, 1.0, 12.5),
    "claude-opus-5-5": Price(4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": Price(2.0, 10.0, 0.20, 2.5),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01, 0.125),
}


def resolve_price(model: str, env: Mapping[str, str] | None = None) -> Price | None:
    """`REFOLD_PRICE_*` vence a tabela: é o preço contratado do endpoint."""
    env = os.environ if env is None else env
    if all(env.get(name) for name in _ENV):
        try:
            prompt, output = float(env[_ENV[0]]), float(env[_ENV[1]])
            read = float(env.get("REFOLD_PRICE_CACHE_READ") or prompt * _CACHE_READ_FACTOR)
            write = float(env.get("REFOLD_PRICE_CACHE_WRITE") or prompt * _CACHE_WRITE_FACTOR)
        except ValueError:
            return None
        return Price(prompt, output, read, write)
    return PRICES.get(model)
