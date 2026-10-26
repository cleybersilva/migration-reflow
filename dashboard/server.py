"""Loopback-only threaded dashboard with replayable SSE and isolated local tests."""

from __future__ import annotations

import argparse
import json
import secrets
import socket
import sys
import threading
import time
import uuid
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.pipeline import DashboardRunner  # noqa: E402
from reflow.security.masking import mask_data  # noqa: E402

STEPS = (
    ("ollama_check", "Ollama local", "Disponibilidade do modelo"),
    ("extract", "Extração", "Análise determinística isolada"),
    ("document", "Documentação", "Prévia textual do LLM"),
    ("classify", "Classificação", "Sugestão sujeita a revisão"),
    ("security", "Segurança", "Scan das saídas do teste"),
    ("lint", "Robin", "Gate estático, se houver flow"),
    ("report", "Relatório", "Resultados deste teste"),
)

# Corpo máximo de um POST: o dashboard só recebe seleção de projeto, então o
# teto é minúsculo de propósito. Usado tanto na validação quanto no descarte
# do corpo de requisições rejeitadas (Handler._drain_body).
MAX_BODY_BYTES = 4096


class Dashboard:
    # Teste local de um usuário só: uma aba normal mantém 1 SSE (2 durante um
    # reconnect). O teto existe para um script/aba perdida não acumular
    # threads sem limite — não é defesa contra um atacante com acesso
    # loopback, que já teria controle do processo de qualquer forma.
    MAX_SSE_CLIENTS = 6

    def __init__(self, root: Path = ROOT, runner: DashboardRunner | None = None) -> None:
        self.root = root
        self.runner = runner or DashboardRunner(root)
        self.condition = threading.Condition()
        self.events: deque = deque(maxlen=500)
        self.sequence = 0
        self.csrf = secrets.token_urlsafe(32)
        self.cancel = threading.Event()
        self.sse_clients = 0
        self.state: dict = {
            "run_id": None,
            "status": "idle",
            "active": False,
            "projects": [],
            "steps": [],
            "logs": [],
            "started_at": None,
            "finished_at": None,
        }

    def snapshot(self) -> dict:
        with self.condition:
            return {**json.loads(json.dumps(self.state)), "revision": self.sequence}

    def emit(self, kind: str, **data) -> None:
        with self.condition:
            safe = mask_data(data)
            self.sequence += 1
            self.events.append((self.sequence, kind, safe))
            self.condition.notify_all()

    def log(self, level: str, message, project: str | None = None) -> None:
        with self.condition:
            entry = mask_data(
                {"level": level, "message": message, "project": project, "time": time.time()}
            )
            self.state["logs"] = (self.state["logs"] + [entry])[-150:]
            self.emit("update", snapshot=self.snapshot())

    def step(self, project: str, step: str, status: str, detail: str) -> None:
        with self.condition:
            item = next(
                s for s in self.state["steps"] if s["project"] == project and s["id"] == step
            )
            item.update(status=status, detail=detail)
            self.log("error" if status == "error" else "info", detail, project)

    def start(self, selection: str | None) -> str | None:
        projects = self.runner.projects(selection)
        if not projects:
            raise ValueError("Nenhum projeto disponível para o teste.")
        with self.condition:
            if self.state["active"]:
                return None
            run_id = uuid.uuid4().hex
            self.cancel.clear()
            self.state = {
                "run_id": run_id,
                "status": "running",
                "active": True,
                "projects": projects,
                "started_at": time.time(),
                "finished_at": None,
                "logs": [],
                "steps": [
                    {
                        "project": project,
                        "id": key,
                        "label": label,
                        "description": description,
                        "status": "pending",
                        "detail": "Aguardando",
                    }
                    for project in projects
                    for key, label, description in STEPS
                ],
            }
            self.log(
                "info", "Teste iniciado em área isolada; os flows existentes não serão alterados."
            )
            threading.Thread(target=self._run, args=(run_id, projects), daemon=True).start()
            return run_id

    def _run(self, run_id: str, projects: list[str]) -> None:
        failed = False
        try:
            for project in projects:
                if self.cancel.is_set():
                    break
                for key, label, _ in STEPS:
                    if self.cancel.is_set():
                        break
                    self.step(project, key, "running", f"{label}: executando…")
                    try:
                        result = self.runner.execute(run_id, project, key, self.cancel)
                        if self.cancel.is_set():
                            break
                        self.step(project, key, result.get("status", "completed"), result["detail"])
                    except Exception:
                        if self.cancel.is_set():
                            break
                        failed = True
                        self.step(
                            project,
                            key,
                            "error",
                            f"{label}: falhou. Confira modelo, tempo limite e dados do teste.",
                        )
                        # Do not expose exception values, prompts or stderr to the browser.
                        break
        except Exception:
            failed = True
            self.log("error", "Falha interna no teste; conclusão bloqueada.")
        finally:
            with self.condition:
                for item in self.state["steps"]:
                    if item["status"] in {"pending", "running"}:
                        item.update(status="skipped", detail="Não executado nesta tentativa")
                status = "cancelled" if self.cancel.is_set() else "error" if failed else "completed"
                self.state.update(status=status, active=False, finished_at=time.time())
                self.log(
                    "error" if failed else "info",
                    {
                        "completed": "Teste encerrado. Revise as sugestões; PAD não executado.",
                        "error": "Teste com erro. Nenhuma aprovação ou migração registrada.",
                        "cancelled": "Teste cancelado; etapas restantes não foram executadas.",
                    }[status],
                )


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        return

    @property
    def app(self) -> Dashboard:
        return self.server.app

    def _valid_host(self) -> bool:
        return self.headers.get("Host") in {
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        }

    def _headers(self, status, content_type, length=None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; "
            "style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        )
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()

    def _json(self, status, data) -> None:
        content = json.dumps(mask_data(data), ensure_ascii=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(content))
        self.wfile.write(content)

    def _drain_body(self) -> None:
        """Descarta o corpo de uma requisição que vai ser rejeitada.

        O `http.client` manda cabeçalho e corpo em **dois `send()`**. Se o
        corpo chega depois de o handler já ter lido os cabeçalhos, ele
        rejeitava, escrevia a resposta e fechava sem nunca ter lido o corpo:
        o Winsock responde **RST** a um envio que bate em socket fechado, e o
        RST destrói a resposta que estava no buffer de recepção do cliente —
        o cliente via `ConnectionAbortedError` no lugar do 403, e o próprio
        servidor via WinError 10053 no `wfile.write`. Consumir o corpo antes
        de responder transforma essa corrida, que só aparecia sob carga, em
        FIN limpo.

        O teto é o mesmo do corpo aceito e o timeout é curto de propósito: um
        `Content-Length` mentiroso não pode prender a thread do handler. Isso
        **não** resolve a pendência do `POST` sem deadline de leitura (ADR-021)
        — só evita repetir, nesta leitura nova, a mesma fraqueza. Quando o
        corpo declarado passa do teto, sobra byte no socket mesmo depois do
        descarte e a conexão é marcada para fechar, nunca reutilizar.
        """
        try:
            declared = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return
        if declared <= 0:
            return
        if declared > MAX_BODY_BYTES:
            self.close_connection = True
        remaining = min(declared, MAX_BODY_BYTES)
        try:
            self.connection.settimeout(1.0)
            while remaining > 0:
                chunk = self.rfile.read1(remaining)
                if not chunk:
                    self.close_connection = True
                    return
                remaining -= len(chunk)
        except (TimeoutError, OSError):
            self.close_connection = True
        finally:
            self.connection.settimeout(None)

    def do_GET(self) -> None:  # noqa: N802
        if not self._valid_host():
            self._json(HTTPStatus.FORBIDDEN, {"error": "Host não autorizado."})
            return
        path = urlsplit(self.path).path
        assets = {
            "/": ("index.html", "text/html"),
            "/index.html": ("index.html", "text/html"),
            "/app.js": ("app.js", "application/javascript"),
            "/style.css": ("style.css", "text/css"),
            "/favicon.svg": ("favicon.svg", "image/svg+xml"),
        }
        if path in assets:
            name, media = assets[path]
            content = (Path(__file__).parent / name).read_bytes()
            self._headers(HTTPStatus.OK, media + "; charset=utf-8", len(content))
            self.wfile.write(content)
        elif path == "/api/status":
            self._json(
                HTTPStatus.OK,
                {
                    "server": "reflow-dashboard",
                    "version": 1,
                    "csrf": self.app.csrf,
                    "snapshot": self.app.snapshot(),
                    "projects": self.app.runner.projects(None),
                    "ollama": self.app.runner.health(),
                },
            )
        elif path == "/api/events":
            self._events()
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin")
        if (
            not self._valid_host()
            or origin not in {None, f"http://{self.headers.get('Host')}"}
            or not secrets.compare_digest(self.headers.get("X-Reflow-Token", ""), self.app.csrf)
        ):
            self._drain_body()
            self._json(
                HTTPStatus.FORBIDDEN, {"error": "Requisição não autorizada. Recarregue o painel."}
            )
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if (
                not 0 < length <= MAX_BODY_BYTES
                or self.headers.get("Content-Type") != "application/json"
            ):
                self._drain_body()
                raise ValueError("Corpo inválido.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Objeto esperado.")
            if self.path == "/api/run":
                if payload.get("all") is True and not payload.get("project"):
                    selection = None
                elif isinstance(payload.get("project"), str) and not payload.get("all"):
                    selection = payload["project"]
                else:
                    raise ValueError("Selecione projeto ou lote.")
                run_id = self.app.start(selection)
                self._json(
                    HTTPStatus.ACCEPTED if run_id else HTTPStatus.CONFLICT,
                    {"run_id": run_id, "error": None if run_id else "Já há um teste em execução."},
                )
            elif self.path == "/api/cancel":
                if payload.get("run_id") != self.app.snapshot()["run_id"]:
                    self._json(
                        HTTPStatus.CONFLICT, {"error": "O teste mudou; recarregue o estado."}
                    )
                    return
                self.app.cancel.set()
                self._json(HTTPStatus.ACCEPTED, {"message": "Cancelamento solicitado."})
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})
        except (ValueError, OSError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Seleção ou corpo inválido."})

    def _events(self) -> None:
        with self.app.condition:
            if self.app.sse_clients >= Dashboard.MAX_SSE_CLIENTS:
                over_limit = True
            else:
                self.app.sse_clients += 1
                over_limit = False
        if over_limit:
            self._json(
                HTTPStatus.TOO_MANY_REQUESTS,
                {"error": "Muitas conexões abertas; recarregue a página."},
            )
            return
        try:
            self.connection.settimeout(10)
            self._headers(HTTPStatus.OK, "text/event-stream; charset=utf-8")
            try:
                cursor = int(self.headers.get("Last-Event-ID", "0"))
            except ValueError:
                cursor = 0
            try:
                # Each client has its own cursor: clients do not consume one shared queue.
                with self.app.condition:
                    current = self.app.sequence
                    backlog = [item for item in self.app.events if cursor < item[0] <= current]
                    snapshot = self.app.snapshot()
                if cursor and backlog:
                    for number, kind, data in backlog:
                        self._send_event(number, kind, data)
                self._send_event(current, "snapshot", {"snapshot": snapshot})
                cursor = current
                while True:
                    with self.app.condition:
                        available = [item for item in self.app.events if item[0] > cursor]
                        if not available:
                            self.app.condition.wait(timeout=2)
                            available = [item for item in self.app.events if item[0] > cursor]
                    for number, kind, data in available:
                        self._send_event(number, kind, data)
                        cursor = number
                    if not available:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
                return
        finally:
            with self.app.condition:
                self.app.sse_clients -= 1

    def _send_event(self, number: int, kind: str, data: dict) -> None:
        frame = f"id: {number}\nevent: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(frame.encode("utf-8"))
        self.wfile.flush()


def create_server(port: int = 8765, app: Dashboard | None = None) -> DashboardServer:
    server = DashboardServer(("127.0.0.1", port), Handler)
    server.app = app or Dashboard()
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Dashboard local do reflow (somente loopback).")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--model",
        default="llama3.1:8b",
        help="Modelo Ollama já baixado (ver `ollama list`). Padrão: llama3.1:8b.",
    )
    args = parser.parse_args()
    try:
        app = Dashboard(ROOT, DashboardRunner(ROOT, model=args.model))
        server = create_server(args.port, app)
    except OSError:
        print(
            "Não foi possível abrir a porta. Já há um servidor? Não encerre todos os processos.",
            flush=True,
        )
        raise SystemExit(1) from None
    print(
        f"Reflow Dashboard: http://127.0.0.1:{server.server_port} (modelo: {args.model})",
        flush=True,
    )
    print("Abra o endereço HTTP, não o arquivo HTML. Ctrl+C encerra este servidor.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.app.cancel.set()
        server.server_close()


if __name__ == "__main__":
    main()
