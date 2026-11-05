"""Checagem estática da sintaxe Robin de um `Main.robin`, antes de colar no PAD.

Implementação própria das regras documentadas na PAD Robin Action KB vendorizada
(`reference/vendor/pad-robin-kb/robin-rules.json`, CC BY 4.0), cada uma provada por
colagens reais no PAD Designer 2.72/2.73 (`probe-corpus.json`). A maioria dessas falhas
é **silenciosa**: o PAD descarta a colagem inteira, sem erro visível, por causa de uma
linha só. Por isso o lint reprova cedo (ADR-029, que revoga o ADR-012).

O texto é só lido: nada é executado, importado ou interpretado além de regex e
varredura de caracteres. Falso positivo é preferível a falso negativo (falhar de forma
restritiva, `AGENTS.md`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .kb import KbAction

# Palavras reservadas do PAD: nunca nome de variável nem de propriedade (regra
# `keywords-as-names`). `Mail.From` derruba a colagem; o certo é `Mail['From']`.
KEYWORDS = frozenset(
    {
        "from", "to", "step", "end", "in", "then", "if", "else", "loop", "foreach",
        "while", "set", "wait", "next", "exit", "label", "goto", "call", "case",
        "default", "switch", "block", "error", "on", "not", "and", "or", "mod",
        "true", "false", "global", "disable", "function", "throw",
    }
)  # fmt: skip
# Nomes que aparecem em expressão sem serem variável.
NOT_VARIABLES = frozenset({"and", "or", "not", "mod", "true", "false", "appmask", "imgrepo"})
# Argumentos cujo literal não pode ser um segredo escrito no flow.
SENSITIVE_ARGUMENT_RE = re.compile(r"(?i)(password|passphrase|secret|apikey|api_key|token)$")
# Elementos de UI de exemplo da KB: nunca existem no repositório de UI do flow.
KB_PLACEHOLDER_ELEMENT_RE = re.compile(r"KB Test (Window|Page)")
# Variáveis `in_` são entradas do flow, declaradas no designer (convenção do reflow).
FLOW_INPUT_PREFIX = "in_"

_ID = r"[^\W\d][\w]*"
_SET_RE = re.compile(r"^SET\s+(\S+)\s+TO\b(.*)$", re.IGNORECASE)
_FOREACH_RE = re.compile(r"^LOOP\s+FOREACH\s+(\S+)\s+IN\b(.*)$", re.IGNORECASE)
_FROM_RE = re.compile(r"^LOOP\s+(\S+)\s+FROM\b(.*)$", re.IGNORECASE)
_WRAPPED_RE = re.compile(r"^(IF|WAIT|LOOP WHILE)\s*\((.*)\)(?:\s+(THEN|FOR\s+.+))?$", re.I)
_ACTION_HEAD_RE = re.compile(r"^([A-Za-z]\w*)\.[A-Za-z]\w*")
_ARG_RE = re.compile(r"(?:^|\s)(\w+)\s?:\s?(?=\S)")
_OUT_RE = re.compile(rf"(?:^|\s)(\w+)\s?=>\s?({_ID})")
_ENUM_RE = re.compile(r"\b([A-Za-z]\w*)\.([A-Za-z]\w*)\.(\w+)\b")
_EXPR_STRING_RE = re.compile(r"'(?:\\.|[^'\\])*'")
_IDENT_RE = re.compile(rf"(?<![.\w])({_ID})(?![\w])(?!\s*\()")
_STRING_SLOT_RE = re.compile(r'"\d+"')
_PROPERTY_RE = re.compile(rf"\b({_ID}(?:\[[^\]]*\])*)\.({_ID})")


@dataclass
class RobinIssue:
    line: int
    code: str
    message: str


@dataclass
class _Statement:
    line: int
    bare: str  # texto com cada string `$'''...'''` trocada por `""`
    comment: bool = False
    strings: list[tuple[int, str]] = field(default_factory=list)  # (linha, conteúdo)
    exprs: list[tuple[int, str]] = field(default_factory=list)  # `%...%` dentro de string


def _scan(text: str) -> tuple[list[_Statement], list[RobinIssue]]:
    """Quebra o texto em instruções. String `$'''...'''` pode ter várias linhas; dentro
    dela `\\` escapa o próximo caractere, `%...%` é expressão e `%%` é `%` literal."""
    issues: list[RobinIssue] = []
    stmts: list[_Statement] = []
    line, i, n = 1, 0, len(text)
    cur: _Statement | None = None

    def finish() -> None:
        nonlocal cur
        if cur is not None and cur.bare.strip():
            cur.bare = cur.bare.strip()
            stmts.append(cur)
        cur = None

    while i < n:
        c = text[i]
        if c == "\r" and text[i + 1 : i + 2] == "\n":
            i += 1
            continue
        if c in "\r\n":  # o PAD também aceita quebra só com CR
            finish()
            line += 1
            i += 1
            continue
        if cur is None or not cur.bare.strip():
            rest = text[i:].lstrip(" \t")
            skip = len(text) - i - len(rest)
            if rest.startswith("# [ControlRepository]"):
                break  # daqui em diante é o JSON do repositório de UI, não Robin
            if rest.startswith("/#"):
                end = text.find("#/", i + skip + 2)
                stop = n if end < 0 else end + 2
                stmts.append(_Statement(line, "#", comment=True))
                line += text.count("\n", i, stop)
                i = stop
                cur = None
                continue
            if rest.startswith("#"):
                stmts.append(_Statement(line, "#", comment=True))
                nl = text.find("\n", i)
                i = n if nl < 0 else nl
                cur = None
                continue
        if c == "#" and cur is not None and cur.bare[-1:].isspace():
            nl = text.find("\n", i)  # comentário no fim da linha vira linha própria
            i = n if nl < 0 else nl
            continue
        if text.startswith("$'''", i):
            if cur is None:
                cur = _Statement(line, "")
            start_line, i = line, i + 4
            content_start, closed = i, False
            while i < n:
                d = text[i]
                if d == "\n":
                    line += 1
                    i += 1
                    continue
                if d == "\\":
                    if text[i + 1 : i + 2] == "%":
                        issues.append(
                            RobinIssue(
                                line,
                                "robin_barra_antes_de_percent",
                                "`\\%` dentro de string: o PAD perde o `%`. Caminho antes de "
                                "variável é `\\\\%Var%`; `%` literal é `%%`",
                            )
                        )
                    i += 2
                    continue
                if text.startswith("''''", i):
                    issues.append(
                        RobinIssue(
                            line,
                            "robin_apostrofo_sem_escape",
                            "string não pode terminar em apóstrofo: escreva `\\'`",
                        )
                    )
                    cur.strings.append((start_line, text[content_start : i + 1]))
                    i, closed = i + 4, True
                    break
                if text.startswith("'''", i):
                    cur.strings.append((start_line, text[content_start:i]))
                    i, closed = i + 3, True
                    break
                if d == "'":
                    issues.append(
                        RobinIssue(
                            line,
                            "robin_apostrofo_sem_escape",
                            "apóstrofo dentro de `$'''...'''` derruba a colagem: escreva `\\'`",
                        )
                    )
                    i += 1
                    continue
                if d == "%":
                    if text[i + 1 : i + 2] == "%":
                        i += 2
                        continue
                    j, quoted = i + 1, False
                    while j < n and not (text[j] == "%" and not quoted):
                        if not quoted and text.startswith("'''", j):
                            break
                        if text[j] == "'":
                            quoted = not quoted
                        j += 1
                    if j >= n or text[j] != "%":
                        issues.append(
                            RobinIssue(
                                line,
                                "robin_percent_solto",
                                "`%` solto dentro de string derruba a colagem: `%` literal é `%%`",
                            )
                        )
                        i += 1
                        continue
                    cur.exprs.append((line, text[i + 1 : j]))
                    line += text.count("\n", i, j)
                    i = j + 1
                    continue
                i += 1
            if not closed:
                issues.append(
                    RobinIssue(
                        start_line,
                        "robin_string_sem_fechamento",
                        "string nunca fecha (`\\'''` escapa as aspas; para terminar em barra, "
                        "use `\\\\'''`)",
                    )
                )
            if not closed:
                cur.strings.append((start_line, text[content_start:i]))
            cur.bare += f'"{len(cur.strings) - 1}"'
            continue
        if cur is None:
            cur = _Statement(line, "")
        cur.bare += c
        i += 1
    finish()
    return stmts, issues


def _parse_action(bare: str) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Id, argumentos `(nome, valor)` e saídas `(nome, variável)` de uma ação."""
    action_id = bare.split(" ")[0]
    rest = bare[len(action_id) :]
    outputs = [(m.group(1), m.group(2)) for m in _OUT_RE.finditer(rest)]
    no_out = _OUT_RE.sub(" ", rest)
    marks = list(_ARG_RE.finditer(no_out))
    args = []
    for k, mark in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(no_out)
        args.append((mark.group(1), no_out[mark.end() : end].strip()))
    return action_id, args, outputs


class _Checker:
    def __init__(self, kb: dict[str, KbAction], text: str) -> None:
        self.kb = kb
        self.modules = frozenset(a.action_id.split(".")[0].lower() for a in kb.values())
        self.stmts, self.issues = _scan(text)
        self.defined: set[str] = set()
        self.reported: set[str] = set()
        self.action_lines = 0
        self._group_action: KbAction | None = None
        self.used_actions: list[tuple[int, str]] = []

    def err(self, line: int, code: str, message: str) -> None:
        self.issues.append(RobinIssue(line, code, message))

    # -- nomes e variáveis ---------------------------------------------------------
    def _is_action_call(self, text: str) -> bool:
        match = _ACTION_HEAD_RE.match(text)
        return bool(match) and match.group(1).lower() in self.modules

    def _strip_enums(self, text: str) -> str:
        return _ENUM_RE.sub(
            lambda m: " " if m.group(1).lower() in self.modules else m.group(0), text
        )

    def _collect_definitions(self) -> None:
        for st in self.stmts:
            if st.comment:
                continue
            bare = re.sub(r"^DISABLE\s+", "", st.bare, flags=re.I)
            for regex in (_SET_RE, _FOREACH_RE, _FROM_RE):
                match = regex.match(bare)
                if match:
                    self.defined.add(match.group(1).lower())
            for match in re.finditer(rf"=>\s?({_ID})", bare):
                self.defined.add(match.group(1).lower())

    def _var_name(self, line: int, name: str, where: str) -> None:
        if not re.match(rf"^{_ID}$", name):
            self.err(line, "robin_nome_invalido", f"{where} `{name}` tem que começar por letra")
        elif name.lower() in KEYWORDS:
            self.err(
                line,
                "robin_palavra_reservada",
                f"{where} `{name}` é palavra reservada do PAD e derruba a colagem",
            )

    def _reserved_properties(self, line: int, text: str) -> None:
        for match in _PROPERTY_RE.finditer(self._strip_enums(text)):
            if match.group(2).lower() in KEYWORDS:
                self.err(
                    line,
                    "robin_palavra_reservada",
                    f"`{match.group(1)}.{match.group(2)}`: `{match.group(2)}` é palavra "
                    f"reservada; escreva `{match.group(1)}['{match.group(2)}']`",
                )

    def _uses(self, line: int, text: str) -> None:
        cleaned = _STRING_SLOT_RE.sub(" ", self._strip_enums(_EXPR_STRING_RE.sub("''", text)))
        for match in _IDENT_RE.finditer(cleaned):
            name = match.group(1).lower()
            if (
                name in NOT_VARIABLES
                or name in self.defined
                or name in self.reported
                or name.startswith(FLOW_INPUT_PREFIX)
            ):
                continue
            self.reported.add(name)
            self.err(
                line,
                "robin_variavel_indefinida",
                f"variável `{match.group(1)}` é usada mas nunca definida no flow "
                f"(PAD: \"Variable '{match.group(1)}' doesn't exist\")",
            )

    # -- ação ----------------------------------------------------------------------
    def _check_action(self, st: _Statement, bare: str) -> KbAction | None:
        self.action_lines += 1
        action_id, args, outputs = _parse_action(bare)
        record = self.kb.get(action_id.lower())
        self.used_actions.append((st.line, record.action_id if record else action_id))
        if record is None:
            self.err(st.line, "robin_acao_desconhecida", f"ação `{action_id}` não existe na KB")
            return None
        seen: set[str] = set()
        for name, value in args:
            if name.lower() in seen:
                self.err(st.line, "robin_argumento_repetido", f"{action_id}: `{name}` duas vezes")
            seen.add(name.lower())
            if name.lower() not in record.input_names:
                hint = [
                    sibling
                    for sibling in record.sibling_selectors
                    if (other := self.kb.get(sibling.lower())) and name.lower() in other.input_names
                ]
                tip = f" (existe em {', '.join(hint)})" if hint else ""
                self.err(
                    st.line,
                    "robin_argumento_desconhecido",
                    f"{action_id} não tem o argumento `{name}`{tip}",
                )
                continue
            self._check_value(st, record, name, value)
        for name, variable in outputs:
            if name.lower() not in record.output_names:
                self.err(st.line, "robin_saida_desconhecida", f"{action_id} não tem saída `{name}`")
            self._var_name(st.line, variable, "variável de saída")
        if record.needs_ui_selector and KB_PLACEHOLDER_ELEMENT_RE.search(bare):
            self.err(
                st.line,
                "robin_elemento_ui_de_exemplo",
                f"{action_id} usa o elemento de exemplo da KB; grave o elemento real no "
                "designer ou deixe o passo como `# TODO reflow`",
            )
        self._reserved_properties(st.line, bare[len(action_id) :])
        return record

    def _check_value(self, st: _Statement, record: KbAction, name: str, value: str) -> None:
        param = next(p for p in record.input_params if p["name"].lower() == name.lower())
        enum_values = [v.lower() for v in param.get("enumValues") or ()]
        enum = re.fullmatch(r"([A-Za-z]\w*)\.([A-Za-z]\w*)\.(\w+)", value)
        if enum_values and enum:
            if enum.group(3).lower() not in enum_values:
                self.err(
                    st.line,
                    "robin_enum_invalido",
                    f"{record.action_id} {name}: `{enum.group(3)}` não é valor de "
                    f"`{enum.group(1)}.{enum.group(2)}`",
                )
            return
        if enum_values and value.lower() in enum_values and value.lower() not in self.defined:
            self.reported.add(value.lower())
            self.err(
                st.line,
                "robin_enum_sem_modulo",
                f"{record.action_id} {name}: enum precisa de módulo e tipo "
                f"(`Modulo.{param.get('type')}.{value}`)",
            )
            return
        slot = re.fullmatch(r'"(\d+)"', value)
        literal = st.strings[int(slot.group(1))][1] if slot else ""
        if SENSITIVE_ARGUMENT_RE.search(name) and re.sub(r"%[^%]*%", "", literal).strip():
            self.err(
                st.line,
                "robin_segredo_literal",
                f"{record.action_id} {name}: segredo não vai como literal no flow; use uma "
                "variável (entrada sensível ou cofre)",
            )
        self._uses(st.line, value)

    # -- fluxo ---------------------------------------------------------------------
    def run(self) -> list[RobinIssue]:
        self._collect_definitions()
        stack: list[str] = []  # "if" | "loop" | "switch" | "block" | "handler"
        pending_block_handler = False
        last_action: KbAction | None = None
        had_action = False
        group_default = False

        for k, st in enumerate(self.stmts):
            if st.comment:
                continue
            for line, expr in st.exprs:
                self._reserved_properties(line, expr)
                self._uses(line, expr)
            bare = re.sub(r"^DISABLE\s+", "", st.bare, flags=re.I)
            upper = bare.upper()
            prev_action, prev_had_action = last_action, had_action
            last_action, had_action = None, False
            in_handler = bool(stack) and stack[-1] == "handler"

            if "%" in bare:
                self.err(
                    st.line,
                    "robin_percent_fora_de_string",
                    "`%...%` fora de string derruba a colagem: escreva a expressão nua "
                    "(`Instance: X`, `SET A TO B + 1`, `IF N = 5 THEN`)",
                )
            if re.search(r"\S\s+SET\s+\w+\s+TO\s", bare, re.I):
                self.err(st.line, "robin_duas_instrucoes", "duas instruções numa linha só")

            if bare.startswith("//"):
                self.err(
                    st.line,
                    "robin_comentario_invalido",
                    "`//` não é comentário Robin e derruba a colagem: use `# texto`",
                )
                continue
            if bare.startswith("@@"):
                nxt = self.stmts[k + 1] if k + 1 < len(self.stmts) else None
                if not re.match(r"^@@copilotGeneratedAction\b", bare, re.I):
                    self.err(st.line, "robin_cabecalho", "linha `@@` derruba a colagem")
                elif nxt is None or nxt.comment:
                    self.err(st.line, "robin_cabecalho", "`@@` tem que vir logo antes de ação")
                continue
            if re.match(r"^(IMPORT|@SENSITIVE)\b", bare, re.I):
                self.err(st.line, "robin_cabecalho", "cabeçalho de arquivo derruba a colagem")
                continue
            if re.match(r"^\*\*(END)?REGION\b", bare, re.I):
                continue
            if re.match(r"^(END\s+)?REGION\b", bare, re.I):
                self.err(
                    st.line,
                    "robin_regiao_invalida",
                    "região é `**REGION Nome` / `**ENDREGION`; `REGION` derruba a colagem",
                )
                continue
            if re.match(r"^EXIT\s+FUNCTION\b", bare, re.I):
                self.err(
                    st.line,
                    "robin_exit_function",
                    "`EXIT FUNCTION` só funciona dentro de um subflow, não no Main",
                )
                continue
            if re.match(r"^(END\s+)?FUNCTION\b", bare, re.I):
                self.err(
                    st.line,
                    "robin_definicao_de_subflow",
                    "`FUNCTION ... END FUNCTION` não cola: crie o subflow no designer e cole "
                    "o corpo dentro dele",
                )
                continue

            if in_handler and not re.match(
                r"^(SET |CALL |GOTO |THROW ERROR\b|END\b|ON (BLOCK )?ERROR\b)", bare, re.I
            ):
                self.err(
                    st.line,
                    "robin_instrucao_no_tratador",
                    "dentro de `ON ERROR`/`ON BLOCK ERROR` só `SET`, `CALL`, `GOTO` e "
                    "`THROW ERROR`: marque uma flag e teste depois do bloco",
                )

            if re.match(r"^END\b", bare, re.I):
                if not stack:
                    self.err(st.line, "robin_end_sem_abertura", "`END` sem bloco aberto")
                else:
                    stack.pop()
                continue
            if re.match(r"^ON BLOCK ERROR\b", bare, re.I):
                named_case = re.match(r"^ON BLOCK ERROR\s+(?!all\s*$)\S", bare, re.I)
                if named_case and not re.search(r"\bIsUserDefinedErrorCode:\s*True\b", bare, re.I):
                    self.err(
                        st.line,
                        "robin_on_block_error_nomeado",
                        "caso nomeado de `ON BLOCK ERROR` é para código próprio: "
                        "`ON BLOCK ERROR MeuErro IsUserDefinedErrorCode: True`",
                    )
                if in_handler:
                    continue  # outro caso do mesmo tratador, mesmo END
                if pending_block_handler:
                    stack.append("handler")
                    pending_block_handler = False
                else:
                    self.err(st.line, "robin_on_error_solto", "`ON BLOCK ERROR` fora de `BLOCK`")
                continue
            if re.match(r"^ON ERROR\s+GOTO\b", bare, re.I):
                self.err(
                    st.line,
                    "robin_on_error_goto",
                    "`ON ERROR GOTO` derruba a colagem: ponha `GOTO Rotulo` dentro do tratador",
                )
                continue
            if re.match(r"^ON ERROR\b", bare, re.I):
                continuing = in_handler
                if not continuing:
                    if not prev_had_action:
                        self.err(
                            st.line,
                            "robin_on_error_solto",
                            "`ON ERROR` tem que vir logo depois da ação que trata",
                        )
                    elif prev_action is not None and not prev_action.on_error:
                        self.err(
                            st.line,
                            "robin_on_error_nao_suportado",
                            f"{prev_action.action_id} não gera erro: `ON ERROR` nela é erro "
                            "de colagem e faz execução pela nuvem rejeitar o flow; use `BLOCK`",
                        )
                    stack.append("handler")
                    group_default = False
                    self._group_action = prev_action
                if re.match(r"^ON ERROR\s+REPEAT\b", bare, re.I):
                    if continuing:
                        self.err(st.line, "robin_on_error_ordem", "`ON ERROR REPEAT` vem primeiro")
                    continue
                named = re.match(rf"^ON ERROR\s+({_ID})\s*$", bare, re.I)
                action = self._group_action
                if named:
                    if group_default:
                        self.err(
                            st.line,
                            "robin_on_error_ordem",
                            "caso nomeado depois do `ON ERROR` genérico: nomeados primeiro",
                        )
                    if (
                        action is not None
                        and action.on_error
                        and named.group(1) not in action.errors
                    ):
                        listed = ", ".join(action.errors) or "nenhum"
                        self.err(
                            st.line,
                            "robin_erro_desconhecido",
                            f"{action.action_id} não declara `{named.group(1)}` "
                            f"(declara: {listed})",
                        )
                elif re.match(r"^ON ERROR\s*$", bare, re.I):
                    if group_default:
                        self.err(st.line, "robin_on_error_ordem", "dois `ON ERROR` genéricos")
                    group_default = True
                continue
            if re.match(r"^BLOCK\b", bare, re.I):
                stack.append("block")
                pending_block_handler = True
                continue
            pending_block_handler = False

            if re.match(r"^ELSE\s+IF\s*\(", bare, re.I) and self._is_action_call(
                re.sub(r"^ELSE\s+IF\s*\(", "", bare, flags=re.I)
            ):
                self.err(
                    st.line,
                    "robin_else_if_acao",
                    "`ELSE IF (Ação ...)` derruba a colagem: use `ELSE` com `IF (Ação) THEN` "
                    "aninhado",
                )
                continue
            if re.match(r"^(ELSE|ELSE IF .* THEN)$", bare, re.I):
                if not stack or stack[-1] != "if":
                    self.err(st.line, "robin_else_sem_if", "`ELSE` fora de um `IF`")
                cond = re.match(r"^ELSE IF (.*) THEN$", bare, re.I)
                if cond:
                    self._reserved_properties(st.line, cond.group(1))
                    self._uses(st.line, cond.group(1))
                continue
            if re.match(
                r"^(NEXT LOOP|EXIT LOOP|EXIT\b.*|THROW ERROR\b.*|LABEL \w+|GOTO \w+|CALL \w+.*)$",
                bare,
                re.I,
            ):
                continue
            if re.match(r"^WAIT\s+(?!\()", bare, re.I):
                self._uses(st.line, bare[4:])
                continue
            if re.match(r"^(CASE|DEFAULT)\b", bare, re.I):
                if not stack or stack[-1] != "switch":
                    self.err(st.line, "robin_case_sem_switch", "`CASE`/`DEFAULT` fora de `SWITCH`")
                if upper.startswith("CASE") and not re.match(
                    r"^CASE\s*(=|<>|>=|<=|>|<)", bare, re.I
                ):
                    self.err(
                        st.line,
                        "robin_case_invalido",
                        "`CASE` só aceita comparação (`CASE = x`, `<>`, `>`...)",
                    )
                continue
            if re.match(r"^SWITCH\b", bare, re.I):
                stack.append("switch")
                self._uses(st.line, bare[6:])
                continue
            match = re.match(r"^ERROR\s*=>\s*(\S+)", bare, re.I)
            if match:
                self._var_name(st.line, match.group(1), "variável")
                continue
            match = _SET_RE.match(bare)
            if match:
                self._var_name(st.line, match.group(1), "variável")
                self._reserved_properties(st.line, match.group(2))
                self._uses(st.line, match.group(2))
                continue
            match = _FOREACH_RE.match(bare)
            if match:
                stack.append("loop")
                self._var_name(st.line, match.group(1), "variável do laço")
                self._uses(st.line, match.group(2))
                continue
            match = _FROM_RE.match(bare)
            if match:
                stack.append("loop")
                self._var_name(st.line, match.group(1), "variável do laço")
                self._uses(st.line, re.sub(r"\b(TO|STEP)\b", " ", match.group(2), flags=re.I))
                continue

            wrapped = _WRAPPED_RE.match(bare)
            if wrapped:
                keyword, inner, tail = wrapped.group(1).upper(), wrapped.group(2), wrapped.group(3)
                if keyword == "IF":
                    stack.append("if")
                    if not tail or tail.upper() != "THEN":
                        self.err(st.line, "robin_if_sem_then", "`IF` precisa terminar em `THEN`")
                elif keyword == "LOOP WHILE":
                    stack.append("loop")
                if self._is_action_call(inner):
                    last_action, had_action = self._check_action(st, inner), True
                else:
                    self._reserved_properties(st.line, inner)
                    self._uses(st.line, inner)
                continue
            match = re.match(r"^LOOP\s+WHILE\s+(.*)$", bare, re.I)
            if match:
                stack.append("loop")
                self._reserved_properties(st.line, match.group(1))
                self._uses(st.line, match.group(1))
                continue
            match = re.match(r"^IF\s+(.*)\s+THEN$", bare, re.I)
            if match:
                stack.append("if")
                self._reserved_properties(st.line, match.group(1))
                self._uses(st.line, match.group(1))
                continue
            if self._is_action_call(bare):
                last_action, had_action = self._check_action(st, bare), True
                continue
            self.err(
                st.line,
                "robin_instrucao_desconhecida",
                f"não é instrução Robin nem ação da KB (derruba a colagem): `{bare[:60]}`. "
                "Pendência vira comentário `# TODO reflow: ...`",
            )

        if stack:
            last_line = self.stmts[-1].line if self.stmts else 1
            self.err(last_line, "robin_end_faltando", f"{len(stack)} bloco(s) aberto(s) sem `END`")
        return sorted(self.issues, key=lambda issue: issue.line)


def check_robin(text: str, kb: dict[str, KbAction]) -> list[RobinIssue]:
    """Erros de sintaxe Robin de `text`, em ordem de linha. Lista vazia = cola no PAD
    segundo as regras da KB (não prova que o flow faz o que deveria)."""
    return analyze_robin(text, kb)[0]


def analyze_robin(
    text: str, kb: dict[str, KbAction]
) -> tuple[list[RobinIssue], list[tuple[int, str]]]:
    """Como `check_robin`, mais as ações usadas: `(linha, actionId)` em ordem."""
    checker = _Checker(kb, text)
    return checker.run(), checker.used_actions
