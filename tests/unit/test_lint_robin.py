"""robin/lint.py de verdade: whitelist, cabeçalho, segredo e caminho absoluto."""

from __future__ import annotations

from pathlib import Path

import pytest

from reflow.robin.lint import lint_robin_files

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
    robin_text: str = "[não validado — TODO reflow]\n",
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
    (flow_dir / "Main.robin").write_text(robin_text, encoding="utf-8")
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


def test_fails_when_notas_conversao_is_missing(tmp_path: Path) -> None:
    root = _make_flow(tmp_path, with_notes=False)
    findings = lint_robin_files(root, project="quote-scraper")
    require(
        any(f.pattern == "notas_conversao_ausente" for f in findings),
        "Falta de notas-conversao.md deveria reprovar o lint.",
    )
