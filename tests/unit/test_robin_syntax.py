"""reflow/robin/syntax.py contra o corpus de colagens reais da KB e casos do reflow."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

import pytest

from reflow.robin.kb import KB_DIR, load_action_kb
from reflow.robin.syntax import check_robin

ROOT = Path(__file__).resolve().parents[2]
# Reprovações por política do reflow, mais estritas que o PAD (ADR-029): segredo
# literal num argumento de senha, e `\%` (o PAD cola mas descarta o `%` em silêncio).
POLICY_CODES = frozenset({"robin_segredo_literal", "robin_barra_antes_de_percent"})


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@cache
def _kb():
    return load_action_kb(ROOT)


def _codes(text: str) -> set[str]:
    return {issue.code for issue in check_robin(text, _kb())}


def _probes() -> list[dict]:
    path = ROOT / KB_DIR / "probe-corpus.json"
    return json.loads(path.read_text(encoding="utf-8"))["probes"]


def test_every_paste_pad_silently_rejected_is_flagged() -> None:
    """107 colagens que o PAD descartou inteiras, sem erro visível."""
    missed = [p["id"] for p in _probes() if p["outcome"] == "rejected" and not _codes(p["robin"])]
    require(not missed, f"colagens rejeitadas pelo PAD que o lint deixou passar: {missed}")


def test_clean_pastes_only_fail_for_documented_policy_reasons() -> None:
    unexpected = {
        p["id"]: sorted(codes - POLICY_CODES)
        for p in _probes()
        if p["outcome"] == "clean" and (codes := _codes(p["robin"])) - POLICY_CODES
    }
    require(not unexpected, f"falso positivo em colagem limpa do PAD: {unexpected}")


def test_most_pastes_that_landed_with_errors_are_flagged() -> None:
    errors = [p for p in _probes() if p["outcome"] == "errors"]
    flagged = sum(1 for p in errors if _codes(p["robin"]))
    require(flagged >= 22, f"só {flagged}/{len(errors)} colagens com erro detectadas")


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("// comentario estilo C\r\n", "robin_comentario_invalido"),
        ('cfg_x: "valor"\r\n', "robin_instrucao_desconhecida"),
        ("[não validado — TODO reflow: colar aqui]\r\n", "robin_instrucao_desconhecida"),
        (
            "Excel.LaunchExcel.Launch Visible: True Instance=> xl\r\n"
            "Excel.CloseExcel.Close Instance: %xl%\r\n",
            "robin_percent_fora_de_string",
        ),
        ("Web.InvokeRestApi Url: $'''x'''\r\n", "robin_acao_desconhecida"),
        ("REGION Leitura\r\nEND REGION\r\n", "robin_regiao_invalida"),
        ("SET a TO $'''Joe's'''\r\n", "robin_apostrofo_sem_escape"),
        ("SET a TO $'''100% feito'''\r\n", "robin_percent_solto"),
        ("SET End TO 1\r\n", "robin_palavra_reservada"),
        ("IF 1 = 1 THEN\r\nSET a TO 1\r\n", "robin_end_faltando"),
        ("SET a TO b + 1\r\n", "robin_variavel_indefinida"),
    ],
)
def test_reflow_specific_mistakes_are_flagged(text: str, code: str) -> None:
    codes = _codes(text)
    require(code in codes, f"esperado {code}, veio {sorted(codes)}")


def test_argument_from_a_sibling_selector_points_to_the_right_selector() -> None:
    """`EndRow` existe em `ReadCells`, não em `ReadCell`: o lint diz onde está."""
    text = (
        "Excel.LaunchExcel.Launch Visible: True Instance=> xl\r\n"
        "Excel.ReadFromExcel.ReadCell Instance: xl StartColumn: $'''A''' StartRow: 1 "
        "EndRow: 3 CellValue=> v\r\n"
    )
    issues = [i for i in check_robin(text, _kb()) if i.code == "robin_argumento_desconhecido"]
    require(issues, "argumento de seletor irmão tinha que reprovar")
    require("Excel.ReadFromExcel.ReadCells" in issues[0].message, issues[0].message)


def test_on_error_follows_the_kb_error_handling_record() -> None:
    no_errors = (
        "Database.Connect.Connect ConnectionString: in_cs Connection=> c\r\n"
        "Database.Close Connection: c\r\nON ERROR\r\n    SET f TO True\r\nEND\r\n"
    )
    require("robin_on_error_nao_suportado" in _codes(no_errors), "Database.Close não gera erro")
    bad_name = (
        "File.ReadTextFromFile.ReadText File: in_f Encoding: File.TextFileEncoding.UTF8 "
        "Content=> c\r\nON ERROR ErroInventado\r\n    SET f TO True\r\nEND\r\n"
    )
    require("robin_erro_desconhecido" in _codes(bad_name), "nome de erro não declarado")
    good = bad_name.replace("ErroInventado", "FileNotFoundError")
    require(not _codes(good), f"tratador válido reprovou: {_codes(good)}")


def test_secret_literal_is_flagged_but_a_variable_is_not() -> None:
    literal = (
        "Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\a.xlsx''' "
        "Visible: True ReadOnly: False UseMachineLocale: False "
        "ReadProtectionPassword: $'''hunter2''' Instance=> xl\r\n"  # reflow:allow-secret
    )
    require("robin_segredo_literal" in _codes(literal), "senha literal tinha que reprovar")
    via_variable = literal.replace("$'''hunter2'''", "$'''%in_senha_planilha%'''")
    require("robin_segredo_literal" not in _codes(via_variable), "senha por variável é válida")


def test_kb_placeholder_ui_element_is_flagged() -> None:
    text = "UIAutomation.FocusWindow.Focus Window: appmask['Window \\'KB Test Window\\'']\r\n"
    require("robin_elemento_ui_de_exemplo" in _codes(text), "elemento de exemplo da KB")


def test_todo_as_robin_comment_and_flow_inputs_are_valid() -> None:
    text = (
        "# TODO reflow: credencial pendente (ver robin-actions.md)\r\n"
        "**REGION Leitura\r\n"
        "Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: in_arquivo Visible: True "
        "ReadOnly: False UseMachineLocale: False Instance=> out_excel\r\n"
        "Excel.CloseExcel.Close Instance: out_excel\r\n"
        "**ENDREGION\r\n"
    )
    require(not _codes(text), f"flow válido reprovou: {_codes(text)}")
