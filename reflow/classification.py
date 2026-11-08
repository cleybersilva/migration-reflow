"""Gate determinístico da classificação: contrato, evidência e coerência com o inventário.

Não julga o mérito do veredito (isso é do agent, do revisor e do analista): confere o que dá
para provar sem LLM. Roda dentro de `phase-done 03-classification` e de
`checkpoint --approve`, os pontos por onde todo harness passa, e em `classify-check`.

Erro bloqueia; aviso só informa. O resultado nunca aprova nada sozinho (AGENTS.md).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

VERDICTS = ("PAD", "PARTIAL", "NOT_PAD")
AGREEMENTS = ("concorda", "diverge")
CRITERIA = tuple(f"{group}{n}" for group in "CNA" for n in range(1, 6))
# Projetos do golden set (reflow classify-eval): ficam fora de lote, relatório e gates.
EVAL_PREFIX = "eval-"

_CITATION_RE = re.compile(
    r"(?<![\w/.\\-])((?:[\w.-]+/)*[\w.-]+\.(?:json|md|py|cs|vb|robin)):(\d+)(?:-(\d+))?"
)
ALERT_ID_RE = re.compile(r"A(\d+)\b")
_VERDICT_TOKEN_RE = re.compile(r"\b(?:NOT_PAD|PARTIAL|PAD)\b")


@dataclass(frozen=True)
class Issue:
    level: str  # "erro" ou "aviso"
    file: str
    message: str


def parse_frontmatter(text: str) -> dict[str, str | list[str]] | None:
    """Subconjunto de YAML que o contrato usa: `chave: valor`, `chave: []` e lista de itens.

    Escalar fica cru de propósito: `verdict: "NOT_PAD"` não pode virar `NOT_PAD` aqui, porque
    `report.read_verdict` lê as aspas junto e o bloqueio do checkpoint deixaria de valer.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    data: dict[str, str | list[str]] = {}
    key = ""
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if line[0] in " \t":
            current = data.get(key)
            if not isinstance(current, list):
                return None
            stripped = line.strip()
            if stripped.startswith("- "):
                current.append(stripped[2:].strip().strip('"'))
            elif current:  # item longo quebrado em mais de uma linha
                current[-1] = f"{current[-1]} {stripped.strip(chr(34))}"
            else:
                return None
            continue
        name, separator, value = line.partition(":")
        if not separator or name in data:
            return None
        key, value = name.strip(), value.strip()
        data[key] = [] if value in ("", "[]") else value
    return data


@dataclass(frozen=True)
class _Context:
    root: Path
    project: str
    source_type: str
    files: frozenset[str]
    facts: frozenset[tuple[str, int]]
    inventory: dict

    @property
    def out_dir(self) -> Path:
        return self.root / "output" / self.project


def _load_context(root: Path, project: str) -> _Context | None:
    path = root / "output" / project / "01-inventory" / "inventory.json"
    if not path.is_file():
        return None
    inventory = json.loads(path.read_text(encoding="utf-8"))
    facts = {
        (item["file"], item["line"])
        for value in inventory.values()
        if isinstance(value, list)
        for item in value
        if isinstance(item, dict) and "file" in item and "line" in item
    }
    return _Context(
        root,
        project,
        inventory.get("source_type", ""),
        frozenset(inventory.get("files", [])),
        frozenset(facts),
        inventory,
    )


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _citation_error(ctx: _Context, cited: str, start: int, end: int) -> str | None:
    """Motivo pelo qual a citação não se sustenta, ou None."""
    if start < 1 or end < start:
        return "intervalo de linhas inválido"
    source = cited.removeprefix(f"input/{ctx.project}/")
    if source in ctx.files:
        if ctx.source_type == "a360" and source.lower().endswith(".json"):
            # No A360 a "linha" é o índice do nó na pré-ordem, não a linha física do JSON:
            # só o inventário prova que aquele nó existe.
            if (source, start) not in ctx.facts or (source, end) not in ctx.facts:
                return "nó não existe no inventário"
            return None
        path = ctx.root / "input" / ctx.project / source
        # Legado real não é versionado: sem a entrada, vale a presença no inventário.
        if path.is_file() and end > _line_count(path):
            return "linha além do fim do arquivo"
        return None
    candidates = (
        ctx.out_dir / cited,
        ctx.out_dir / "01-inventory" / cited,
        ctx.out_dir / "02-docs" / cited,
        ctx.out_dir / "03-classification" / cited,
        ctx.root / cited,
    )
    for path in candidates:
        if path.is_file():
            return "linha além do fim do arquivo" if end > _line_count(path) else None
    return "arquivo não encontrado"


def _citations(text: str) -> list[tuple[str, str, int, int]]:
    found = []
    for match in _CITATION_RE.finditer(text):
        start = int(match[2])
        found.append((match[0], match[1], start, int(match[3]) if match[3] else start))
    return found


def _check_citations(ctx: _Context, text: str, file: str) -> list[Issue]:
    citations = _citations(text)
    if not citations:
        return [Issue("erro", file, "nenhuma evidência arquivo:linha citada")]
    issues = []
    for raw in sorted({c[0] for c in citations}):
        match = next(c for c in citations if c[0] == raw)
        if reason := _citation_error(ctx, match[1], match[2], match[3]):
            issues.append(Issue("erro", file, f"evidência `{raw}`: {reason}"))
    return issues


def _check_alerts(ctx: _Context, alerts: list[str], file: str) -> tuple[list[Issue], set[str]]:
    issues: list[Issue] = []
    found: set[str] = set()
    for alert in alerts:
        if not _citations(alert):
            issues.append(Issue("erro", file, f"alerta sem evidência arquivo:linha: {alert[:60]}"))
        match = ALERT_ID_RE.match(alert)
        if match:
            if f"A{match[1]}" in CRITERIA:
                found.add(f"A{match[1]}")
            else:
                issues.append(Issue("erro", file, f"alerta fora de A1-A5: A{match[1]}"))
    return issues, found


def _check_inventory_coherence(
    ctx: _Context, verdict: str, alert_ids: set[str], file: str
) -> list[Issue]:
    """Fatos que o inventário prova e o veredito não pode contradizer."""
    issues = []
    is_a360 = ctx.source_type == "a360"
    ui = ctx.inventory.get("ui_interactions") or []
    unknown = ctx.inventory.get("unknown_commands") or []
    if is_a360 and ctx.inventory.get("credentials") and "A4" not in alert_ids:
        issues.append(Issue("erro", file, "inventário tem CredentialVault e falta o alerta A4"))
    if verdict == "PAD" and not ui and not unknown:
        # Fora do A360 os extractors não registram UI: lá, ausência não prova nada.
        level = "erro" if is_a360 else "aviso"
        issues.append(Issue(level, file, "veredito PAD sem nenhuma interação de UI no inventário"))
    total = sum(
        len(ctx.inventory.get(key) or [])
        for key in ("ui_interactions", "http_calls", "data_sources")
    )
    if verdict == "NOT_PAD" and total and len(ui) * 2 > total:
        issues.append(
            Issue("aviso", file, "NOT_PAD com UI majoritária: confirmar a regra de nuvem/API")
        )
    return issues


def check_classification(root: Path, project: str) -> list[Issue]:
    file = f"output/{project}/03-classification/classification.md"
    path = root / file
    if not path.is_file():
        return [Issue("erro", file, "classificação ausente")]
    ctx = _load_context(root, project)
    if ctx is None:
        return [Issue("erro", file, "inventário ausente: sem ele não há o que conferir")]
    text = path.read_text(encoding="utf-8")
    data = parse_frontmatter(text)
    if data is None:
        return [Issue("erro", file, "frontmatter ausente ou inválido")]

    verdict = data.get("verdict")
    if verdict not in VERDICTS:
        return [Issue("erro", file, f"verdict inválido: {verdict!r} (sem aspas, um de {VERDICTS})")]

    issues: list[Issue] = []
    use_cases = data.get("pad_use_cases")
    alerts = data.get("alerts")
    if not isinstance(use_cases, list) or not isinstance(alerts, list):
        return [Issue("erro", file, "pad_use_cases e alerts precisam ser listas")]
    if verdict == "NOT_PAD" and use_cases:
        issues.append(Issue("erro", file, "NOT_PAD não pode ter pad_use_cases"))
    if verdict != "NOT_PAD" and not use_cases:
        issues.append(Issue("erro", file, f"{verdict} sem nenhum pad_use_cases"))

    body = text[text.find("\n---", 4) + 4 :]
    missing = [c for c in CRITERIA if not re.search(rf"\b{c}\b", body)]
    if missing:
        issues.append(Issue("erro", file, f"critérios não avaliados: {', '.join(missing)}"))
    for line in body.splitlines():
        if line.startswith("**Veredito"):
            tokens = _VERDICT_TOKEN_RE.findall(line)
            if tokens and verdict not in tokens:
                issues.append(Issue("erro", file, f"corpo contradiz o frontmatter: {line[:60]}"))

    alert_issues, alert_ids = _check_alerts(ctx, alerts, file)
    issues.extend(alert_issues)
    issues.extend(_check_inventory_coherence(ctx, verdict, alert_ids, file))
    issues.extend(_check_citations(ctx, text, file))
    return issues


def check_review(root: Path, project: str) -> list[Issue]:
    file = f"output/{project}/03-classification/review.md"
    path = root / file
    if not path.is_file():
        return [Issue("aviso", file, "sem segunda opinião (rode reflow-classify-review)")]
    ctx = _load_context(root, project)
    if ctx is None:
        return [Issue("erro", file, "inventário ausente: sem ele não há o que conferir")]
    text = path.read_text(encoding="utf-8")
    data = parse_frontmatter(text)
    if data is None:
        return [Issue("erro", file, "frontmatter ausente ou inválido")]
    original = data.get("original_verdict")
    reviewed = data.get("reviewed_verdict")
    agreement = data.get("agreement")
    if original not in VERDICTS or reviewed not in VERDICTS or agreement not in AGREEMENTS:
        return [Issue("erro", file, "original_verdict, reviewed_verdict ou agreement inválido")]

    issues: list[Issue] = []
    classification = root / f"output/{project}/03-classification/classification.md"
    current = None
    if classification.is_file():
        current = (parse_frontmatter(classification.read_text(encoding="utf-8")) or {}).get(
            "verdict"
        )
    if original != current:
        issues.append(Issue("erro", file, f"desatualizada: revisou {original}, vigente {current}"))
    if (agreement == "concorda") != (original == reviewed):
        issues.append(Issue("erro", file, f"agreement {agreement} com {original} x {reviewed}"))
    if "Minha análise" not in text:
        issues.append(Issue("erro", file, "falta a seção Minha análise"))
    if agreement == "diverge":
        if "Por que divirjo" not in text:
            issues.append(Issue("erro", file, "diverge sem a seção Por que divirjo"))
        issues.append(Issue("aviso", file, f"DIVERGÊNCIA: {original} x {reviewed}"))
    issues.extend(_check_citations(ctx, text, file))
    return issues


def check_project(root: Path, project: str) -> list[Issue]:
    return check_classification(root, project) + check_review(root, project)


def classified_projects(root: Path) -> list[str]:
    output = root / "output"
    if not output.is_dir():
        return []
    return sorted(
        path.parent.parent.name
        for path in output.glob("*/03-classification/classification.md")
        if not path.parent.parent.name.startswith(EVAL_PREFIX)
    )


def errors(issues: list[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.level == "erro"]
