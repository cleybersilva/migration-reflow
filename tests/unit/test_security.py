"""Masking, safe_zip (zip-slip/tamanho/quantidade) e redação dos achados do scan."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from reflow.security.masking import is_placeholder_value, mask_pii, mask_secrets
from reflow.security.safe_zip import safe_zip
from reflow.security.scan import scan_repository

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_mask_secrets_redacts_value_keeps_key() -> None:
    masked = mask_secrets('API_KEY="sk-real-secret-value"')  # reflow:allow-secret
    require("sk-real-secret-value" not in masked, "O valor real não pode sobrar na máscara.")
    require("API_KEY" in masked and "***" in masked, "A chave fica, o valor vira ***.")


def test_mask_secrets_ignores_unrelated_text() -> None:
    text = "Mascarar secrets e PII antes de gravar saídas."
    require(mask_secrets(text) == text, "Texto sem atribuição não deve ser alterado.")


def test_mask_pii_redacts_cpf_cnpj_email_phone_and_account() -> None:
    text = (  # reflow:allow-secret
        "CPF 123.456.789-01, CNPJ 12.345.678/0001-99, e-mail a@b.com, "  # reflow:allow-secret
        "telefone (11) 91234-5678, conta: 12345-6"  # reflow:allow-secret
    )
    masked = mask_pii(text)
    leaked_values = [
        "123.456.789-01",  # reflow:allow-secret
        "12.345.678/0001-99",  # reflow:allow-secret
        "a@b.com",  # reflow:allow-secret
        "91234-5678",  # reflow:allow-secret
        "12345-6",  # reflow:allow-secret
    ]
    for leaked in leaked_values:
        require(leaked not in masked, f"PII não mascarada: {leaked}")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", True),
        ("xxx", True),
        ("{env:IARA_API_KEY}", True),
        ("synthetic-vault-reference", True),
        ("not-a-real-credential", True),
        ("sk-this-looks-real-12345", False),
    ],
)
def test_is_placeholder_value(value: str, expected: bool) -> None:
    require(is_placeholder_value(value) is expected, f"Classificação errada para {value!r}.")


def test_safe_zip_rejects_too_many_files(tmp_path: Path) -> None:
    archive = tmp_path / "many.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for index in range(3):
            bundle.writestr(f"file-{index}.json", "{}")
    zipped = safe_zip(archive, tmp_path, max_file_count=2)
    with pytest.raises(ValueError, match="quantidade"), zipped:
        pytest.fail("Não deve extrair acima do limite de quantidade de arquivos.")


def test_scan_excerpt_never_echoes_the_real_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    content = f'API_KEY="{secret}"\n'  # reflow:allow-secret
    (tmp_path / "leak.env").write_text(content, encoding="utf-8")
    findings = scan_repository(tmp_path)
    require(bool(findings), "Deveria encontrar o segredo atribuído.")
    for finding in findings:
        require(secret not in finding.excerpt, "O achado nunca pode ecoar o segredo real.")
