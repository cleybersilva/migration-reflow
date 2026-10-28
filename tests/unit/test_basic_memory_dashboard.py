"""Gerador do dashboard (docs/data.json) a partir das notas do Basic Memory.

O parser de frontmatter é mínimo (não é YAML geral) — estes testes travam
exatamente os estilos que as notas reais do Basic Memory usam: escalar
citado dobrado em duas linhas, escalar sem aspas dobrado, e lista `- item`
sem indentação (mesma coluna da chave).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.basic_memory_dashboard import (
    build_dashboard,
    build_note,
    category_for,
    parse_frontmatter,
    project_for,
    split_frontmatter,
    write_dashboard,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


NOTE_WITH_FOLDED_FIELDS = """---
title: 'Corrigido erro real no dashboard: thinking de modelo local consumia todo o
  token budget'
type: trabalho_dev
projeto: migration-reflow
atividade: Corrigir etapa Documentacao do dashboard local (content vazio por esgotar
  num_predict em thinking) e adicionar flag --model
data: '2026-10-21'
hora: 17:04 -03:00
status: concluido
tipo: correcao
tags:
- migration-reflow
- dashboard
- ollama
- bugfix
---

## Corpo
Texto da nota.
"""

NOTE_RULE = """---
title: 'Regra: registrar todo trabalho dev no Basic Memory'
type: regra
tags:
- workflow
- basic-memory
---

# Regra
Corpo da regra.
"""


def test_split_frontmatter_separates_header_and_body() -> None:
    frontmatter, body = split_frontmatter(NOTE_WITH_FOLDED_FIELDS)
    require("title:" in frontmatter, "frontmatter deveria conter o title")
    require(body.startswith("## Corpo"), f"corpo inesperado: {body[:30]!r}")


def test_parse_frontmatter_folds_quoted_scalar_across_lines() -> None:
    frontmatter, _ = split_frontmatter(NOTE_WITH_FOLDED_FIELDS)
    fm = parse_frontmatter(frontmatter)
    require(
        fm["title"] == "Corrigido erro real no dashboard: thinking de modelo local consumia todo o "
        "token budget",
        f"title mal dobrado: {fm['title']!r}",
    )


def test_parse_frontmatter_folds_unquoted_scalar_across_lines() -> None:
    frontmatter, _ = split_frontmatter(NOTE_WITH_FOLDED_FIELDS)
    fm = parse_frontmatter(frontmatter)
    require(
        fm["atividade"]
        == "Corrigir etapa Documentacao do dashboard local (content vazio por esgotar "
        "num_predict em thinking) e adicionar flag --model",
        f"atividade mal dobrada: {fm['atividade']!r}",
    )


def test_parse_frontmatter_reads_unindented_list() -> None:
    frontmatter, _ = split_frontmatter(NOTE_WITH_FOLDED_FIELDS)
    fm = parse_frontmatter(frontmatter)
    require(
        fm["tags"] == ["migration-reflow", "dashboard", "ollama", "bugfix"],
        f"lista de tags incorreta: {fm['tags']!r}",
    )


def test_parse_frontmatter_strips_quotes_from_simple_scalar() -> None:
    frontmatter, _ = split_frontmatter(NOTE_WITH_FOLDED_FIELDS)
    fm = parse_frontmatter(frontmatter)
    require(fm["data"] == "2026-10-21", f"data com aspas sobrando: {fm['data']!r}")


def test_category_for_prefers_tipo_over_type() -> None:
    frontmatter, _ = split_frontmatter(NOTE_WITH_FOLDED_FIELDS)
    fm = parse_frontmatter(frontmatter)
    slug, label = category_for(fm)
    require(slug == "correcao" and label == "Correção", f"categoria errada: {slug}/{label}")


def test_category_for_falls_back_to_type_when_tipo_absent() -> None:
    frontmatter, _ = split_frontmatter(NOTE_RULE)
    fm = parse_frontmatter(frontmatter)
    slug, label = category_for(fm)
    require(slug == "regra" and label == "Regra", f"categoria errada: {slug}/{label}")


def test_project_for_reads_projects_subfolder(tmp_path: Path) -> None:
    root = tmp_path
    note = root / "projects" / "migration-reflow" / "nota.md"
    note.parent.mkdir(parents=True)
    note.write_text(NOTE_WITH_FOLDED_FIELDS, encoding="utf-8")
    require(
        project_for(note, root) == "migration-reflow",
        "nota em projects/<x>/ deveria pertencer ao projeto <x>",
    )


def test_project_for_treats_instructions_as_its_own_project(tmp_path: Path) -> None:
    root = tmp_path
    note = root / "instructions" / "regra.md"
    note.parent.mkdir(parents=True)
    note.write_text(NOTE_RULE, encoding="utf-8")
    require(
        project_for(note, root) == "instructions",
        "nota em instructions/ deveria ser do projeto instructions",
    )


def test_build_note_excludes_handled_keys_from_meta(tmp_path: Path) -> None:
    root = tmp_path
    note = root / "projects" / "migration-reflow" / "nota.md"
    note.parent.mkdir(parents=True)
    note.write_text(NOTE_WITH_FOLDED_FIELDS, encoding="utf-8")
    record = build_note(note, root)
    require(record["meta"] == {}, f"meta deveria estar vazio para esta nota: {record['meta']!r}")
    require(record["status"] == "concluido", "status nao propagado")
    require(record["statusLabel"] == "Concluído", "statusLabel nao traduzido")
    require("## Corpo" in record["content"], "corpo da nota ausente")


def test_build_note_keeps_extra_frontmatter_fields_in_meta(tmp_path: Path) -> None:
    root = tmp_path
    note = root / "projects" / "migration-reflow" / "nota.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        NOTE_WITH_FOLDED_FIELDS.replace("tipo: correcao", "tipo: correcao\nadr: ADR-021"),
        encoding="utf-8",
    )
    record = build_note(note, root)
    require(record["meta"] == {"adr": "ADR-021"}, f"meta incompleto: {record['meta']!r}")


def test_build_dashboard_sorts_notes_by_date_descending(tmp_path: Path) -> None:
    root = tmp_path
    older = root / "projects" / "p" / "a.md"
    newer = root / "projects" / "p" / "b.md"
    older.parent.mkdir(parents=True)
    older.write_text(
        "---\ntitle: Mais antiga\ntype: nota\ndata: '2026-01-01'\n---\n\ncorpo", encoding="utf-8"
    )
    newer.write_text(
        "---\ntitle: Mais nova\ntype: nota\ndata: '2026-06-01'\n---\n\ncorpo", encoding="utf-8"
    )
    data = build_dashboard(root)
    require(
        [n["title"] for n in data["notes"]] == ["Mais nova", "Mais antiga"],
        f"ordem incorreta: {[n['title'] for n in data['notes']]}",
    )
    require(
        {p["id"] for p in data["projects"]} == {"p"},
        f"projeto nao detectado: {data['projects']!r}",
    )


def test_build_dashboard_on_empty_root_returns_no_notes(tmp_path: Path) -> None:
    data = build_dashboard(tmp_path)
    require(data["notes"] == [], "raiz vazia deveria gerar zero notas")
    require(data["projects"] == [], "raiz vazia deveria gerar zero projetos")


def test_write_dashboard_masks_secret_looking_text_in_content(tmp_path: Path) -> None:
    content = "Token de `Authorization: Bearer` nao escapa mais do scan."  # reflow:allow-secret
    data = {"notes": [{"content": content}]}
    out = tmp_path / "data.json"
    write_dashboard(data, out)
    written = out.read_text(encoding="utf-8")
    require("Bearer`" not in written, f"valor sensivel nao mascarado: {written!r}")
    require("***" in written, f"mascara esperada ausente: {written!r}")
