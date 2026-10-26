"""Checkpoint humano vinculado aos hashes das entradas — `reflow checkpoint`.

Cobre o que a Fase 3 de segurança trouxe: a decisão só grava se as entradas
continuam idênticas às que foram extraídas e se já existe classificação —
nunca uma aprovação presumida, nunca gravação em cima de dado velho.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from reflow.cli import main

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    shutil.copytree(ROOT / "input" / "quote-scraper", tmp_path / "input" / "quote-scraper")
    return tmp_path


def _classify(workspace: Path, verdict: str = "PAD") -> None:
    folder = workspace / "output" / "quote-scraper" / "03-classification"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "classification.md").write_text(
        f"---\nverdict: {verdict}\n---\n\n# Classificação\n",
        encoding="utf-8",
    )


def _manifest(workspace: Path) -> dict:
    path = workspace / "output" / "quote-scraper" / "00-manifest.json"
    require(path.is_file(), "O manifesto tem que existir para este teste.")
    return json.loads(path.read_text(encoding="utf-8"))


def test_status_stays_pending_until_the_analyst_records_a_decision(workspace: Path) -> None:
    require(main(["extract", "quote-scraper"]) == 0, "extract deveria concluir sem erro.")
    require(
        main(["checkpoint", "quote-scraper"]) == 0,
        "status sem decisão é pendente, não erro.",
    )
    require(_manifest(workspace)["checkpoint"] is None, "Nenhum checkpoint nasce sozinho.")

    _classify(workspace)
    require(
        main(["checkpoint", "quote-scraper", "--approve"]) == 0,
        "Com classificação, o approve tem que ser gravado.",
    )
    checkpoint = _manifest(workspace)["checkpoint"]
    require(checkpoint["decision"] == "approved", "Decisão registrada: approved.")
    require(len(checkpoint["inputs_fingerprint"]) == 64, "O fingerprint é SHA256.")
    require(
        len(checkpoint["classification_sha256"]) == 64,
        "A classificação usada na decisão também fica amarrada por hash.",
    )
    require(checkpoint["recorded_at"].startswith("20"), "Data/hora da gravação em ISO.")
    require(
        main(["checkpoint", "quote-scraper", "--status"]) == 0,
        "status tem que continuar funcionando depois de gravado.",
    )


def test_approval_is_refused_when_inputs_changed_after_extract(workspace: Path) -> None:
    require(main(["extract", "quote-scraper"]) == 0, "extract deveria concluir sem erro.")
    _classify(workspace)
    (workspace / "input" / "quote-scraper" / "novo-arquivo.json").write_text("{}", encoding="utf-8")

    require(
        main(["checkpoint", "quote-scraper", "--approve"]) == 1,
        "Entrada nova depois da extração tem que recusar a aprovação.",
    )
    require(
        _manifest(workspace)["checkpoint"] is None,
        "Nada pode ser gravado em cima de dado que não foi extraído.",
    )
    require(
        main(["checkpoint", "quote-scraper", "--status"]) == 1,
        "status tem que acusar que o manifesto está velho.",
    )


def test_approval_is_refused_without_classification(workspace: Path) -> None:
    require(main(["extract", "quote-scraper"]) == 0, "extract deveria concluir sem erro.")
    require(
        main(["checkpoint", "quote-scraper", "--approve"]) == 1,
        "Sem 03-classification não existe decisão a registrar.",
    )
    require(_manifest(workspace)["checkpoint"] is None, "Nada gravado sem classificação.")


def test_reject_is_recorded_and_the_decision_can_be_substituted(workspace: Path) -> None:
    require(main(["extract", "quote-scraper"]) == 0, "extract deveria concluir sem erro.")
    _classify(workspace)

    require(
        main(["checkpoint", "quote-scraper", "--reject"]) == 0,
        "A rejeição é uma decisão humana válida.",
    )
    require(_manifest(workspace)["checkpoint"]["decision"] == "rejected", "Decisão: rejected.")

    require(
        main(["checkpoint", "quote-scraper", "--approve"]) == 0,
        "O analista pode mudar de decisão antes da conversão.",
    )
    require(_manifest(workspace)["checkpoint"]["decision"] == "approved", "Decisão virou approved.")


def test_approval_is_refused_for_not_pad(workspace: Path) -> None:
    require(main(["extract", "quote-scraper"]) == 0, "extract deveria concluir sem erro.")
    _classify(workspace, verdict="NOT_PAD")
    require(
        main(["checkpoint", "quote-scraper", "--approve"]) == 1,
        "NOT_PAD não tem conversão para aprovar.",
    )
    require(_manifest(workspace)["checkpoint"] is None, "Nada gravado para NOT_PAD.")
    require(
        main(["checkpoint", "quote-scraper", "--reject"]) == 0,
        "Rejeitar um NOT_PAD continua permitido — é o que o pipeline espera.",
    )


def test_re_extract_clears_the_previous_decision(workspace: Path) -> None:
    require(main(["extract", "quote-scraper"]) == 0, "extract deveria concluir sem erro.")
    _classify(workspace)
    require(
        main(["checkpoint", "quote-scraper", "--approve"]) == 0,
        "approve deveria ser gravado.",
    )

    require(main(["extract", "quote-scraper"]) == 0, "reextração deveria concluir sem erro.")
    require(
        _manifest(workspace)["checkpoint"] is None,
        "Reextração regrava o manifesto: a decisão antiga não sobrevive a entradas novas.",
    )


def test_status_without_a_manifest_is_an_error(workspace: Path) -> None:
    require(
        main(["checkpoint", "quote-scraper", "--status"]) == 1,
        "Sem extract não há manifesto — falhar de forma restritiva.",
    )
