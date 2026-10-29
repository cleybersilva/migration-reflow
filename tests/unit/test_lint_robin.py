"""robin/lint.py de verdade: whitelist, cabeçalho, segredo e caminho absoluto."""

from __future__ import annotations

from pathlib import Path

import pytest

from reflow.robin.lint import fix_robin_eol, lint_robin_files, normalize_robin_eol

WHITELIST = """\
### `Browser.LaunchNewBrowser`
- Módulo: Browser
- Quando usar: abrir o navegador.
- Status: [não validado]

```robin
[não validado — TODO reflow]
```
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _make_flow(
    tmp_path: Path,
    *,
    robin_text: str = "[não validado — TODO reflow]\r\n",
    readme_text: str = "# quote-scraper — fluxo principal\n",
    notes_text: str = "# Notas de conversão\n\n- `Browser.LaunchNewBrowser` — abre o navegador\n",
    with_whitelist: bool = True,
    with_notes: bool = True,
    with_readme: bool = True,
) -> Path:
    (tmp_path / "reference").mkdir(exist_ok=True)
    if with_whitelist:
        (tmp_path / "reference" / "robin-actions.md").write_text(WHITELIST, encoding="utf-8")

    flow_dir = tmp_path / "output" / "quote-scraper" / "04-pad" / "main-flow"
    flow_dir.mkdir(parents=True)
    # write_bytes (nunca write_text): quebra de linha tem que ser exatamente a
    # da string acima em qualquer SO — write_text traduziria "\n" para
    # os.linesep, que já é "\r\n" no Windows e mascararia o teste de EOL.
    (flow_dir / "Main.robin").write_bytes(robin_text.encode("utf-8"))
    if with_readme:
        (flow_dir / "README.md").write_text(readme_text, encoding="utf-8")
    if with_notes:
        (flow_dir / "notas-conversao.md").write_text(notes_text, encoding="utf-8")
    return tmp_path


def test_valid_flow_passes_clean(tmp_path: Path) -> None:
    root = _make_flow(tmp_path)
    findings = lint_robin_files(root, project="quote-scraper")
    require(not findings, f"Fluxo válido não deveria reprovar: {findings}")


def test_fails_when_action_is_outside_the_whitelist(tmp_path: Path) -> None:
    root = _make_flow(
        tmp_path,
        notes_text="# Notas\n\n- `Browser.ActionThatDoesNotExist` — tentativa\n",
    )
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "acao_fora_da_whitelist" for f in findings),
        "Ação fora da whitelist deveria reprovar o lint.",
    )


def test_fails_when_flow_header_is_missing(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, readme_text="sem cabeçalho nenhum\n")
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "cabecalho_ausente" for f in findings),
        "README sem cabeçalho `# ...` deveria reprovar o lint.",
    )


def test_fails_when_main_robin_has_an_assigned_secret(tmp_path: Path) -> None:
    leaked = 'API_KEY="sk-this-is-not-a-placeholder"\n'  # reflow:allow-secret
    root = _make_flow(tmp_path, robin_text=leaked)
    findings = lint_robin_files(root, project="quote-scraper")
    secret_findings = [f for f in findings if f.pattern == "segredo_no_robin"]
    require(bool(secret_findings), "Segredo atribuído dentro do Main.robin deveria reprovar.")
    require(
        "sk-this-is-not-a-placeholder" not in secret_findings[0].excerpt,
        "O achado nunca pode ecoar o segredo real.",
    )


def test_fails_when_absolute_path_is_outside_the_allowed_prefix(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, robin_text=r"out_path = C:\Windows\System32\config.sys" + "\n")
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "caminho_fora_do_permitido" for f in findings),
        "Caminho fora de C:\\Users\\Public\\Documents\\ deveria reprovar.",
    )


def test_path_inside_the_allowed_prefix_does_not_fail(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, robin_text=r"out_path = C:\Users\Public\Documents\saida.csv" + "\n")
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        not any(f.pattern == "caminho_fora_do_permitido" for f in findings),
        "Caminho dentro do prefixo permitido não deveria reprovar.",
    )


def test_fails_when_allowed_prefix_is_followed_by_dotdot_escape(tmp_path: Path) -> None:
    """A string começa com o prefixo permitido, mas `..\\..\\` sai dele — a
    checagem tem que resolver o caminho, não só comparar o começo da string."""
    root = _make_flow(
        tmp_path,
        robin_text=(r"out_path = C:\Users\Public\Documents\..\..\Windows\System32\cmd.exe" + "\n"),
    )
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "caminho_fora_do_permitido" for f in findings),
        "Escape por .. depois do prefixo permitido deveria reprovar.",
    )


def test_relative_dotdot_that_stays_inside_the_allowed_prefix_does_not_fail(
    tmp_path: Path,
) -> None:
    """`..` legítimo que não sai do prefixo permitido não deveria reprovar."""
    root = _make_flow(
        tmp_path,
        robin_text=(r"out_path = C:\Users\Public\Documents\Sub\..\OtherSub\saida.csv" + "\n"),
    )
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        not any(f.pattern == "caminho_fora_do_permitido" for f in findings),
        "O .. fica dentro do prefixo permitido; não deveria reprovar.",
    )


def test_fails_when_path_is_unc(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, robin_text=r"out_path = \\fileserver\share\saida.csv" + "\n")
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "caminho_unc_nao_permitido" for f in findings),
        "Caminho UNC nunca é permitido e tem que reprovar o lint.",
    )


def test_fails_when_notas_conversao_is_missing(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, with_notes=False)
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "notas_conversao_ausente" for f in findings),
        "Falta de notas-conversao.md deveria reprovar o lint.",
    )


def test_fails_when_main_robin_has_bare_lf(tmp_path: Path) -> None:
    """LF puro é a causa mais comum de um .robin que cola errado no PAD."""
    root = _make_flow(tmp_path, robin_text="[não validado — TODO reflow]\n")
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "eol_lf_sem_cr" for f in findings),
        "Main.robin com LF puro (sem \\r) deveria reprovar — PAD espera CRLF.",
    )


def test_passes_when_main_robin_is_already_crlf(tmp_path: Path) -> None:
    root = _make_flow(tmp_path)  # robin_text padrão já termina em \r\n
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        not any(f.pattern == "eol_lf_sem_cr" for f in findings),
        "Main.robin já em CRLF não deveria reprovar por quebra de linha.",
    )


def test_fails_when_only_some_lines_are_bare_lf(tmp_path: Path) -> None:
    """Mistura de CRLF e LF no mesmo arquivo também tem que reprovar."""
    mixed = "linha_1\r\nlinha_2\nlinha_3\r\n"
    root = _make_flow(tmp_path, robin_text=mixed)
    findings = lint_robin_files(root, project="quote-scraper")
    eol_findings = [f for f in findings if f.pattern == "eol_lf_sem_cr"]
    require(len(eol_findings) == 1, "Uma única mistura de EOL deveria gerar um achado.")
    require("1 de 3" in eol_findings[0].excerpt, f"Contagem errada: {eol_findings[0].excerpt}")


def test_normalize_robin_eol_converts_bare_lf_to_crlf(tmp_path: Path) -> None:
    path = tmp_path / "Main.robin"
    path.write_bytes(b"linha_1\nlinha_2\nlinha_3\n")
    changed = normalize_robin_eol(path)
    require(changed, "Arquivo com LF puro deveria ser normalizado (mudou).")
    require(
        path.read_bytes() == b"linha_1\r\nlinha_2\r\nlinha_3\r\n",
        "Toda quebra de linha deveria virar CRLF.",
    )


def test_normalize_robin_eol_is_a_noop_when_already_crlf(tmp_path: Path) -> None:
    path = tmp_path / "Main.robin"
    path.write_bytes(b"linha_1\r\nlinha_2\r\n")
    changed = normalize_robin_eol(path)
    require(not changed, "Arquivo já em CRLF não deveria ser reescrito.")
    require(path.read_bytes() == b"linha_1\r\nlinha_2\r\n", "Conteúdo não pode mudar.")


def test_normalize_robin_eol_does_not_duplicate_existing_cr(tmp_path: Path) -> None:
    """Mistura de CRLF e LF: o CR existente não pode virar CRCRLF."""
    path = tmp_path / "Main.robin"
    path.write_bytes(b"linha_1\r\nlinha_2\n")
    normalize_robin_eol(path)
    require(
        path.read_bytes() == b"linha_1\r\nlinha_2\r\n",
        "Linha já com \\r\\n não pode ganhar um \\r extra.",
    )


def test_fix_robin_eol_normalizes_every_main_robin_under_the_project(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, robin_text="[não validado — TODO reflow]\n")
    robin_path = root / "output" / "quote-scraper" / "04-pad" / "main-flow" / "Main.robin"
    require(b"\r\n" not in robin_path.read_bytes(), "Pré-condição: começa só com LF.")

    changed = fix_robin_eol(root, project="quote-scraper")

    require(changed == [robin_path], f"fix_robin_eol deveria normalizar {robin_path}.")
    require(robin_path.read_bytes().endswith(b"\r\n"), "Arquivo deveria terminar em CRLF.")
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        not any(f.pattern == "eol_lf_sem_cr" for f in findings),
        "Depois do fix, lint-robin não deveria mais reprovar por EOL.",
    )


def test_fix_robin_eol_returns_empty_when_nothing_to_fix(tmp_path: Path) -> None:
    root = _make_flow(tmp_path)  # robin_text padrão já em CRLF
    changed = fix_robin_eol(root, project="quote-scraper")
    require(changed == [], "Nada para normalizar deveria devolver lista vazia.")
