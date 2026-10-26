"""Contenção de caminho — symlink/junction e UNC (reflow/security/paths.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reflow.security.paths import UnsafePathError, is_unc_path, is_unsafe_link, reject_unsafe_links
from tests.link_support import make_unsafe_link


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("\\\\server\\share\\arquivo.txt", True),
        ("//server/share/arquivo.txt", True),
        ("C:\\Users\\Public\\Documents\\arquivo.txt", False),
        ("arquivo.txt", False),
        ("", False),
        ("\\arquivo-local.txt", False),
    ],
)
def test_is_unc_path(raw: str, expected: bool) -> None:
    require(is_unc_path(raw) is expected, f"Classificação UNC errada para {raw!r}.")


def test_is_unsafe_link_false_for_regular_file_and_dir(tmp_path: Path) -> None:
    regular_dir = tmp_path / "project"
    regular_dir.mkdir()
    regular_file = regular_dir / "file.txt"
    regular_file.write_text("conteudo normal", encoding="utf-8")
    require(not is_unsafe_link(regular_dir), "Diretório normal não é link.")
    require(not is_unsafe_link(regular_file), "Arquivo normal não é link.")


def test_is_unsafe_link_true_for_missing_path() -> None:
    # Caminho que nunca existiu: nem symlink nem junction, mas também não é
    # "seguro" no sentido de inspecionável — is_symlink()/is_junction() do
    # pathlib devolvem False para inexistente, então o resultado aqui é
    # False mesmo, e quem chama trata isso via is_dir()/is_file() depois.
    require(not is_unsafe_link(Path("Z:/caminho/que/nao/existe")), "Sem crash em caminho ausente.")


def test_reject_unsafe_links_passes_for_clean_tree(tmp_path: Path) -> None:
    project = tmp_path / "clean"
    (project / "sub").mkdir(parents=True)
    (project / "sub" / "file.txt").write_text("ok", encoding="utf-8")
    reject_unsafe_links(project)  # não deve levantar


def test_reject_unsafe_links_passes_for_missing_or_file_root(tmp_path: Path) -> None:
    reject_unsafe_links(tmp_path / "nao-existe")  # não deve levantar
    single_file = tmp_path / "arquivo.txt"
    single_file.write_text("ok", encoding="utf-8")
    reject_unsafe_links(single_file)  # não deve levantar


def test_reject_unsafe_links_raises_when_root_is_a_junction(tmp_path: Path) -> None:
    target = tmp_path / "real-target"
    target.mkdir()
    link = tmp_path / "project"
    make_unsafe_link(link, target)
    with pytest.raises(UnsafePathError):
        reject_unsafe_links(link)


def test_reject_unsafe_links_raises_for_nested_junction(tmp_path: Path) -> None:
    """A junction pode estar escondida dentro de um projeto que, por fora,
    parece legítimo — tem que ser pega na varredura, não só na raiz."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "regular.txt").write_text("ok", encoding="utf-8")
    target = tmp_path / "outside-target"
    target.mkdir()
    (target / "secret.txt").write_text("conteudo fora do sandbox", encoding="utf-8")
    nested_link = project / "nested"
    make_unsafe_link(nested_link, target)
    with pytest.raises(UnsafePathError):
        reject_unsafe_links(project)
