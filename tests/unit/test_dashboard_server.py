"""Handler._drain_body e o prazo de leitura (reflow/dashboard/server.py).

O descarte do corpo tem a corrida de RST reproduzida de forma determinística
no teste de integração do corpo atrasado
(`test_rejected_post_whose_body_arrives_late_still_gets_its_403`): sem ele, 40
de 40 tentativas com 2 ms de atraso morriam com RST. Aqui se fixa a lógica em
si, sem rede, com um handler montado na mão — o call site é coberto pelo
teste de integração com spy.

Este arquivo também fixa a restauração do prazo: o descarte curta o socket
para ler rápido, e se devolvesse `None` (sem prazo) anularia o deadline da
requisição (ADR-024) no meio do caminho.
"""

from __future__ import annotations

import io

import pytest

from dashboard.server import (
    DRAIN_TIMEOUT_SECONDS,
    MAX_BODY_BYTES,
    READ_TIMEOUT_SECONDS,
    Handler,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


class FakeConnection:
    """Só o que o descarte toca: `settimeout`/`gettimeout`, com histórico."""

    def __init__(self, initial=READ_TIMEOUT_SECONDS):
        self.current = initial
        self.timeouts = []

    def settimeout(self, value):
        self.current = value
        self.timeouts.append(value)

    def gettimeout(self):
        return self.current


class StalledReader(io.BytesIO):
    """Simula um cliente que declara corpo e nunca manda (ou manda e some)."""

    def read1(self, size=-1):
        raise TimeoutError("cliente sumiu no meio do corpo")


def handler_for(content_length: str | None, body: bytes = b"", rfile=None) -> Handler:
    """Monta um Handler sem socket: só os atributos que o descarte lê."""
    handler = object.__new__(Handler)
    handler.headers = {} if content_length is None else {"Content-Length": content_length}
    handler.rfile = rfile if rfile is not None else io.BytesIO(body)
    handler.connection = FakeConnection()
    handler.close_connection = False
    return handler


def test_handler_carries_a_read_deadline_on_every_request():
    """O prazo é o hook nativo do stdlib, não timeout improvisado.

    Sem ele o socket fica bloqueante e qualquer conexão que mande só os
    cabeçalhos traz a thread do handler junto para sempre.
    """
    require(
        Handler.timeout == READ_TIMEOUT_SECONDS,
        "Handler.timeout é o que o StreamRequestHandler.setup() aplica ao socket.",
    )
    require(
        READ_TIMEOUT_SECONDS is not None and READ_TIMEOUT_SECONDS > 0,
        "Prazo tem que ser finito e positivo; `None` é o bug de ADR-021.",
    )


def test_drain_consumes_the_whole_body_of_an_accepted_size():
    handler = handler_for("3000", b"x" * 3000)

    handler._drain_body()

    require(handler.rfile.read() == b"", "O corpo tem que ser consumido por inteiro.")
    require(
        handler.connection.timeouts == [DRAIN_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS],
        f"Curta para drenar e devolve o prazo da requisição; veio {handler.connection.timeouts}.",
    )
    require(not handler.close_connection, "Corpo drenado deixa a conexão limpa para reutilizar.")


def test_drain_restores_the_deadline_it_found_not_none():
    """Regreção de ADR-024: `settimeout(None)` anularia o prazo no meio.

    O descarte curta o socket para não esperar corpo de quem nunca vai mandar.
    Se devolvesse `None` em vez do prazo que a requisição já tinha, a leitura
    seguinte (ou a conexão reutilizada) voltaria a ser bloqueante sem prazo —
    exatamente a falha que este ADR fecha.
    """
    handler = handler_for("10", b"z" * 10)
    handler.connection = FakeConnection(initial=READ_TIMEOUT_SECONDS)

    handler._drain_body()

    require(
        handler.connection.current == READ_TIMEOUT_SECONDS,
        f"O prazo da requisição tem que voltar; ficou {handler.connection.current}.",
    )
    require(
        handler.connection.current is not None,
        "Nunca `None`: `None` é socket bloqueante sem deadline (o bug de ADR-021).",
    )


def test_drain_reads_at_most_the_accepted_limit_and_closes():
    handler = handler_for(str(MAX_BODY_BYTES * 4), b"y" * (MAX_BODY_BYTES * 4))

    handler._drain_body()

    consumed = MAX_BODY_BYTES * 4 - len(handler.rfile.read())
    require(
        consumed == MAX_BODY_BYTES,
        f"Só {MAX_BODY_BYTES} bytes são lidos mesmo; veio {consumed}.",
    )
    require(
        handler.close_connection,
        "Corpo maior que o teto deixa byte no socket, então a conexão fecha e nunca reutiliza.",
    )


def test_drain_does_not_hang_when_the_body_never_arrives():
    handler = handler_for("100", rfile=StalledReader(b""))

    handler._drain_body()  # não pode prender a thread do handler

    require(handler.close_connection, "Descarte incompleto fecha a conexão suja.")
    require(
        handler.connection.timeouts == [DRAIN_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS],
        "Prazo restaurado mesmo quando o corpo nunca chega.",
    )
    require(
        handler.connection.current == READ_TIMEOUT_SECONDS,
        "E é o prazo da requisição que volta, não `None`.",
    )


def test_drain_reads_nothing_when_there_is_no_body():
    handler = handler_for(None)

    handler._drain_body()

    require(
        handler.connection.timeouts == [],
        "Sem corpo não há o que drenar e o socket intocado fica.",
    )
    require(not handler.close_connection, "GET/sem corpo não pode marcar a conexão para fechar.")


def test_drain_ignores_a_content_length_that_is_not_a_number():
    handler = handler_for("dez")

    handler._drain_body()

    require(
        handler.connection.timeouts == [],
        "Content-Length inválido não dá corpo a ler; o handler responde 400 e segue.",
    )
