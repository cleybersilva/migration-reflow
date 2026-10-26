"""Handler._drain_body — descarte do corpo de POST rejeitado (reflow/dashboard/server.py).

A corrida que este descarte mata está reproduzida de forma determinística no
teste de integração do corpo atrasado (`test_rejected_post_whose_body_arrives_
late_still_gets_its_403`): sem o descarte, 40 de 40 tentativas com 2 ms de
atraso morriam com RST. Aqui se fixa a lógica em si, sem rede, com um handler
montado na mão — o call site é coberto pelo teste de integração com spy.
"""

from __future__ import annotations

import io

import pytest

from dashboard.server import MAX_BODY_BYTES, Handler


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


class FakeConnection:
    """Só o que o descarte toca: `settimeout`, com histórico para conferência."""

    def __init__(self):
        self.timeouts = []

    def settimeout(self, value):
        self.timeouts.append(value)


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


def test_drain_consumes_the_whole_body_of_an_accepted_size():
    handler = handler_for("3000", b"x" * 3000)

    handler._drain_body()

    require(handler.rfile.read() == b"", "O corpo tem que ser consumido por inteiro.")
    require(
        handler.connection.timeouts == [1.0, None],
        f"Timeout curto e restaurado no finally; veio {handler.connection.timeouts}.",
    )
    require(not handler.close_connection, "Corpo drenado deixa a conexão limpa para reutilizar.")


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
        handler.connection.timeouts == [1.0, None],
        "Timeout tem que ser restaurado mesmo quando o corpo nunca chega.",
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
