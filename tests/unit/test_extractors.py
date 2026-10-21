"""Synthetic extraction, security boundaries and CLI contracts."""

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from reflow.cli import extract_to, main
from reflow.extractors import detect_extractor
from reflow.extractors.a360 import A360Extractor
from reflow.extractors.dotnet import DotnetExtractor
from reflow.extractors.python import PythonExtractor
from reflow.inventory import FACT_FIELDS
from reflow.security.safe_zip import safe_zip

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_a360_preorder_dependencies_and_credentials() -> None:
    inventory = A360Extractor().extract(FIXTURES / "a360" / "browser-rest")
    require(inventory.http_calls[0]["line"] == 2, "REST deve ser o segundo node.")
    require(inventory.credentials[0]["line"] == 3, "Vault deve ser o terceiro node.")
    require(inventory.dependencies[0]["target"] == "child.json", "Resolver bot filho.")
    require(
        "synthetic-vault-reference" not in json.dumps(inventory.to_dict()),
        "Valor bruto de credencial não deve sair.",
    )


def test_a360_unknown_and_stability() -> None:
    extractor = A360Extractor()
    inventory = extractor.extract(FIXTURES / "a360" / "excel-vault")
    require(len(inventory.unknown_commands) == 2, "Capturar comandos desconhecidos.")
    require(
        inventory.to_dict() == extractor.extract(FIXTURES / "a360" / "excel-vault").to_dict(),
        "Extração deve ser estável.",
    )
    for category in FACT_FIELDS:
        for fact in getattr(inventory, category):
            require(fact["line"] >= 1 and bool(fact["file"]), "Fato exige arquivo:linha.")


def test_python_alias_ast_and_no_execution(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text(
        'import requests as req\nreq.get("https://example.invalid")\n'
        'raise RuntimeError("NÃO EXECUTAR")\n',
        encoding="utf-8",
    )
    inventory = PythonExtractor().extract(tmp_path)
    require(inventory.http_calls[0]["operation"] == "requests.get", "Resolver alias.")
    require(inventory.http_calls[0]["line"] == 2, "Preservar linha do AST.")


def test_python_syntax_error(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("def broken(:", encoding="utf-8")
    require(bool(PythonExtractor().extract(tmp_path).warnings), "Avisar sintaxe inválida.")


def test_dotnet_source_and_binary(tmp_path: Path) -> None:
    shutil.copytree(FIXTURES / "dotnet", tmp_path, dirs_exist_ok=True)
    (tmp_path / "legacy.dll").write_bytes(b"synthetic-not-an-assembly")
    inventory = DotnetExtractor().extract(tmp_path)
    require(bool(inventory.http_calls) and bool(inventory.data_sources), "Detectar HTTP/IO.")
    require(
        any(w["message"] == "decompile com ILSpy antes" for w in inventory.warnings),
        "Binários exigem aviso ILSpy.",
    )


def test_a360_registry_covers_window_soap_and_database(tmp_path: Path) -> None:
    document = {
        "nodes": [
            {"packageName": "Window", "commandName": "activate", "attributes": {}},
            {"packageName": "SOAP", "commandName": "call", "attributes": {"url": "x"}},
            {"packageName": "Database", "commandName": "query", "attributes": {"sql": "x"}},
        ]
    }
    (tmp_path / "main.json").write_text(json.dumps(document), encoding="utf-8")
    inventory = A360Extractor().extract(tmp_path)
    require(len(inventory.ui_interactions) == 1, "Window/activate deve ser ui_interactions.")
    require(len(inventory.http_calls) == 1, "SOAP/call deve ser http_calls.")
    require(len(inventory.data_sources) == 1, "Database/query deve ser data_sources.")
    require(not inventory.unknown_commands, "Nenhum comando deveria ficar desconhecido aqui.")


def test_registry_precedence_and_unsupported(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    (tmp_path / "main.cs").write_text("class Example {}", encoding="utf-8")
    require(detect_extractor(tmp_path).name == "dotnet", ".NET vence Python.")
    shutil.copy(FIXTURES / "a360" / "excel-vault" / "main.json", tmp_path)
    require(detect_extractor(tmp_path).name == "a360", "A360 deve ter prioridade.")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="nenhuma origem suportada"):
        detect_extractor(empty)


def test_zip_folder_and_cleanup(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.write(FIXTURES / "a360" / "excel-vault" / "main.json", "bot.json")
    require(A360Extractor().detect(tmp_path), "Aceitar export ZIP dentro da pasta.")
    require(len(A360Extractor().extract(archive).data_sources) == 2, "Extrair ZIP.")
    require(not list(tmp_path.glob(".reflow-zip-*")), "Limpar temporários.")


@pytest.mark.parametrize("name", ["../escape.json", "/absolute.json", "C:/escape.json"])
def test_zip_rejects_paths(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(name, "{}")
    with pytest.raises(ValueError, match="inseguro"), safe_zip(archive, tmp_path):
        pytest.fail("Não deve extrair caminho inseguro.")


def test_zip_limits(tmp_path: Path) -> None:
    archive = tmp_path / "large.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("big.txt", "x" * 10000)
    with pytest.raises(ValueError, match="tamanho"), safe_zip(archive, tmp_path, max_file_size=10):
        pytest.fail("Não deve extrair acima do limite.")


def test_cli_batch_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    inputs = tmp_path / "input"
    shutil.copytree(ROOT / "input" / "quote-scraper", inputs / "quote-scraper")
    for name in ("browser-rest", "excel-vault"):
        shutil.copytree(FIXTURES / "a360" / name, inputs / name)
    require(main(["extract", "--all"]) == 0, "Lote deve concluir.")
    require(main(["report"]) == 0, "Relatório deve concluir.")
    manifest = json.loads((tmp_path / "output/browser-rest/00-manifest.json").read_text("utf-8"))
    require(len(manifest["inputs"][0]["sha256"]) == 64, "Manifesto exige SHA256.")
    require(manifest["checkpoint"] is None, "Nunca presumir aprovação.")
    require(main(["extract", "../escape"]) != 0, "Rejeitar traversal no projeto.")


def test_extract_to_writes_inventory_without_manifest(tmp_path: Path) -> None:
    out_dir = tmp_path / "isolated-run" / "quote-scraper"
    source_type, inventory = extract_to(ROOT / "input" / "quote-scraper", out_dir)
    require(source_type == "python", "Fixture quote-scraper é Python.")
    require(inventory.project == "quote-scraper", "Nome do projeto vem do diretório.")
    require((out_dir / "01-inventory" / "inventory.json").is_file(), "Inventário tem que existir.")
    require(not (out_dir / "00-manifest.json").is_file(), "extract_to não grava manifesto.")
