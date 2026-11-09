"""`refold migrate` sem rede: orçamento, checkpoint e piso determinístico, com modelo falso."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.cli import _inputs_fingerprint
from reflow.cli import main as reflow_main
from refold import migrate
from refold.client import Config, MessagesClient
from refold.pricing import PRICES, Price, resolve_price
from tests.classification_support import classification_text, review_text

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "a360-excel-vault"
PRICE_MODEL = "claude-opus-5-5"
TURN = {"input_tokens": 1000, "output_tokens": 500}  # US$ 0,014 no preço do Opus 5.5


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _write(path: str, content: str, usage: dict = TURN) -> dict:
    use = {"type": "tool_use", "id": "1", "name": "write_file"}
    use["input"] = {"path": path, "content": content}
    return {"stop_reason": "tool_use", "content": [use], "usage": usage}


END = {"stop_reason": "end_turn", "content": [{"type": "text", "text": "ok"}], "usage": TURN}


class FakeModel:
    """Identifica o agent pelo prompt e grava o que ele gravaria."""

    def __init__(self, root: Path, optimized: str | None = None, usage: dict = TURN) -> None:
        self.root = root
        self.optimized = optimized
        self.usage = usage
        self.calls: list[str] = []

    def _agent(self, system: str) -> str:
        for marker, agent in (
            ("segunda opinião independente", "cls-review"),
            ("gerado deterministicamente", "optimizer"),
            ("Você audita", "robin-review"),
            ("Você gera o flow de teste", "tester"),
            ("Você classifica", "classifier"),
        ):
            if marker in system:
                return agent
        return "documenter"

    def __call__(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        if len(messages) > 1:
            return END
        agent = self._agent(system)
        self.calls.append(agent)
        out = f"output/{PROJECT}"
        if agent == "documenter":
            return _write(f"{out}/02-docs/use-cases.md", "# Casos de uso\n", self.usage)
        if agent == "classifier":
            return _write(
                f"{out}/03-classification/classification.md",
                classification_text("PARTIAL", "main.json:1", alerts=["A4 (main.json:4)"]),
                self.usage,
            )
        if agent == "cls-review":
            return _write(
                f"{out}/03-classification/review.md",
                review_text("PARTIAL", "PARTIAL", "concorda", "main.json:1"),
                self.usage,
            )
        if agent == "optimizer":
            flow = f"{out}/04-pad/flow-main/Main.robin"
            current = (self.root / flow).read_bytes().decode("utf-8")
            content = (
                self.optimized
                if self.optimized is not None
                else current.replace(
                    "**REGION Chamadas externas", "**REGION Enviar dados ao serviço"
                )
            )
            return _write(flow, content, self.usage)
        if agent == "robin-review":
            return _write(f"{out}/04-pad/flow-main/review.md", "# Revisão\n", self.usage)
        return END


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    for name in ("REFOLD_PRICE_INPUT", "REFOLD_PRICE_OUTPUT"):
        monkeypatch.delenv(name, raising=False)
    shutil.copytree(ROOT / "reference", tmp_path / "reference")
    shutil.copytree(ROOT / ".opencode" / "agents", tmp_path / ".opencode" / "agents")
    shutil.copytree(ROOT / "input" / PROJECT, tmp_path / "input" / PROJECT)
    require(reflow_main(["extract", PROJECT]) == 0, "extract deveria concluir")
    return tmp_path


def _ledger(root: Path) -> dict:
    return json.loads((root / "output" / PROJECT / "cost.json").read_text(encoding="utf-8"))


def _approve(root: Path) -> None:
    path = root / "output" / PROJECT / "00-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["checkpoint"] = {
        "decision": "approved",
        "inputs_fingerprint": _inputs_fingerprint(manifest["inputs"]),
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")


def _run(root: Path, model: FakeModel, budget: float = 1.0) -> int:
    return migrate.run(root, PROJECT, budget, model, PRICE_MODEL)


def test_unknown_price_is_refused_before_any_call(workspace: Path) -> None:
    model = FakeModel(workspace)
    with pytest.raises(migrate.BudgetError, match="desconhecido"):
        migrate.run(workspace, PROJECT, 1.0, model, "modelo-da-iara")
    require(model.calls == [], "sem preço, nenhuma chamada")


def test_stops_at_the_human_checkpoint(workspace: Path) -> None:
    model = FakeModel(workspace)
    require(_run(workspace, model) == 0, "parar no checkpoint não é falha")
    require(model.calls == ["documenter", "classifier", "cls-review"], f"{model.calls}")
    pad = workspace / "output" / PROJECT / "04-pad"
    require(not pad.exists(), "sem aprovação humana, nada é gerado")


def test_full_run_records_cost_and_keeps_the_gate(workspace: Path) -> None:
    model = FakeModel(workspace)
    _run(workspace, model)
    _approve(workspace)
    require(_run(workspace, model) == 0, "depois do checkpoint, segue")
    require(model.calls[3:] == ["optimizer", "robin-review", "tester"], f"{model.calls}")
    robin = workspace / "output" / PROJECT / "04-pad" / "flow-main" / "Main.robin"
    require(b"Enviar dados" in robin.read_bytes(), "otimização válida fica")
    ledger = _ledger(workspace)
    require(0 < ledger["total_usd"] <= 1.0, f"{ledger['total_usd']}")
    statuses = {item["agent"]: item["status"] for item in ledger["stages"]}
    require(statuses["reflow-robin-optimizer"] == "ok", f"{statuses}")


def test_second_run_does_not_pay_twice(workspace: Path) -> None:
    model = FakeModel(workspace)
    _run(workspace, model)
    calls = len(model.calls)
    _run(workspace, model)
    require(len(model.calls) == calls, f"refez estágio já pago: {model.calls}")


def test_rejected_optimization_restores_the_base(workspace: Path) -> None:
    model = FakeModel(workspace, optimized="# passos sumiram\r\n")
    _run(workspace, model)
    _approve(workspace)
    require(_run(workspace, model) == 0, "a migração segue com a base")
    flow = workspace / "output" / PROJECT / "04-pad" / "flow-main"
    require(
        (flow / "Main.robin").read_bytes() == (flow / "Main.generated.robin").read_bytes(),
        "otimização reprovada não pode ficar",
    )
    statuses = {item["agent"]: item["status"] for item in _ledger(workspace)["stages"]}
    require(statuses["reflow-robin-optimizer"] == "descartado", f"{statuses}")


def test_budget_exhausted_keeps_the_deterministic_base(workspace: Path) -> None:
    model = FakeModel(workspace)
    _run(workspace, model)
    _approve(workspace)
    ledger = _ledger(workspace)
    ledger["total_usd"] = 1.0
    (workspace / "output" / PROJECT / "cost.json").write_text(json.dumps(ledger), encoding="utf-8")
    calls = len(model.calls)
    require(_run(workspace, model) == 0, "base determinística ainda vale")
    require(len(model.calls) == calls, f"gastou além do orçamento: {model.calls}")
    flow = workspace / "output" / PROJECT / "04-pad" / "flow-main" / "Main.robin"
    require(flow.is_file(), "a base é gerada sem LLM, mesmo sem saldo")
    statuses = {item["agent"]: item["status"] for item in _ledger(workspace)["stages"]}
    require(statuses["reflow-robin-optimizer"] == "sem orçamento", f"{statuses}")


def test_valid_optimization_survives_a_budget_stop(workspace: Path) -> None:
    model = FakeModel(workspace)
    _run(workspace, model)
    _approve(workspace)
    model.usage = {"input_tokens": 20_000, "output_tokens": 9_000}  # US$ 0,26 num turno
    require(_run(workspace, model) == 0, "a migração segue")
    flow = workspace / "output" / PROJECT / "04-pad" / "flow-main" / "Main.robin"
    require(b"Enviar dados" in flow.read_bytes(), "o flow já pago e aprovado no gate fica")
    statuses = {item["agent"]: item["status"] for item in _ledger(workspace)["stages"]}
    require(statuses["reflow-robin-optimizer"] == "ok", f"{statuses}")


def test_expensive_required_stage_stops_the_migration(workspace: Path) -> None:
    usage = {"input_tokens": 200_000, "output_tokens": 50_000}  # US$ 1,80 num turno
    model = FakeModel(workspace, usage=usage)
    require(_run(workspace, model, 1.0) == 1, "obrigatório incompleto precisa falhar")
    statuses = [item["status"] for item in _ledger(workspace)["stages"]]
    require(statuses and "falhou (budget)" in statuses[0], f"{statuses}")
    require(model.calls == ["documenter"], f"continuou depois de estourar: {model.calls}")


def test_price_math_and_env_override() -> None:
    usage = {
        "input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
        "cache_read_input_tokens": 1_000_000,
        "cache_creation_input_tokens": 1_000_000,
    }
    require(PRICES["claude-opus-5-5"].cost(usage) == pytest.approx(29.2), "preço do Opus 5.5")
    price = resolve_price("qualquer", {"REFOLD_PRICE_INPUT": "1", "REFOLD_PRICE_OUTPUT": "5"})
    require(price == Price(1.0, 5.0, 0.1, 1.25), f"{price}")
    require(resolve_price("qualquer", {}) is None, "sem tabela nem ambiente, sem preço")


def test_cache_and_effort_only_when_enabled() -> None:
    sent: list[dict] = []

    def transport(url: str, headers: dict, body: bytes) -> tuple[int, bytes]:
        sent.append(json.loads(body))
        return 200, b"{}"

    MessagesClient(Config("https://x/v1", "k", "m"), transport).create("s", [], [])
    MessagesClient(
        Config("https://x/v1", "k", "m", prompt_cache=True, effort="low"), transport
    ).create("s", [], [])
    require("cache_control" not in sent[0] and "output_config" not in sent[0], f"{sent[0]}")
    require(sent[1]["cache_control"] == {"type": "ephemeral"}, f"{sent[1]}")
    require(sent[1]["output_config"] == {"effort": "low"}, f"{sent[1]}")
