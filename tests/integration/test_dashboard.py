"""Real HTTP/SSE regression tests; fake inference is explicit and isolated."""

from __future__ import annotations

import http.client
import json
import shutil
import threading
import time
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path

import pytest

from dashboard.server import STEPS, Dashboard, create_server

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
