"""Gerador determinístico e gate do otimizador, sobre as fixtures sintéticas."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.cli import main as reflow_main
from reflow.context_pack import build_pack
from reflow.report import build_batch_report
from reflow.robin import lint_robin_files
from reflow.robin.generate import BASE_NAME, build_flows
from reflow.robin.optimize import check_project, restore_base
from reflow.robin.whitelist import load_whitelist

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ("a360-excel-vault", "a360-browser-rest", "quote-scraper")
CLASSIFICATION = "---\nverdict: PARTIAL\n---\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _approve(root: Path, project: str, verdict: str = "PARTIAL") -> None:
    """Grava o checkpoint como a CLI grava, sem passar pelo gate da classificação."""
    out = root / "output" / project
    (out / "03-classification").mkdir(exist_ok=True)
    (out / "03-classification" / "classification.md").write_text(
        CLASSIFICATION.replace("PARTIAL", verdict), encoding="utf-8"
    )
    path = out / "00-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    from reflow.cli import _inputs_fingerprint  # noqa: PLC0415

    manifest["checkpoint"] = {
        "decision": "approved",
        "inputs_fingerprint": _inputs_fingerprint(manifest["inputs"]),
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    shutil.copytree(ROOT / "reference", tmp_path / "reference")
    for project in PROJECTS:
        shutil.copytree(ROOT / "input" / project, tmp_path / "input" / project)
        require(reflow_main(["extract", project]) == 0, f"extract de {project}")
    return tmp_path


def _robin(root: Path, project: str, flow: str = "flow-main") -> Path:
    return root / "output" / project / "04-pad" / flow / "Main.robin"


def _rewrite(path: Path, old: str, new: str) -> None:
    text = path.read_bytes().decode("utf-8")
    require(old in text, f"trecho ausente: {old}")
    path.write_bytes(text.replace(old, new).encode("utf-8"))


def test_generate_requires_approved_checkpoint(workspace: Path) -> None:
    require(reflow_main(["generate", PROJECTS[0]]) == 1, "sem checkpoint, não gera")
    require(not (workspace / "output" / PROJECTS[0] / "04-pad").exists(), "nada gravado")


def test_generate_refuses_not_pad(workspace: Path) -> None:
    _approve(workspace, PROJECTS[0], "NOT_PAD")
    require(reflow_main(["generate", PROJECTS[0]]) == 1, "NOT_PAD não tem conversão")


def test_generate_refuses_changed_input(workspace: Path) -> None:
    project = PROJECTS[0]
    _approve(workspace, project)
    (workspace / "input" / project / "novo.txt").write_text("x", encoding="utf-8")
    require(reflow_main(["generate", project]) == 1, "input mudou depois do extract")


@pytest.mark.parametrize("project", PROJECTS)
def test_generated_flow_passes_the_lint_and_is_byte_stable(workspace: Path, project: str) -> None:
    _approve(workspace, project)
    require(reflow_main(["generate", project]) == 0, "generate deveria concluir")
    pad = workspace / "output" / project / "04-pad"
    first = {path: path.read_bytes() for path in sorted(pad.rglob("*")) if path.is_file()}
    require(lint_robin_files(workspace, project) == [], "a base precisa passar no lint")
    require(reflow_main(["generate", project]) == 0, "gerar de novo sem mudança é permitido")
    second = {path: path.read_bytes() for path in sorted(pad.rglob("*")) if path.is_file()}
    require(first == second, "mesma entrada precisa gerar os mesmos bytes")
    require(check_project(workspace, project) == [], "a base passa no próprio gate")


def test_only_whitelisted_actions_and_no_invented_values(workspace: Path) -> None:
    project = "a360-excel-vault"
    inventory = json.loads(
        (workspace / "output" / project / "01-inventory" / "inventory.json").read_text("utf-8")
    )
    whitelist = load_whitelist(workspace)
    flows, _ = build_flows(workspace, inventory)
    used = [step for flow in flows for step in flow.steps if step.action]
    require(used, "alguma ação precisa sair da tabela verdade")
    require(all(step.action in whitelist for step in used), "ação fora da whitelist")
    require(
        all(value == "$''''''" or value.isdigit() for flow in flows for _, value in flow.configs),
        "texto de configuração sempre vazio: o inventário não guarda valores",
    )
    robin = "\n".join(step.line or "" for flow in flows for step in flow.steps)
    require("example" not in robin.lower() and "KB Test" not in robin, "valor de exemplo vazou")


def test_unknown_credential_and_ui_become_todo_with_evidence(workspace: Path) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    require(reflow_main(["generate", project]) == 0, "generate deveria concluir")
    text = _robin(workspace, project).read_bytes().decode("utf-8")
    require("CustomPackage.transform (main.json:5)" in text, "comando desconhecido sem evidência")
    require("Subfluxo comum: Obter credencial" in text, "credencial catalogada sem sinalização")
    require("segredo nunca literal" in text, "atributo authorization sem aviso de segredo")


def test_malicious_legacy_names_do_not_reach_the_flow(workspace: Path) -> None:
    inventory = {
        "source_type": "a360",
        "dependencies": [
            {
                "packageName": "TaskBot",
                "commandName": "run\nSET x TO 1",
                "file": "a.json",
                "line": 1,
                "target": "bot; DELETE.json",
                "attribute_names": ["x\ny"],
            }
        ],
        "unknown_commands": [
            {"packageName": "Pkg\nEvil", "commandName": "Do", "file": "a\n.json", "line": 2}
        ],
    }
    flows, _ = build_flows(workspace, inventory)
    for step in flows[0].steps:
        require(step.line is None, f"nome de legado virou instrução: {step.line}")
        require(all("\n" not in comment for comment in step.comments), "quebra de linha vazou")


def test_generate_keeps_optimized_flow_unless_forced(workspace: Path) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    require(reflow_main(["generate", project]) == 0, "generate deveria concluir")
    robin = _robin(workspace, project)
    _rewrite(robin, "**REGION Chamadas externas", "**REGION Enviar dados ao serviço")
    require(reflow_main(["generate", project]) == 1, "não pode apagar a otimização")
    require(b"Enviar dados" in robin.read_bytes(), "o arquivo otimizado continua lá")
    require(reflow_main(["generate", project, "--force"]) == 0, "--force regrava")
    require(b"Enviar dados" not in robin.read_bytes(), "--force volta à base")


def test_gate_accepts_a_legitimate_optimization(workspace: Path) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    reflow_main(["generate", project])
    robin = _robin(workspace, project)
    _rewrite(robin, "**REGION Chamadas externas", "**REGION Enviar dados ao serviço")
    _rewrite(robin, "cfg_03_rest_post_url", "cfg_url_servico")
    require(check_project(workspace, project) == [], "reorganizar e nomear é o papel do agent")


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("# step_05_custom_package_transform", "# passo", "passo removido"),
        ("(main.json:5)", "(sem evidência)", "evidência removida"),
        (
            "SET cfg_03_rest_post_url TO $''''''",
            "SET cfg_03_rest_post_url TO $'''https://inventada.example/api'''",
            "valor inventado",
        ),
    ],
)
def test_gate_blocks_what_the_optimizer_must_not_do(
    workspace: Path, old: str, new: str, expected: str
) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    reflow_main(["generate", project])
    _rewrite(_robin(workspace, project), old, new)
    issues = check_project(workspace, project)
    require(any(expected in issue.message for issue in issues), f"{issues}")
    require(reflow_main(["optimize-check", project]) == 2, "erro precisa reprovar")


def test_gate_blocks_removed_action_and_edited_base(workspace: Path) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    reflow_main(["generate", project])
    robin = _robin(workspace, project)
    lines = robin.read_bytes().decode("utf-8").split("\r\n")
    kept = [line for line in lines if not line.startswith("Web.InvokeWebService")]
    robin.write_bytes("\r\n".join(kept).encode("utf-8"))
    messages = [issue.message for issue in check_project(workspace, project)]
    require(any("ação da base removida" in m for m in messages), f"{messages}")

    with (robin.parent / BASE_NAME).open("ab") as base:
        base.write(b"# mexi\r\n")
    messages = [issue.message for issue in check_project(workspace, project)]
    require(any("base determinística foi editada" in m for m in messages), f"{messages}")


def test_restore_returns_the_base(workspace: Path) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    reflow_main(["generate", project])
    robin = _robin(workspace, project)
    original = robin.read_bytes()
    robin.write_bytes(b"lixo")
    require(reflow_main(["optimize-check", project, "--restore"]) == 2, "reprova antes")
    require(robin.read_bytes() == original, "--restore devolve a base")
    require(restore_base(workspace, project) == ["flow-main"], "lista o que restaurou")


def test_context_pack_carries_only_what_the_flow_uses_and_is_masked(workspace: Path) -> None:
    project = "a360-excel-vault"
    _approve(workspace, project)
    reflow_main(["generate", project])
    pack = build_pack(workspace, project, "reflow-robin-optimizer")
    require("### `Excel.ReadFromExcel.ReadCells`" in pack, "ação usada precisa estar no pacote")
    require("### `Database.Close`" not in pack, "ação não usada fica fora")
    require("flow-main/Main.robin" in pack, "o flow precisa estar no pacote")


def test_report_shows_complexity(workspace: Path) -> None:
    out = build_batch_report(workspace)
    require("| Complexidade |" in out, out)
    require("| a360-excel-vault | a360 | M |" in out, out)
