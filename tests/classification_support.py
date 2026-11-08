"""Classificação mínima que passa no gate, para testes que precisam dela como pré-condição."""

from __future__ import annotations

from reflow.classification import CRITERIA


def classification_text(
    verdict: str = "PAD",
    evidence: str = "main.py:8",
    use_cases: list[str] | None = None,
    alerts: list[str] | None = None,
) -> str:
    if use_cases is None:
        use_cases = [] if verdict == "NOT_PAD" else [f"UC-01 ({evidence})"]

    def block(items: list[str]) -> str:
        return "".join(f'\n  - "{item}"' for item in items) if items else " []"

    table = "\n".join(f"| {criterion} | avaliado |" for criterion in CRITERIA)
    return (
        f"---\nverdict: {verdict}\npad_use_cases:{block(use_cases)}\n"
        f"alerts:{block(alerts or [])}\n---\n\n# Classificação\n\n"
        f"Evidência: `{evidence}`.\n\n{table}\n"
    )


def review_text(
    original: str = "PAD",
    reviewed: str = "PAD",
    agreement: str = "concorda",
    evidence: str = "main.py:8",
    extra: str = "",
) -> str:
    return (
        f"---\noriginal_verdict: {original}\nreviewed_verdict: {reviewed}\n"
        f"agreement: {agreement}\n---\n\n## Minha análise\n\nEvidência: `{evidence}`.\n{extra}"
    )
