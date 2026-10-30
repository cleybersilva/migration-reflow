"""Masking, safe_zip (zip-slip/tamanho/quantidade) e redação dos achados do scan."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from reflow.security.masking import is_placeholder_value, mask_data, mask_pii, mask_secrets
from reflow.security.safe_zip import safe_zip
from reflow.security.scan import StagedScanError, scan_bytes, scan_repository, scan_staged

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)  # noqa: S603, S607


def _init_repo(root: Path) -> None:
    _git(["init", "-q"], root)
    _git(["config", "user.email", "reflow-test@example.com"], root)  # reflow:allow-secret
    _git(["config", "user.name", "reflow-test"], root)


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
        ("read", True),
        ("write", True),
        ("none", True),
    ],
)
def test_is_placeholder_value(value: str, expected: bool) -> None:
    require(is_placeholder_value(value) is expected, f"Classificação errada para {value!r}.")


def test_github_actions_permission_scopes_are_not_flagged_as_secrets() -> None:
    """Chaves do bloco permissions do workflow nunca são segredo, mesmo quando a
    chave contém a palavra sensível "token" (caso de id-token) — sem
    is_placeholder_value reconhecer o vocabulário fechado read/write/none isso
    reprovaria todo workflow que usa OIDC."""
    text = "id-token: write\ncontents: read\npages: write\n"  # reflow:allow-secret
    findings = scan_bytes(text.encode("utf-8"), "workflow.yml")
    require(not findings, f"Permissão de GitHub Actions não deveria reprovar o scan: {findings}")


def test_a_real_looking_token_value_still_gets_flagged() -> None:
    """Garante que a correção acima não destampou a detecção real de token."""
    text = 'token: "ghp_abcdef1234567890abcdef1234567890"\n'  # reflow:allow-secret
    findings = scan_bytes(text.encode("utf-8"), "config.yml")
    require(findings, "Um valor de token real ainda precisa reprovar o scan.")


def test_markdown_inline_code_backtick_right_after_the_value_is_not_swallowed() -> None:
    """Prosa em Markdown tipo "`id-token: write` (permissão OIDC)" não pode
    reprovar: sem a crase no conjunto de paradas do valor, "write`" vira o
    valor capturado (nunca igual a "write" sozinho) e o achado falso volta."""
    text = (  # reflow:allow-secret
        "Ao commitar `id-token: write` (permissão OIDC exigida pelo deploy), reprovou.\n"
    )
    findings = scan_bytes(text.encode("utf-8"), "docs/decisions.md")
    require(not findings, f"Crase colada ao valor não deveria reprovar o scan: {findings}")


def test_a_real_token_immediately_followed_by_a_backtick_still_gets_flagged() -> None:
    """A crase vira parada do valor, mas não pode virar uma forma nova de
    escapar a detecção de um segredo real (ex.: um token real citado em
    Markdown, com a crase de fechamento colada nele)."""
    text = "Rotacione `token: ghp_abc123xyz789` antes de publicar.\n"  # reflow:allow-secret
    findings = scan_bytes(text.encode("utf-8"), "docs/runbook.md")
    require(findings, "Token real colado a uma crase ainda precisa reprovar o scan.")


def test_safe_zip_rejects_too_many_files(tmp_path: Path) -> None:
    archive = tmp_path / "many.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for index in range(3):
            bundle.writestr(f"file-{index}.json", "{}")
    zipped = safe_zip(archive, tmp_path, max_file_count=2)
    with pytest.raises(ValueError, match="quantidade"), zipped:
        pytest.fail("Não deve extrair acima do limite de quantidade de arquivos.")


@pytest.mark.parametrize(
    "name",
    [
        "con",
        "con.txt",
        "CON.TXT",
        "sub/prn.json",
        "nul.py",
        "com1.cs",
        "lpt9",
    ],
)
def test_zip_rejects_windows_reserved_device_names(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "reserved.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(name, "{}")
    with pytest.raises(ValueError, match="inseguro"), safe_zip(archive, tmp_path):
        pytest.fail(f"Não deve extrair nome reservado do Windows: {name!r}.")


@pytest.mark.parametrize(
    "name",
    ["normal.txt:hidden", "normal.txt:$DATA", "sub/file.txt:stream"],
)
def test_zip_rejects_alternate_data_stream_names(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "ads.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(name, "conteudo")
    with pytest.raises(ValueError, match="inseguro"), safe_zip(archive, tmp_path):
        pytest.fail(f"Não deve extrair nome com Alternate Data Stream: {name!r}.")


@pytest.mark.parametrize("name", ["file.txt ", "file.txt.", "sub./file.txt"])
def test_zip_rejects_trailing_dot_or_space_component(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "trailing.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(name, "conteudo")
    with pytest.raises(ValueError, match="inseguro"), safe_zip(archive, tmp_path):
        pytest.fail(f"Não deve extrair componente com espaço/ponto final: {name!r}.")


def test_zip_rejects_case_insensitive_collision(tmp_path: Path) -> None:
    archive = tmp_path / "collide.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("Report.txt", "primeira versão")
        bundle.writestr("report.txt", "segunda versão, sobrescreveria a primeira no Windows")
    with pytest.raises(ValueError, match="[Cc]olis"), safe_zip(archive, tmp_path):
        pytest.fail("Não deve extrair dois membros que colidem no Windows (case-insensitive).")


def test_zip_allows_same_exact_name_twice_without_treating_as_collision(tmp_path: Path) -> None:
    """Duas entradas idênticas (mesmo nome exato) não são 'colisão' no
    sentido novo — isso já era permitido antes (a segunda sobrescreve a
    primeira na extração) e continua sendo, sem relação com case/espaço."""
    archive = tmp_path / "exact-duplicate.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("same.txt", "primeira")
        bundle.writestr("same.txt", "segunda")
    with safe_zip(archive, tmp_path) as extracted:
        content = (extracted / "same.txt").read_text(encoding="utf-8")
        require(content == "segunda", "Última escrita vence, como antes.")


def test_scan_bytes_finds_the_same_patterns_as_scan_repository() -> None:
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    content = f'API_KEY="{secret}"\n'.encode()  # reflow:allow-secret
    findings = scan_bytes(content, "preview.json")
    require(bool(findings), "scan_bytes deveria encontrar o segredo atribuído.")
    for finding in findings:
        require(secret not in finding.excerpt, "O achado nunca pode ecoar o segredo real.")


def test_scan_bytes_ignores_undecodable_content() -> None:
    findings = scan_bytes(b"\xff\xfe\x00", "bin.dat")
    require(findings == [], "Bytes não-UTF-8 não devem quebrar o scan.")


def test_mask_data_redacts_nested_strings_in_dict_and_list() -> None:
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    payload = {"evidence": [{"file": "a.json", "note": f"token={secret}"}]}  # reflow:allow-secret
    masked = mask_data(payload)
    require(secret not in str(masked), "mask_data tem que mascarar strings aninhadas.")
    require(masked["evidence"][0]["file"] == "a.json", "Valor sem segredo/PII não muda.")


def test_mask_data_passes_through_non_string_leaves() -> None:
    original = {"line": 12, "ok": True}
    require(mask_data(original) == original, "Número/booleano ficam iguais.")


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


def test_mask_data_redacts_value_by_sensitive_key_without_inline_assignment() -> None:
    """Chave e valor são strings separadas num dict — não há `chave=valor` no
    mesmo texto, então só `mask_secrets` (que olha uma string por vez) nunca
    veria a associação. `mask_data` tem que mascarar pelo nome da chave."""
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    payload = {
        "password": secret,  # reflow:allow-secret
        "connection_string": secret,  # reflow:allow-secret
        "nested": {"api_key": secret, "name": "robot-01"},  # reflow:allow-secret
        "list_of_secrets": {"authorization": [secret, secret]},  # reflow:allow-secret
    }
    masked = mask_data(payload)
    require(secret not in str(masked), "Nenhuma chave sensível pode deixar o valor real sobrar.")
    require(masked["password"] == "***", "password vira ***.")  # noqa: S105
    require(masked["connection_string"] == "***", "connection_string vira ***.")
    require(masked["nested"]["api_key"] == "***", "api_key aninhada vira ***.")
    require(masked["nested"]["name"] == "robot-01", "Chave não sensível não muda.")
    require(
        masked["list_of_secrets"]["authorization"] == ["***", "***"],
        "Lista de segredos sob chave sensível vira *** item a item.",
    )


def test_mask_data_keeps_legitimate_placeholders_under_sensitive_key() -> None:
    payload = {"password": "{env:IARA_API_KEY}", "token": "***", "api_key": "xxx"}
    require(
        mask_data(payload) == payload,
        "Placeholder legítimo sob chave sensível não deve mudar nem dobrar máscara.",
    )


def test_mask_secrets_redacts_authorization_bearer_header() -> None:
    token = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    masked = mask_secrets(f"Authorization: Bearer {token}")  # reflow:allow-secret
    require(token not in masked, "O token real do header Bearer não pode sobrar.")
    require("Authorization" in masked, "O nome do header é preservado.")


def test_mask_secrets_redacts_quoted_json_key() -> None:
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    masked = mask_secrets(f'"password": "{secret}"')  # reflow:allow-secret
    require(secret not in masked, "Atribuição JSON (chave entre aspas) tem que ser mascarada.")
    require('"password"' in masked, "O nome da chave JSON é preservado.")


def test_scan_excerpt_masks_before_truncating_long_credential(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Credencial maior que o trecho de 120 caracteres exibido: a máscara tem
    que acontecer antes do corte, nunca depois — senão o corte pode cair no
    meio do nome da chave e deixar o regex de segredo sem reconhecer nada."""
    monkeypatch.chdir(tmp_path)
    secret = "sk-" + ("x" * 200)  # noqa: S105  # reflow:allow-secret
    content = f'API_KEY="{secret}"\n'  # reflow:allow-secret
    (tmp_path / "leak.env").write_text(content, encoding="utf-8")
    findings = scan_repository(tmp_path)
    require(bool(findings), "Deveria encontrar o segredo atribuído.")
    for finding in findings:
        require(secret not in finding.excerpt, "O achado nunca pode ecoar o segredo real.")
        require(secret[:80] not in finding.excerpt, "Nem um prefixo longo pode escapar truncado.")


def test_allow_marker_is_ignored_outside_tests_and_detector_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text(
        'password="sk-this-is-a-real-looking-secret"  # reflow:allow-secret\n',
        encoding="utf-8",
    )
    findings = scan_repository(tmp_path)
    require(
        bool(findings),
        "Fora de tests/ e dos módulos do detector, o marcador não pode silenciar um achado.",
    )


def test_allow_marker_is_honored_under_tests_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "tests" / "unit"
    nested.mkdir(parents=True)
    (nested / "fixture.py").write_text(
        'password="sk-this-is-a-real-looking-secret"  # reflow:allow-secret\n',
        encoding="utf-8",
    )
    findings = scan_repository(tmp_path)
    require(findings == [], "Fixture sintética dentro de tests/ continua podendo usar o marcador.")


def test_allow_marker_does_not_bypass_scan_bytes_for_isolated_content() -> None:
    """`scan_bytes` é usado pelo dashboard para checar saída de LLM antes de
    servi-la — teria que ser impossível para esse conteúdo (nunca sob
    tests/ nem módulo do detector) se autoexcluir citando o marcador."""
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    content = f'password="{secret}"  # reflow:allow-secret\n'.encode()  # reflow:allow-secret
    findings = scan_bytes(content, "preview.json")
    require(bool(findings), "Conteúdo isolado não pode usar o marcador para escapar do scan.")


def test_scan_staged_reads_index_not_working_tree(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    path = tmp_path / "config.txt"
    path.write_text(f'password="{secret}"\n', encoding="utf-8")  # reflow:allow-secret
    _git(["add", "config.txt"], tmp_path)
    path.write_text("conteudo local sem nenhum segredo\n", encoding="utf-8")

    staged_findings = scan_staged(tmp_path)
    working_findings = scan_repository(tmp_path)

    require(bool(staged_findings), "scan_staged tem que achar o segredo que está no índice.")
    require(working_findings == [], "working tree está limpa; scan_repository não acha nada.")
    for finding in staged_findings:
        require(secret not in finding.excerpt, "Achado do índice nunca ecoa o segredo real.")


def test_scan_staged_ignores_secret_only_in_working_tree(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "clean.txt").write_text("nada sensivel aqui\n", encoding="utf-8")
    _git(["add", "clean.txt"], tmp_path)
    _git(["commit", "-q", "-m", "baseline"], tmp_path)
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    leaked = f'token="{secret}"\n'  # reflow:allow-secret
    (tmp_path / "clean.txt").write_text(leaked, encoding="utf-8")

    require(
        scan_staged(tmp_path) == [],
        "Segredo só na working tree (sem git add) não pode bloquear o commit.",
    )


def test_scan_staged_skips_file_removed_from_index(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    leaked = f'token="{secret}"\n'  # reflow:allow-secret
    (tmp_path / "secret.txt").write_text(leaked, encoding="utf-8")
    _git(["add", "secret.txt"], tmp_path)
    _git(["rm", "--cached", "-q", "secret.txt"], tmp_path)

    require(scan_staged(tmp_path) == [], "Arquivo removido do índice não deve gerar achado.")


def test_scan_staged_handles_names_with_spaces_and_accents(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    secret = "sk-this-is-a-real-looking-secret"  # noqa: S105  # reflow:allow-secret
    name = "arquivo com espaco e acentuacao ç.txt"
    (tmp_path / name).write_text(f'password="{secret}"\n', encoding="utf-8")  # reflow:allow-secret
    _git(["add", name], tmp_path)

    findings = scan_staged(tmp_path)
    require(bool(findings), "Nome de arquivo com espaço/acento não pode impedir a detecção.")
    require(all(finding.file == name for finding in findings), "Nome do arquivo é preservado.")


def test_scan_staged_flags_non_utf8_content_instead_of_silently_skipping(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00\x01")
    _git(["add", "bin.dat"], tmp_path)

    findings = scan_staged(tmp_path)
    require(
        bool(findings),
        "Conteúdo não UTF-8 preparado tem que gerar achado explícito, não silêncio.",
    )
    require(
        all(finding.pattern == "conteudo_nao_utf8" for finding in findings),
        "O achado tem que dizer que o conteúdo não foi inspecionado, nunca alegar o contrário.",
    )


def test_scan_staged_raises_instead_of_succeeding_silently_when_index_unreadable(
    tmp_path: Path,
) -> None:
    with pytest.raises(StagedScanError):
        scan_staged(tmp_path)
