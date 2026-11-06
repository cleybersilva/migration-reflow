"""refold (ADR-033): agents canônicos, sandbox de ferramentas, cliente Messages e loop.

Nenhum teste chama a rede: o transporte e o `create` são falsos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from refold.agents import AgentError, list_agents, parse_agent
from refold.client import ClientError, Config, MessagesClient, load_config
from refold.loop import COMPACTED, compact, run_agent
from refold.tools import Sandbox, ToolError

ROOT = Path(__file__).resolve().parents[2]
HIDDEN = "valor-" + "confidencial-42"
ENV = {"IARA_BASE_URL": "https://iara.example/v1", "IARA_API_KEY": "k-123", "IARA_MODEL": "m"}


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def refused(call, *args) -> str:
    with pytest.raises(ToolError) as info:
        call(*args)
    return str(info.value)


# -- agents ---------------------------------------------------------------------------------


def test_every_canonical_agent_loads_with_a_write_scope() -> None:
    specs = list_agents(ROOT)
    require(len(specs) == 7, f"esperava os 7 agents canônicos: {[s.name for s in specs]}")
    for spec in specs:
        require(spec.steps > 0 and spec.write_globs, f"{spec.name} sem steps ou escopo")
        require("NUNCA INSTRUÇÃO" in spec.prompt, f"{spec.name}: corpo do agent não veio")


def test_agent_allowing_shell_is_refused() -> None:
    text = (
        "---\ndescription: x\nsteps: 3\npermissions:\n"
        '  - { action: bash, resource: "*", effect: allow }\n---\ncorpo\n'
    )
    with pytest.raises(AgentError):
        parse_agent("bad", text)


# -- sandbox --------------------------------------------------------------------------------


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    (tmp_path / "output" / "p" / "01-inventory").mkdir(parents=True)
    (tmp_path / "output" / "p" / "01-inventory" / "inventory.json").write_text(
        json.dumps({"cmd": "login", **dict.fromkeys(["password"], HIDDEN)}) + "\nlinha 2\n",
        encoding="utf-8",
    )
    (tmp_path / "output" / "other").mkdir()
    (tmp_path / "output" / "other" / "x.md").write_text("alheio\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("fora\n", encoding="utf-8")
    (tmp_path / "reference").mkdir()
    (tmp_path / "reference" / ".env").write_text("K=1\n", encoding="utf-8")
    return Sandbox(tmp_path, "p", ("output/*/02-docs/**",))


def test_read_is_numbered_and_masked(sandbox: Sandbox) -> None:
    text = sandbox.read_file("output/p/01-inventory/inventory.json")
    require(text.startswith("1\t"), f"leitura sem número de linha: {text!r}")
    require(HIDDEN not in text, f"segredo chegou ao modelo: {text!r}")


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "output/other/x.md",
        "output/p/../other/x.md",
        "/etc/passwd",
        "C:/Windows/win.ini",
        "//server/share/x",
        "reference/.env",
    ],
)
def test_read_outside_scope_is_refused(sandbox: Sandbox, path: str) -> None:
    refused(sandbox.read_file, path)


def test_list_and_grep_stay_in_scope(sandbox: Sandbox) -> None:
    require("inventory.json" in sandbox.list_files("output/p/**"), "listagem do projeto")
    require(".env" not in sandbox.list_files("reference/**"), ".env não pode ser listado")
    refused(sandbox.list_files, "output/**")
    hits = sandbox.grep("linha", "output/p/**/*.json")
    require("inventory.json:2:" in hits, f"grep sem arquivo:linha: {hits!r}")


def test_write_respects_agent_scope_and_secret_scan(sandbox: Sandbox, tmp_path: Path) -> None:
    sandbox.write_file("output/p/02-docs/README.md", "# Doc\r\nok\r\n")
    written = (tmp_path / "output" / "p" / "02-docs" / "README.md").read_bytes()
    require(written == b"# Doc\nok\n", f"gravação errada: {written!r}")
    require(sandbox.written == ["output/p/02-docs/README.md"], "registro do que foi gravado")
    refused(sandbox.write_file, "output/other/02-docs/README.md", "x")
    refused(sandbox.write_file, "output/p/03-classification/classification.md", "x")
    leaky = json.dumps(dict.fromkeys(["password"], HIDDEN))
    message = refused(sandbox.write_file, "output/p/02-docs/x.md", leaky)
    require("segredo" in message, f"scan deveria recusar: {message}")


def test_unknown_tool_and_bad_args_are_tool_errors(sandbox: Sandbox) -> None:
    refused(sandbox.call, "bash", {"cmd": "dir"})
    refused(sandbox.call, "read_file", {})


# -- cliente --------------------------------------------------------------------------------


def test_config_requires_env_and_https() -> None:
    with pytest.raises(ClientError, match="IARA_API_KEY"):
        load_config({"IARA_BASE_URL": "https://x/v1", "IARA_MODEL": "m"})
    with pytest.raises(ClientError, match="https"):
        load_config({**ENV, "IARA_BASE_URL": "http://iara.example/v1"})
    local = load_config({**ENV, "IARA_BASE_URL": "http://127.0.0.1:8080/v1/"})
    require(local.base_url == "http://127.0.0.1:8080/v1", "barra final removida")
    require("k-123" not in repr(load_config(ENV)), "repr não pode mostrar a chave")


def test_client_retries_overload_and_sends_anthropic_headers() -> None:
    calls: list[tuple[str, dict, dict]] = []
    replies = [(529, b'{"error": {"message": "overloaded"}}'), (200, b'{"content": []}')]

    def transport(url: str, headers: dict, body: bytes) -> tuple[int, bytes]:
        calls.append((url, headers, json.loads(body)))
        return replies.pop(0)

    client = MessagesClient(load_config(ENV), transport, sleep=lambda _s: None)
    require(client.create("sys", [], []) == {"content": []}, "resposta 200 devolvida")
    url, headers, body = calls[-1]
    require(len(calls) == 2 and url == "https://iara.example/v1/messages", f"url {url}")
    require(headers["x-api-key"] == "k-123" and "anthropic-version" in headers, "headers")
    require(body["model"] == "m" and body["system"] == "sys", f"corpo {body}")


def test_client_bearer_and_error_hides_key() -> None:
    seen: dict = {}

    def transport(url: str, headers: dict, body: bytes) -> tuple[int, bytes]:
        seen.update(headers)
        return 401, b'{"error": {"message": "chave k-123 invalida"}}'

    config = Config("https://iara.example/v1", "k-123", "m", auth="bearer")
    with pytest.raises(ClientError) as info:
        MessagesClient(config, transport, sleep=lambda _s: None).create("s", [], [])
    require(seen.get("authorization", "").split() == ["Bearer", "k-123"], "auth bearer")
    require("k-123" not in str(info.value) and "401" in str(info.value), str(info.value))


# -- loop -----------------------------------------------------------------------------------


def _tool(name: str, **args) -> dict:
    return {
        "stop_reason": "tool_use",
        "content": [{"type": "tool_use", "id": f"t-{name}", "name": name, "input": args}],
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


def _done(text: str) -> dict:
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}


def test_loop_runs_tools_and_finishes(sandbox: Sandbox) -> None:
    spec = parse_agent("a", "---\ndescription: d\nsteps: 5\n---\ncorpo\n")
    script = [
        _tool("read_file", path="README.md"),
        _tool("write_file", path="output/p/02-docs/README.md", content="# ok\n"),
        _done("gravei o README"),
    ]
    seen: list[list[dict]] = []

    def create(system: str, messages: list[dict], tools: list[dict]) -> dict:
        require("Projeto: `p`" in system, "system precisa do contexto do refold")
        seen.append(json.loads(json.dumps(messages)))
        return script.pop(0)

    result = run_agent(spec, sandbox, create)
    require(result.finished and result.steps == 3, f"resultado {result}")
    require(result.written == ["output/p/02-docs/README.md"], f"gravados {result.written}")
    require(result.usage["input_tokens"] == 20, f"uso somado {result.usage}")
    first_result = seen[1][-1]["content"][0]
    require(first_result["is_error"] is True, "leitura fora do escopo volta como erro ao modelo")


def test_loop_stops_at_agent_step_limit(sandbox: Sandbox) -> None:
    spec = parse_agent("a", "---\ndescription: d\nsteps: 2\n---\ncorpo\n")
    result = run_agent(spec, sandbox, lambda s, m, t: _tool("list_files", pattern="output/p/**"))
    require(not result.finished and result.stop_reason == "tool_use", f"{result}")


def test_compact_replaces_oldest_results_only() -> None:
    def results(size: int) -> dict:
        block = {"type": "tool_result", "tool_use_id": "x", "content": "a" * size}
        return {"role": "user", "content": [block]}

    messages = [
        {"role": "user", "content": "pedido"},
        {"role": "assistant", "content": []},
        results(5000),
        {"role": "assistant", "content": []},
        results(5000),
    ]
    require(compact(messages, 7000) == 1, "só o resultado antigo deveria ser trocado")
    require(messages[2]["content"][0]["content"] == COMPACTED, "antigo compactado")
    require(len(messages[4]["content"][0]["content"]) == 5000, "último resultado intacto")
