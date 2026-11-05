"""reference/robin-actions.md e reference/a360-to-pad.md: leitura e coerência cruzada."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from reflow.robin import load_truth_table, load_whitelist, truth_table_action_name
from reflow.robin.kb import load_action_kb

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_whitelist_loads_without_error() -> None:
    actions = load_whitelist(ROOT)
    require(len(actions) > 0, "A whitelist deveria ter pelo menos uma ação.")
    require(
        all(action.status.startswith("[") for action in actions.values()),
        "Toda ação precisa de um status entre colchetes.",
    )


def test_truth_table_loads_without_error() -> None:
    rows = load_truth_table(ROOT)
    require(len(rows) > 0, "A tabela verdade deveria ter pelo menos uma linha.")
    require(
        all("Pacote A360" in row and "Status" in row for row in rows),
        "Toda linha precisa das colunas Pacote A360 e Status.",
    )


def test_every_truth_table_action_exists_in_whitelist() -> None:
    actions = load_whitelist(ROOT)
    rows = load_truth_table(ROOT)
    missing = sorted(
        {
            name
            for row in rows
            if (name := truth_table_action_name(row)) is not None and name not in actions
        }
    )
    require(not missing, f"Ações citadas na tabela verdade mas ausentes na whitelist: {missing}")


def _robin_block_after_heading(text: str, name: str) -> str:
    """Pega o primeiro bloco de código robin que vem depois da seção `### name`."""
    heading = f"### `{name}`"
    start = text.index(heading)
    block_start = text.index("```robin", start) + len("```robin")
    block_end = text.index("```", block_start)
    return text[block_start:block_end]


def test_validated_actions_have_a_real_snippet_not_the_generic_placeholder() -> None:
    """`[validado PAD: rodou]` só existe depois de execução real confirmada
    (ver ADR-025/Fase 25) — mas o status sozinho não garante que o snippet
    foi de fato trocado; essa checagem cruza as duas coisas."""
    path = ROOT / "reference" / "robin-actions.md"
    text = path.read_text(encoding="utf-8")
    actions = load_whitelist(ROOT)
    validated = [name for name, action in actions.items() if action.validated]
    require(validated, "Pelo menos uma ação validada é esperada neste ponto do projeto.")
    for name in validated:
        block = _robin_block_after_heading(text, name)
        require(
            "TODO reflow: colar aqui" not in block,
            f"{name} está [validado PAD: rodou] mas o snippet ainda é o placeholder genérico.",
        )


# Instruções da linguagem: não são registros da KB (ADR-029).
LANGUAGE_STATEMENTS = frozenset(
    {
        "SET",
        "IF",
        "LOOP FOREACH",
        "LOOP FROM",
        "LOOP WHILE",
        "**REGION",
        "ON ERROR",
        "BLOCK",
        "CALL",
    }
)
KB_STATUS = "[colado KB: PAD 2.73, não rodado nesta instalação]"


def _sections(text: str) -> dict[str, str]:
    """`{cabeçalho: corpo da seção até o próximo ### ou ##}`."""
    sections: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("### `") and line.rstrip().endswith("`"):
            current = line.strip()[5:-1]
            sections[current] = ""
        elif line.startswith("## "):
            current = None
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def _robin_blocks(body: str) -> list[str]:
    blocks, rest = [], body
    while "```robin" in rest:
        start = rest.index("```robin") + len("```robin")
        end = rest.index("```", start)
        blocks.append(rest[start:end].strip())
        rest = rest[end + 3 :]
    return blocks


def test_every_action_heading_is_a_real_kb_id_or_a_language_statement() -> None:
    """Pega o erro que motivou o ADR-029: nome "plausível" que não existe no PAD."""
    kb = load_action_kb(ROOT)
    invented = sorted(
        name
        for name, action in load_whitelist(ROOT).items()
        if name not in LANGUAGE_STATEMENTS
        and name.lower() not in kb
        and not action.status.startswith("[não validado")
    )
    require(not invented, f"Ação com status de sintaxe real mas ausente da KB: {invented}")


def test_kb_anchored_snippets_use_the_heading_id_and_only_its_arguments() -> None:
    """Snippet `colado KB` de uma ação começa pelo id do cabeçalho e só usa argumentos
    e saídas que esse seletor tem na KB (argumento de seletor irmão = "Unknown argument")."""
    kb = load_action_kb(ROOT)
    text = (ROOT / "reference" / "robin-actions.md").read_text(encoding="utf-8")
    sections = _sections(text)
    problems: list[str] = []
    for name, body in sections.items():
        if name in LANGUAGE_STATEMENTS or name.lower() not in kb:
            continue
        record = kb[name.lower()]
        for block in _robin_blocks(body):
            if "\n" in block:
                continue  # forma em várias linhas do analista: preservada, ver ADR-029
            if not block.startswith(record.action_id + " ") and block != record.action_id:
                problems.append(f"{name}: snippet não começa pelo id ({block[:50]})")
                continue
            for arg in re.findall(r"(?:^|\s)(\w+):\s", _strip_strings(block)):
                if arg.lower() not in record.input_names:
                    problems.append(f"{name}: argumento {arg} não existe nesse seletor")
            for out in re.findall(r"(\w+)=>", block):
                if out.lower() not in record.output_names:
                    problems.append(f"{name}: saída {out} não existe nesse seletor")
    require(not problems, "\n".join(problems))


def _strip_strings(line: str) -> str:
    return re.sub(r"\$'''.*?'''", '""', line)


def test_kb_status_is_used_and_no_snippet_puts_percent_outside_a_string() -> None:
    """Regra `pct-outside-string` da KB: `Instance: %var%` derruba a colagem inteira."""
    text = (ROOT / "reference" / "robin-actions.md").read_text(encoding="utf-8")
    require(KB_STATUS in text, "status da KB ausente da whitelist")
    offenders = [
        line
        for body in _sections(text).values()
        for block in _robin_blocks(body)
        for line in block.splitlines()
        if "%" in _strip_strings(line) and "'''" not in line
    ]
    require(not offenders, f"% fora de string: {offenders}")
