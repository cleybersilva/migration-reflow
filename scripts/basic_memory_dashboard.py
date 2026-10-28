"""Gera `docs/data.json` a partir das notas do Basic Memory local, para o
dashboard estático publicado em GitHub Pages (`docs/index.html`).

Fonte: arquivos markdown em `<basic-memory>/projects/<projeto>/*.md` e
`<basic-memory>/instructions/*.md`. Lê os arquivos direto do disco (sem API,
sem MCP, sem LLM) — determinístico, igual ao resto do núcleo `reflow`.

Antes de gravar, passa `mask_data()` (reflow/security/masking.py) sobre todo
o JSON — a página é pública, e uma nota pode citar um padrão tipo
`chave: valor` só para documentar o próprio scanner (ex.: "Authorization:
Bearer"), que `reflow scan --staged` bloquearia no commit sem essa máscara.

Depois de gravar uma nota nova no Basic Memory, antes do commit, rode:

    uv run python -m scripts.basic_memory_dashboard
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from reflow.security.masking import mask_data

DEFAULT_ROOT = Path.home() / "basic-memory"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "docs" / "data.json"

_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):[ \t]?(.*)$")
_LIST_ITEM_RE = re.compile(r"^-[ \t]+(.*)$")

_HANDLED_KEYS = {
    "title",
    "type",
    "tipo",
    "status",
    "data",
    "hora",
    "tags",
    "permalink",
    "projeto",
    "atividade",
}

_CATEGORY_LABELS = {
    "diagnostico": "Diagnóstico",
    "correcao": "Correção",
    "implementacao": "Implementação",
    "trabalho-dev": "Trabalho",
    "trabalho_dev": "Trabalho",
    "manutencao": "Manutenção",
    "configuracao": "Configuração",
    "regra": "Regra",
    "nota": "Nota",
    "note": "Nota",
}

_STATUS_LABELS = {
    "concluido": "Concluído",
    "em-andamento": "Em andamento",
    "bloqueado": "Bloqueado",
}

_PROJECT_LABELS = {
    "instructions": "Instruções & regras",
}

type FrontmatterValue = str | list[str]


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("nota sem frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("frontmatter sem fechamento '---'")
    frontmatter = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    return frontmatter, body


def parse_frontmatter(raw: str) -> dict[str, FrontmatterValue]:
    """Parser mínimo para o dialeto YAML que o Basic Memory grava: escalares
    simples ou citados (inclusive dobrados em várias linhas, estilo YAML
    folded) e listas `- item`. Não é um parser YAML geral — cobre só o que
    estas notas realmente usam (chave solta na coluna 0, continuação
    indentada)."""
    lines = raw.splitlines()
    result: dict[str, FrontmatterValue] = {}
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        match = _KEY_RE.match(line)
        if not match:
            i += 1
            continue
        key, first_value = match.group(1), match.group(2)
        i += 1
        list_items: list[str] = []
        scalar_parts: list[str] = [first_value] if first_value else []
        # Continuação: linha indentada (fold de escalar) OU, quando a chave
        # não teve valor na própria linha, uma sequência `- item` do YAML
        # pode vir sem indentação (mesma coluna da chave) — ambos os estilos
        # aparecem nas notas do Basic Memory.
        while i < n:
            current = lines[i]
            indented = current.startswith((" ", "\t"))
            unindented_list_item = not first_value and _LIST_ITEM_RE.match(current)
            if not indented and not unindented_list_item:
                break
            cont = current.strip()
            list_match = _LIST_ITEM_RE.match(cont)
            if list_match:
                list_items.append(_strip_quotes(list_match.group(1)))
            elif cont:
                scalar_parts.append(cont)
            i += 1
        result[key] = list_items if list_items else _strip_quotes(" ".join(scalar_parts).strip())
    return result


def iter_note_paths(root: Path) -> Iterable[Path]:
    projects_dir = root / "projects"
    if projects_dir.is_dir():
        yield from sorted(projects_dir.glob("*/*.md"))
    instructions_dir = root / "instructions"
    if instructions_dir.is_dir():
        yield from sorted(instructions_dir.glob("*.md"))


def project_for(path: Path, root: Path) -> str:
    parts = path.relative_to(root).parts
    if parts[0] == "projects" and len(parts) >= 2:
        return parts[1]
    return "instructions"


def category_for(frontmatter: dict[str, FrontmatterValue]) -> tuple[str, str]:
    raw = str(frontmatter.get("tipo") or frontmatter.get("type") or "nota")
    label = _CATEGORY_LABELS.get(raw, raw.replace("-", " ").replace("_", " ").title())
    slug = raw.replace("_", "-")
    return slug, label


def build_note(path: Path, root: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter_raw, body = split_frontmatter(text)
    fm = parse_frontmatter(frontmatter_raw)

    categoria, categoria_label = category_for(fm)
    status = fm.get("status")
    status = str(status) if status else None

    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    meta = {k: v for k, v in fm.items() if k not in _HANDLED_KEYS}
    title = str(fm.get("title") or path.stem)

    return {
        "id": path.relative_to(root).with_suffix("").as_posix(),
        "title": title,
        "project": project_for(path, root),
        "categoria": categoria,
        "categoriaLabel": categoria_label,
        "status": status,
        "statusLabel": _STATUS_LABELS.get(status or "", status),
        "data": fm.get("data"),
        "hora": fm.get("hora"),
        "atividade": fm.get("atividade"),
        "tags": tags,
        "meta": meta,
        "content": body.rstrip("\n"),
    }


def _sort_key(note: dict[str, object]) -> tuple[str, str]:
    return (str(note.get("data") or ""), str(note.get("hora") or ""))


def build_dashboard(root: Path) -> dict[str, object]:
    notes = [build_note(path, root) for path in iter_note_paths(root)]
    notes.sort(key=_sort_key, reverse=True)

    project_ids: dict[str, None] = {}
    for note in notes:
        project_ids.setdefault(str(note["project"]), None)
    projects = [{"id": pid, "label": _PROJECT_LABELS.get(pid, pid)} for pid in project_ids]

    return {
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "projects": projects,
        "notes": notes,
    }


def write_dashboard(data: dict[str, object], out_path: Path) -> None:
    masked = mask_data(data)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(masked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"erro: diretorio do Basic Memory nao encontrado: {args.root}", file=sys.stderr)
        return 1

    data = build_dashboard(args.root)
    write_dashboard(data, args.out)
    print(f"gravado: {args.out} ({len(data['notes'])} notas, {len(data['projects'])} projetos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
