"""Real HTTP/SSE regression tests; fake inference is explicit and isolated."""

from __future__ import annotations

import http.client
import json
import shutil
import socket
import threading
import time
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path

import pytest

from dashboard.server import READ_TIMEOUT_SECONDS, STEPS, Dashboard, Handler, create_server

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


class FakeRunner:
    def __init__(self, fail=None, hold=False):
        self.fail = fail
        self.entered = threading.Event()
        self.release = threading.Event()
        if not hold:
            self.release.set()

    def projects(self, selection):
        if selection not in {None, "synthetic"}:
            raise ValueError("Projeto inválido.")
        return ["synthetic"]

    def health(self):
        return {"available": True, "model": "synthetic-model", "message": "Somente teste"}

    def execute(self, run_id, project, step, cancel):
        self.entered.set()
        self.release.wait(timeout=3)
        if self.fail == step:
            raise ValueError("não divulgar: " + "ghp_" + "Ab12" * 10)
        return {
            "status": "skipped" if step == "lint" else "completed",
            "detail": f"Fixture: {step}",
        }


@contextmanager
def running_server(tmp_path, runner=None):
    runner = runner or FakeRunner()
    app = Dashboard(tmp_path, runner)
    server = create_server(0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, app, runner
    finally:
        app.cancel.set()
        runner.release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def request(server, path="/api/status", body=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        data = None if body is None else json.dumps(body).encode()
        connection.request("GET" if data is None else "POST", path, data, headers or {})
        response = connection.getresponse()
        return response.status, response.read(), dict(response.getheaders())
    finally:
        connection.close()


def authorized(app):
    return {"Content-Type": "application/json", "X-Reflow-Token": app.csrf}


def stream(server, cursor=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    connection.request(
        "GET", "/api/events", headers={} if cursor is None else {"Last-Event-ID": str(cursor)}
    )
    response = connection.getresponse()
    require(response.status == 200, "SSE deveria responder 200.")
    require("text/event-stream" in response.getheader("Content-Type"), "Content-Type SSE esperado.")
    return connection, response


def frame(response):
    fields = {}
    while True:
        line = response.readline().decode("utf-8").strip()
        if not line and fields:
            return fields
        if line and not line.startswith(":"):
            key, value = line.split(": ", 1)
            fields[key] = value


def finished(app):
    with app.condition:
        require(
            app.condition.wait_for(lambda: not app.state["active"], timeout=4),
            "Teste deveria terminar.",
        )
    return app.snapshot()


def test_open_sse_does_not_block_start_or_assets_and_broadcasts_to_both_clients(tmp_path):
    with running_server(tmp_path, FakeRunner(hold=True)) as (server, app, runner):
        first, first_stream = stream(server)
        second, second_stream = stream(server)
        try:
            require(frame(first_stream)["event"] == "snapshot", "Primeiro cliente recebe snapshot.")
            require(frame(second_stream)["event"] == "snapshot", "Segundo cliente recebe snapshot.")
            require(request(server, "/")[0] == 200, "Página inicial tem que responder.")
            require(request(server, "/app.js")[0] == 200, "Asset app.js tem que responder.")
            status, body, _ = request(server, "/api/run", {"project": "synthetic"}, authorized(app))
            require(
                status == 202 and json.loads(body)["run_id"], "Início do teste tem que aceitar."
            )
            require(runner.entered.wait(timeout=2), "Runner tem que ser chamado de verdade.")
            for response in (first_stream, second_stream):
                event = frame(response)
                require(event["event"] == "update", "Evento de atualização esperado.")
                require(
                    json.loads(event["data"])["snapshot"]["active"], "Snapshot tem que estar ativo."
                )
            require(request(server)[0] == 200, "Status continua respondendo durante a execução.")
            require(
                request(server, "/api/run", {"all": True}, authorized(app))[0] == 409,
                "Segunda execução concorrente tem que ser rejeitada.",
            )
            runner.release.set()
            snapshot = finished(app)
            require(
                snapshot["status"] == "completed", "Teste sem falha tem que terminar completed."
            )
            require(len(snapshot["steps"]) == len(STEPS), "Todas as etapas têm que existir.")
            require(
                sum(step["status"] == "completed" for step in snapshot["steps"]) == 6,
                "6 das 7 etapas concluem (lint fica skipped).",
            )
        finally:
            first.close()
            second.close()


def test_sse_connection_cap_rejects_beyond_the_limit_and_recovers_after_close(tmp_path):
    with running_server(tmp_path) as (server, _app, _runner):
        connections = []
        try:
            for _ in range(Dashboard.MAX_SSE_CLIENTS):
                connection, response = stream(server)
                frame(response)  # consome o snapshot inicial
                connections.append((connection, response))
            status, body, _ = request(server, "/api/events")
            require(status == 429, "Conexão acima do limite tem que ser rejeitada.")
            require("error" in json.loads(body), "Resposta de rejeição tem que ser JSON com erro.")

            connections.pop()[0].close()
            # O servidor só nota a conexão fechada na próxima tentativa de
            # escrita (heartbeat a cada ~2s dentro do loop do SSE) — dar
            # folga generosa em vez de um número exato de tentativas rígido.
            recovered = None
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and recovered is None:
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                connection.request("GET", "/api/events")
                response = connection.getresponse()
                if response.status == 200:
                    recovered = (connection, response)
                    break
                connection.close()
                time.sleep(0.2)
            require(recovered is not None, "Depois de liberar uma conexão, uma nova tem que caber.")
            connections.append(recovered)
        finally:
            for connection, _response in connections:
                connection.close()


def test_failure_is_terminal_and_not_published_as_success_or_with_exception_values(tmp_path):
    with running_server(tmp_path, FakeRunner(fail="document")) as (server, app, _):
        require(
            request(server, "/api/run", {"all": True}, authorized(app))[0] == 202,
            "Início do teste tem que aceitar.",
        )
        result = finished(app)
        require(result["status"] == "error", "Falha numa etapa marca o teste inteiro como error.")
        require(
            any(step["id"] == "document" and step["status"] == "error" for step in result["steps"]),
            "A etapa que falhou tem que aparecer como error.",
        )
        require(
            any(step["status"] == "skipped" for step in result["steps"]),
            "Etapas restantes ficam skipped, nunca completed.",
        )
        require(
            "Ab12" * 10 not in json.dumps(result), "Valor sensível nunca pode vazar para o cliente."
        )


def test_reconnection_replays_events_and_snapshot_without_starting_a_run(tmp_path):
    with running_server(tmp_path) as (server, app, _):
        app.log("info", "Primeiro evento")
        cursor = app.sequence
        app.log("info", "Evento a recuperar")
        connection, response = stream(server, cursor)
        try:
            update = frame(response)
            require(
                update["event"] == "update" and int(update["id"]) > cursor,
                "Reconexão replaya o evento perdido.",
            )
            require(
                frame(response)["event"] == "snapshot", "Reconexão também manda o snapshot atual."
            )
            require(app.snapshot()["run_id"] is None, "Reconectar nunca inicia um teste sozinho.")
        finally:
            connection.close()


def test_invalid_origin_missing_token_bad_selection_and_static_traversal_are_rejected(tmp_path):
    with running_server(tmp_path) as (server, app, _):
        require(
            request(server, "/api/run", {"all": True})[0] == 403, "Sem token tem que ser rejeitado."
        )
        evil = {**authorized(app), "Origin": "https://untrusted.invalid"}
        require(
            request(server, "/api/run", {"all": True}, evil)[0] == 403,
            "Origin não confiável tem que ser rejeitado.",
        )
        require(
            request(server, "/api/run", {"project": "../input"}, authorized(app))[0] == 400,
            "Nome de projeto com traversal tem que ser rejeitado.",
        )
        require(
            request(server, "/api/run", {}, authorized(app))[0] == 400,
            "Corpo sem seleção tem que ser rejeitado.",
        )
        require(
            request(server, "/../.env")[0] == 404,
            "Traversal de asset estático não deve expor arquivo.",
        )
        require(app.snapshot()["run_id"] is None, "Nenhuma dessas tentativas inicia um teste.")


def test_rejected_post_drains_the_body_before_answering(tmp_path):
    """A rejeição tem que consumir o corpo antes de escrever a resposta.

    É o call site que mata a corrida de RST descrita no teste do corpo
    atrasado ao lado: sem este descarte, o Winsock fecha com bytes não lidos
    e derruba a própria resposta. Aqui se fixa o acoplamento (só a rejeição
    drena); a lógica do descarte está no teste unitário correspondente.
    """
    drained: list[str] = []
    original = Handler._drain_body

    def spy(self):
        drained.append(self.path)
        return original(self)

    Handler._drain_body = spy
    try:
        with running_server(tmp_path) as (server, app, _):
            require(
                request(server, "/api/run", {"all": True})[0] == 403,
                "Sem token tem que ser rejeitado.",
            )
            require(
                request(server, "/api/status")[0] == 200,
                "O GET de status continua funcionando durante o spy.",
            )
    finally:
        Handler._drain_body = original
    require(
        drained == ["/api/run"],
        f"Só a rejeição drena o corpo; veio {drained}.",
    )


def test_rejected_post_whose_body_arrives_late_still_gets_its_403(tmp_path):
    """Regressão do flake: rejeição com corpo que chega em seguida não aborta.

    O `http.client` manda cabeçalho e corpo em **dois `send()`**. Se o corpo
    chega depois de o handler já ter lido os cabeçalhos, o handler rejeitava,
    escrevia o 403 e fechava sem nunca ter lido o corpo — e o envio do corpo
    batia em socket fechado, fazendo o Winsock responder **RST**, que destrói
    o 403 que estava no buffer de recepção do cliente. O cliente via
    `ConnectionAbortedError` no lugar da rejeição esperada: era o flake de
    `test_invalid_origin_...`, que só aparecia sob carga porque a carga é o
    que atrasa o corpo.

    Medido antes do fix, sem sorte nenhuma no sorteio: com 2 ms de atraso o
    resultado era **RST em 40 de 40** tentativas; com o descarte do corpo, o
    handler passa a esperar o corpo (até 1 s) e fecha com FIN — 40 de 40.
    """
    with running_server(tmp_path) as (server, app, _):
        body = json.dumps({"all": True}).encode()
        connection = socket.create_connection(("127.0.0.1", server.server_port), timeout=3)
        try:
            connection.sendall(
                b"POST /api/run HTTP/1.1\r\n"
                b"Host: 127.0.0.1:" + str(server.server_port).encode() + b"\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"Connection: close\r\n"
                b"\r\n"
            )
            time.sleep(0.010)  # cabeçalho processado; corpo só chega agora
            connection.sendall(body)
            received = b""
            try:
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    received += chunk
            except (ConnectionAbortedError, ConnectionResetError):
                pytest.fail(
                    "RST no meio da resposta: a rejeição respondeu e fechou "
                    "sem consumir o corpo que estava a caminho."
                )
        finally:
            connection.close()
        require(
            received.split(b"\r\n", 1)[0].endswith(b" 403 Forbidden"),
            f"Corpo atrasado não pode custar a resposta; veio: {received[:40]!r}.",
        )
        require(
            "Requisição não autorizada" in received.decode("utf-8"),
            "O 403 tem que chegar inteiro, não só o status.",
        )
        require(app.snapshot()["run_id"] is None, "Rejeição nunca inicia um teste.")


def test_rejected_post_is_answered_and_closed_with_fin_not_rst(tmp_path):
    """A rejeição tem que devolver o 403 inteiro e fechar com FIN.

    Confirma, no caminho real de socket, o resultado do descarte do corpo: o
    403 chega inteiro e o fechamento é FIN (`b""` no `recv`), não RST. A
    corrida que isso evita — e que a lógica do descarte mata — está fixada
    deterministicamente no teste do corpo atrasado ao lado; a lógica em si
    está no teste unitário correspondente.
    """
    with running_server(tmp_path) as (server, app, _):
        body = json.dumps({"all": True}).encode()
        connection = socket.create_connection(("127.0.0.1", server.server_port), timeout=3)
        try:
            connection.sendall(
                b"POST /api/run HTTP/1.1\r\n"
                b"Host: 127.0.0.1:" + str(server.server_port).encode() + b"\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"Connection: close\r\n"
                b"\r\n" + body
            )
            received = b""
            while b"\r\n\r\n" not in received:
                received += connection.recv(4096)
            status_line = received.split(b"\r\n", 1)[0]
            require(
                status_line.endswith(b" 403 Forbidden"),
                f"Resposta de rejeição esperada, veio: {received[:40]!r}.",
            )
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break  # FIN: fechamento gracioso, sem RST.
                received += chunk
        except ConnectionResetError:
            pytest.fail("RST no fechamento: a rejeição respondeu sem consumir o corpo.")
        finally:
            connection.close()
        require(
            "Requisição não autorizada" in received.decode("utf-8"),
            "O corpo do 403 tem que chegar inteiro, não só o status.",
        )
        require(app.snapshot()["run_id"] is None, "Rejeição nunca inicia um teste.")


def test_post_body_that_never_arrives_gets_408_not_a_hung_thread(tmp_path, monkeypatch):
    """Regressão de ADR-024: corpo que nunca chega não pode prender a thread.

    `Content-Length: 32` com a linha de requisição e os cabeçalhos enviados e
    **nenhum byte de corpo**: sem prazo de leitura, o `self.rfile.read(length)`
    do `do_POST` ficaria bloqueando para sempre e a thread do handler morreria
    presa na conexão — cada conexão dessas vaza uma thread, até derrubar o
    dashboard. Com o prazo, o handler responde 408 e **fecha a conexão** (recv
    devolvendo `b""`): fechar é o que prova que a thread foi liberada, já que
    o `ThreadingHTTPServer` atende conexão seguinte em thread nova mesmo com a
    antiga ainda presa.

    Medido com o `server.py` anterior, o prazo já podia existir no socket e o
    teste ainda falhava: o `TimeoutError` caía no `except (ValueError, OSError)`
    do `do_POST`, que respondia **400 "Seleção ou corpo inválido"** mentindo
    sobre o que houve. Fixa-se aqui o 408 e a drenagem que evita o RST.

    O prazo é encurtado por aqui só para o teste não esperar 10 s; o mecanismo
    é o mesmo.
    """
    monkeypatch.setattr(Handler, "timeout", 0.3)
    with running_server(tmp_path) as (server, app, _):
        connection = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
        try:
            connection.sendall(
                b"POST /api/run HTTP/1.1\r\n"
                b"Host: 127.0.0.1:" + str(server.server_port).encode() + b"\r\n"
                b"Content-Type: application/json\r\n"
                b"X-Reflow-Token: " + app.csrf.encode() + b"\r\n"
                b"Content-Length: 32\r\n"
                b"Connection: close\r\n"
                b"\r\n"
            )
            received = b""
            try:
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    received += chunk
            except ConnectionResetError:
                pytest.fail(
                    "RST antes do 408: o handler fechou com o corpo parcial "
                    "no buffer em vez de drenar e responder."
                )
        finally:
            connection.close()
        require(
            received.split(b"\r\n", 1)[0].endswith(b" 408 Request Timeout"),
            f"Corpo que nunca chega tem que virar 408; veio: {received[:60]!r}.",
        )
        require(
            b"recebido no prazo" in received,
            f"O 408 tem que explicar o que houve; veio: {received[:200]!r}.",
        )
        require(
            request(server, "/api/status")[0] == 200,
            "O servidor tem que continuar de pé depois de perder uma conexão travada.",
        )
        require(app.snapshot()["run_id"] is None, "Corpo incompleto nunca inicia um teste.")


def test_idle_connection_is_dropped_by_the_read_deadline(tmp_path, monkeypatch):
    """Conexão que nem manda a linha de requisição tem que morrer sozinha.

    O outro lado do mesmo prazo do ADR-024: um cliente que conecta e nunca
    escreve nada bloquearia o `self.rfile.readline()` do `handle_one_request`
    para sempre. O stdlib já trata esse `TimeoutError` fechando a conexão sem
    traceback — falta só existir prazo.

    Por isso o `require` vem **antes** do `monkeypatch`: encurtar o prazo aqui
    criaria o próprio atributo `timeout` que o stdlib lê, e o teste passaria
    mesmo sem o fix (foi o que aconteceu na primeira versão). Fixa-se que o
    prazo está ligado de fábrica, e só depois se encurta o socket para não
    esperar 10 s. O `recv` client-side devolve `b""` (FIN); se o servidor nunca
    fechar, o timeout do teste derruba o assert em vez de pendurar a suíte.
    """
    require(
        Handler.timeout == READ_TIMEOUT_SECONDS and READ_TIMEOUT_SECONDS > 0,
        f"O prazo tem que estar ligado de fábrica no Handler; veio {Handler.timeout}.",
    )
    monkeypatch.setattr(Handler, "timeout", 0.3)
    with running_server(tmp_path) as (server, app, _):
        connection = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
        try:
            require(
                connection.recv(4096) == b"",
                "Conexão ociosa tem que ser fechada pelo prazo, sem resposta alguma.",
            )
        finally:
            connection.close()
        require(
            request(server, "/api/status")[0] == 200,
            "O servidor tem que continuar de pé depois de descartar conexão ociosa.",
        )


def test_cancel_only_targets_the_current_run(tmp_path):
    with running_server(tmp_path, FakeRunner(hold=True)) as (server, app, runner):
        request(server, "/api/run", {"all": True}, authorized(app))
        require(
            request(server, "/api/cancel", {"run_id": "old"}, authorized(app))[0] == 409,
            "Cancelar run_id antigo/errado tem que ser rejeitado.",
        )
        require(
            request(server, "/api/cancel", {"run_id": app.snapshot()["run_id"]}, authorized(app))[0]
            == 202,
            "Cancelar o run_id atual tem que ser aceito.",
        )
        runner.release.set()
        require(
            finished(app)["status"] == "cancelled", "Teste cancelado tem que terminar cancelled."
        )


class MarkupCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.ids = []
        self.external = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag in {"script", "link", "img"}:
            self.external.append(attrs.get("src") or attrs.get("href") or "")
        if tag not in {"meta", "link", "br", "img", "input", "hr"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        require(bool(self.stack) and self.stack.pop() == tag, f"Fechamento HTML inválido: {tag}")


def test_html_is_well_formed_offline_and_contains_javascript_targets():
    parser = MarkupCheck()
    parser.feed((ROOT / "dashboard/index.html").read_text("utf-8"))
    require(not parser.stack, "Toda tag aberta tem que ser fechada.")
    require(len(parser.ids) == len(set(parser.ids)), "Nenhum id duplicado no HTML.")
    require(
        {
            "run-btn",
            "steps-container",
            "logs-container",
            "project-select",
            "progress-fill",
        }
        <= set(parser.ids),
        "Ids que app.js espera têm que existir no HTML.",
    )
    require(not any(url.startswith("http") for url in parser.external), "Nenhum asset remoto/CDN.")
    css = (ROOT / "dashboard/style.css").read_text("utf-8")
    require(
        "prefers-reduced-motion" in css and "@keyframes spin" in css,
        "CSS tem que respeitar prefers-reduced-motion e ter a animação esperada.",
    )


def test_runner_isolates_artifacts_and_never_rewrites_official_output(tmp_path):
    from dashboard.pipeline import DashboardRunner

    source = ROOT / "tests/fixtures/a360/browser-rest"
    shutil.copytree(source, tmp_path / "input/synthetic")
    (tmp_path / "reference").mkdir()
    shutil.copy(ROOT / "reference/classification-rubric.md", tmp_path / "reference")
    official = tmp_path / "output/synthetic/00-manifest.json"
    official.parent.mkdir(parents=True)
    official.write_text('{"sentinel":"preserve"}', encoding="utf-8")
    before = official.read_bytes()
    runner = DashboardRunner(tmp_path)

    def inference_fixture(mode, payload=None, cancel=None, hint=None):
        require(mode in {"Document", "Classify"}, "Modo tem que ser Document ou Classify.")
        require(
            bool(payload["inventory"]) and bool(payload["evidence_catalog"]),
            "Payload tem que trazer inventário e catálogo de evidência.",
        )
        require(hint is None, "Primeira tentativa não tem dica de retry.")
        return {
            "summary": "Resumo sintético suficientemente longo.",
            "reason": "Justificativa sintética suficientemente longa.",
            "verdict": "PAD",
            "evidence": payload["evidence_catalog"][:1],
        }

    runner._worker = inference_fixture
    cancel = threading.Event()
    for step in ("extract", "document", "classify", "security", "report"):
        require(bool(runner.execute("synthetic-run", "synthetic", step, cancel)["detail"]), step)
    require(
        runner.execute("synthetic-run", "synthetic", "lint", cancel)["status"] == "skipped",
        "Lint é não aplicável neste teste.",
    )
    require(official.read_bytes() == before, "output/ real nunca é tocado pelo dashboard.")
    folder = tmp_path / ".dashboard-runs/synthetic-run/synthetic"
    require(
        (folder / "preview-classify.json").is_file(), "Prévia de classificação tem que ser salva."
    )
    report = json.loads((folder / "test-report.json").read_text("utf-8"))
    require(
        report["pad_executed"] is False and report["migration_completed"] is False,
        "Relatório nunca pode fingir migração/execução real.",
    )


def test_inference_retries_once_and_normalizes_cited_evidence(tmp_path, monkeypatch):
    from dashboard import pipeline as pipeline_module
    from dashboard.pipeline import DashboardRunner

    shutil.copytree(ROOT / "tests/fixtures/a360/browser-rest", tmp_path / "input/synthetic")
    (tmp_path / "reference").mkdir()
    shutil.copy(ROOT / "reference/classification-rubric.md", tmp_path / "reference")
    runner = DashboardRunner(tmp_path)
    cancel = threading.Event()
    require(bool(runner.execute("retry-run", "synthetic", "extract", cancel)["detail"]), "extract")

    calls = []
    expected = {}

    def flaky_inference(mode, payload=None, cancel=None, hint=None):
        calls.append(mode)
        fact = payload["evidence_catalog"][0]
        expected.update(fact)
        if len(calls) == 1:
            return {"summary": "Resumo sintético sem evidência.", "evidence": []}
        require(hint == "retry_evidence", "Segunda tentativa tem que vir com a dica certa.")
        return {
            "summary": "Resumo sintético com uma frase completa.",
            "evidence": [{"file": "./" + fact["file"], "line": str(fact["line"])}],
        }

    runner._worker = flaky_inference
    monkeypatch.setattr(pipeline_module.time, "sleep", lambda _seconds: None)
    detail = runner.execute("retry-run", "synthetic", "document", cancel)["detail"]
    require(len(calls) == 2, "Deveria ter tentado exatamente duas vezes.")
    require("Prévia recebida" in detail, "Resumo de sucesso tem que mencionar a prévia.")
    preview = json.loads(
        (tmp_path / ".dashboard-runs/retry-run/synthetic/preview-document.json").read_text("utf-8")
    )
    require(preview["evidence"][0]["line"] == expected["line"], "Linha normalizada tem que bater.")
    require(
        "\\" not in preview["evidence"][0]["file"],
        "Caminho normalizado usa barra, nunca contrabarra.",
    )

    calls.clear()

    def always_invalid(mode, payload=None, cancel=None, hint=None):
        calls.append(mode)
        return {"summary": "Resumo sem evidência suficiente", "evidence": []}

    runner._worker = always_invalid
    with pytest.raises(ValueError, match="duas tentativas"):
        runner.execute("retry-run", "synthetic", "document", cancel)
    require(len(calls) == 2, "Duas tentativas, nunca mais que isso.")
    failure = json.loads(
        (tmp_path / ".dashboard-runs/retry-run/synthetic/failure-document.json").read_text("utf-8")
    )
    require(failure["step"] == "document", "Falha registrada tem que citar a etapa certa.")
    require(
        failure["attempts"][0]["reason"] == "Evidência obrigatória ausente.",
        "Motivo da primeira falha tem que ser preciso.",
    )
    require(
        failure["attempts"][0]["retry_hint"] == "retry_evidence",
        "Dica de retry tem que corresponder ao motivo.",
    )
    require(
        "Resumo sem evidência" not in json.dumps(failure),
        "Texto bruto do modelo nunca pode ir para o relatório de falha.",
    )
