"""KB Robin vendorizada: integridade por hash, loader e isenção estreita do scan."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.cli import main
from reflow.robin.kb import KB_DIR, VENDORED_FILES, load_action_kb, pinned_hashes, verify_kb
from reflow.security.scan import scan_bytes, scan_repository

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@pytest.fixture
def kb_copy(tmp_path: Path) -> Path:
    """Repositório mínimo com uma cópia da pasta vendorizada (sem git)."""
    shutil.copytree(ROOT / KB_DIR, tmp_path / KB_DIR)
    return tmp_path


def test_vendored_kb_matches_manifest() -> None:
    findings = verify_kb(ROOT)
    require(findings == [], f"KB vendorizada diverge do manifesto: {findings}")


def test_manifest_records_provenance_and_license() -> None:
    manifest = json.loads((ROOT / KB_DIR / "manifest.json").read_text(encoding="utf-8"))
    for key in ("source", "tag", "commit", "license", "author", "pad_build", "kb_version"):
        require(bool(manifest.get(key)), f"manifest.json sem {key}")
    require(manifest["license"] == "CC BY 4.0", "licença tem que ser a CC BY 4.0 do upstream")
    require(len(manifest["commit"]) == 40, "commit tem que ser o SHA completo")


def test_tampered_file_fails_verify(kb_copy: Path) -> None:
    target = kb_copy / KB_DIR / "PROMPT.md"
    target.write_bytes(target.read_bytes() + b"\n")
    patterns = {finding.pattern for finding in verify_kb(kb_copy)}
    require("kb_hash_divergente" in patterns, f"edição não detectada: {patterns}")


def test_extra_file_in_vendor_dir_fails_verify(kb_copy: Path) -> None:
    (kb_copy / KB_DIR / "extra.json").write_text("{}", encoding="utf-8")
    patterns = {finding.pattern for finding in verify_kb(kb_copy)}
    require("kb_arquivo_extra" in patterns, f"arquivo extra não detectado: {patterns}")


def test_manifest_cannot_bless_files_outside_the_closed_set(kb_copy: Path) -> None:
    manifest_path = kb_copy / KB_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"].append({"path": "segredo.env", "sha256": "0" * 64})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    require(
        all(not path.endswith("segredo.env") for path in pinned_hashes(kb_copy)),
        "manifesto conseguiu isentar arquivo fora do conjunto fechado",
    )
    patterns = {finding.pattern for finding in verify_kb(kb_copy)}
    require("kb_lista_de_arquivos" in patterns, f"entrada indevida não detectada: {patterns}")


def test_pinned_vendor_files_are_exempt_from_scan_only_while_unmodified(kb_copy: Path) -> None:
    require(scan_repository(kb_copy) == [], "KB íntegra não deveria gerar achado no scan")
    target = kb_copy / KB_DIR / "PAD_Robin_ActionKB.json"
    target.write_bytes(target.read_bytes() + b"\n")
    findings = scan_repository(kb_copy)
    require(
        any(finding.file.endswith("PAD_Robin_ActionKB.json") for finding in findings),
        "KB editada perdeu a isenção e tinha que voltar a ser varrida",
    )


def test_manifest_and_readme_are_always_scanned(kb_copy: Path) -> None:
    readme = kb_copy / KB_DIR / "README.md"
    leaked = "\napi_key=abc123real\n"  # reflow:allow-secret
    readme.write_text(readme.read_text(encoding="utf-8") + leaked, "utf-8")
    require(
        any(finding.file.endswith("README.md") for finding in scan_repository(kb_copy)),
        "README da pasta vendorizada não pode ser isento",
    )


def test_loader_indexes_actions_case_insensitively() -> None:
    actions = load_action_kb(ROOT)
    require(len(actions) == 1086, f"esperado 1086 ações na KB 3.4.0, veio {len(actions)}")
    action = actions["excel.readfromexcel.readcell"]
    require(action.action_id == "Excel.ReadFromExcel.ReadCell", "actionId original preservado")
    require("instance" in action.input_names, "entrada Instance indexada")
    require("ReadCellsError" in action.errors, "error_handling indexado")
    require(
        "Excel.ReadFromExcel.ReadCells" in action.sibling_selectors, "seletores irmãos indexados"
    )


def test_closed_set_matches_manifest() -> None:
    manifest = json.loads((ROOT / KB_DIR / "manifest.json").read_text(encoding="utf-8"))
    require(
        {entry["path"] for entry in manifest["files"]} == VENDORED_FILES,
        "manifesto e conjunto fechado divergem",
    )


def test_cli_kb_verify_and_show(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    require(main(["kb", "verify"]) == 0, "kb verify deveria passar no repositório")
    require(main(["kb", "show", "excel.closeexcel.close"]) == 0, "kb show deveria achar a ação")
    out = capsys.readouterr().out
    require("Excel.CloseExcel.Close Instance: ExcelInstance" in out, f"exemplo ausente: {out}")
    require(main(["kb", "show", "Text.Concatenate"]) == 1, "ação inexistente tem que falhar")


@pytest.mark.parametrize(
    ("line", "flagged"),
    [
        (
            "FTP.Open Password: $'''hunter2''' Instance=> xl",  # reflow:allow-secret
            True,
        ),
        ("FTP.Open Password: $'''%in_senha%''' Instance=> xl", False),
        ("FTP.Open Password: $'''''' Instance=> xl", False),
        ("Database.Connect.Connect ConnectionString: cfg_db_cs Connection=> c", False),
        (
            "Web.X CustomHeaders: $'''Authorization: %cfg_rest_auth_scheme% %in_rest_token%''' "
            "RequestBody: $'''%out_excel_data%'''",
            False,
        ),
        (
            "Web.X H: $'''Authorization: %cfg_a% abc123real''' Y: z",  # reflow:allow-secret
            True,
        ),
        ("- monta `Authorization: %cfg_rest_auth_scheme% %in_rest_token%`.", False),
        ("- monta `Authorization: %cfg_a% abc123real`.", True),  # reflow:allow-secret
        ("password=hunter2", True),  # reflow:allow-secret
        ("api_key: real-value-123", True),  # reflow:allow-secret
    ],
)
def test_scanner_reads_robin_literals_instead_of_the_dollar_sign(line: str, flagged: bool) -> None:
    """ADR-029: antes, o literal Robin virava o valor `$` e nunca era lido. Argumento
    composto (`ReadProtectionPassword`) é coberto pelo lint de sintaxe, não por aqui."""
    findings = scan_bytes(line.encode("utf-8"), "output/x/04-pad/f/Main.robin")
    require(bool(findings) == flagged, f"{line!r}: esperado flagged={flagged}, veio {findings}")
