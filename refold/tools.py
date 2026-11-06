"""Ferramentas do agent no refold: ler, listar, buscar e gravar, sempre dentro de um sandbox.

Regras (falham de forma restritiva, como no resto do projeto):
- Leitura só em `output/<projeto>/`, `input/<projeto>/` e `reference/`. Nada de `.env`,
  caminho absoluto, `..`, UNC ou symlink/junction.
- Todo texto lido passa por `reflow.security.masking.mask` antes de ir ao LLM.
- Escrita só nos globs `edit: allow` do agent, com o `*` de `output/*/` preso ao projeto.
  O conteúdo gravado passa pelo mesmo scan do pre-commit; achado = gravação recusada.
- Resultado grande é cortado: o agent pede o próximo trecho com `offset`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from reflow.security.masking import mask
from reflow.security.paths import is_unc_path, is_unsafe_link
from reflow.security.scan import scan_bytes

MAX_RESULT_CHARS = 20_000
MAX_LINES = 400
MAX_LIST = 200
MAX_GREP_HITS = 100
MAX_WRITE_BYTES = 512_000


class ToolError(Exception):
    """Pedido recusado; a mensagem volta ao modelo como `is_error`."""


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out))


TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Lê um arquivo de texto (caminho relativo à raiz do repositório). "
        "Devolve linhas numeradas; use offset para continuar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "minimum": 1},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "Lista arquivos que casam com um glob (ex.: output/<projeto>/02-docs/*.md).",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": ["pattern"],
        },
    },
    {
        "name": "grep",
        "description": "Busca uma regex nos arquivos de um glob; devolve arquivo:linha: texto.",
        "input_schema": {
            "type": "object",
            "properties": {"regex": {"type": "string"}, "pattern": {"type": "string"}},
            "required": ["regex", "pattern"],
        },
    },
    {
        "name": "write_file",
        "description": "Grava (cria ou substitui) um arquivo UTF-8 dentro do escopo de escrita.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
]


@dataclass
class Sandbox:
    root: Path
    project: str
    write_globs: tuple[str, ...]
    written: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.read_prefixes = (f"output/{self.project}/", f"input/{self.project}/", "reference/")
        bound = []
        for glob in self.write_globs:
            if glob.startswith("output/*/"):
                glob = f"output/{self.project}/" + glob[len("output/*/") :]
            bound.append(_glob_to_regex(glob))
        self._write_res = tuple(bound)

    def describe_scope(self) -> str:
        writes = ", ".join(self.write_globs) or "nenhum (agent só lê)"
        return (
            f"Leitura: {', '.join(self.read_prefixes)}. "
            f"Escrita: {writes} (com `*` de output/ = {self.project})."
        )

    # -- caminhos ---------------------------------------------------------------------------

    def _normalize(self, raw: str) -> str:
        if not raw or "\x00" in raw or is_unc_path(raw):
            raise ToolError(f"caminho inválido: {raw!r}")
        rel = raw.replace("\\", "/")
        while rel.startswith("./"):
            rel = rel[2:]
        posix = PurePosixPath(rel)
        if posix.is_absolute() or re.match(r"^[A-Za-z]:", rel) or ".." in posix.parts:
            raise ToolError(f"caminho fora do repositório: {raw}")
        if any(part.startswith(".env") for part in posix.parts):
            raise ToolError(f"leitura de .env negada: {raw}")
        return str(posix)

    def _resolve(self, rel: str) -> Path:
        path = self.root / rel
        current = self.root
        for part in PurePosixPath(rel).parts:
            current = current / part
            if current.exists() and is_unsafe_link(current):
                raise ToolError(f"symlink/junction recusado: {rel}")
        return path

    def _check_read(self, raw: str) -> tuple[str, Path]:
        rel = self._normalize(raw)
        if not (rel + "/").startswith(self.read_prefixes):
            raise ToolError(f"fora do escopo de leitura ({', '.join(self.read_prefixes)}): {rel}")
        return rel, self._resolve(rel)

    def _iter_glob(self, pattern: str) -> list[str]:
        rel_pattern = self._normalize(pattern)
        if not rel_pattern.startswith(self.read_prefixes):
            raise ToolError(f"glob fora do escopo de leitura: {pattern}")
        regex = _glob_to_regex(rel_pattern)
        found: list[str] = []
        for prefix in self.read_prefixes:
            base = self.root / prefix
            if not base.is_dir() or not rel_pattern.startswith(prefix):
                continue
            for path in sorted(base.rglob("*")):
                if is_unsafe_link(path) or not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if regex.fullmatch(rel) and not any(
                    p.startswith(".env") for p in PurePosixPath(rel).parts
                ):
                    found.append(rel)
        return found

    # -- ferramentas ------------------------------------------------------------------------

    def read_file(self, path: str, offset: int = 1) -> str:
        rel, full = self._check_read(path)
        if not full.is_file():
            raise ToolError(f"arquivo não encontrado: {rel}")
        try:
            lines = full.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ToolError(f"arquivo não é texto UTF-8: {rel}") from exc
        start = max(offset, 1)
        chunk = lines[start - 1 : start - 1 + MAX_LINES]
        body = "\n".join(f"{start + i}\t{line}" for i, line in enumerate(chunk))
        end = start + len(chunk) - 1
        if end < len(lines):
            body += f"\n[... {len(lines) - end} linhas restantes; use offset={end + 1}]"
        return mask(body)

    def list_files(self, pattern: str) -> str:
        found = self._iter_glob(pattern)
        extra = f"\n[... mais {len(found) - MAX_LIST} arquivos]" if len(found) > MAX_LIST else ""
        return ("\n".join(found[:MAX_LIST]) or "(nenhum arquivo)") + extra

    def grep(self, regex: str, pattern: str) -> str:
        try:
            compiled = re.compile(regex)
        except re.error as exc:
            raise ToolError(f"regex inválida: {exc}") from exc
        hits: list[str] = []
        for rel in self._iter_glob(pattern):
            try:
                text = (self.root / rel).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if compiled.search(line):
                    hits.append(f"{rel}:{lineno}: {line.strip()[:300]}")
                    if len(hits) >= MAX_GREP_HITS:
                        return mask("\n".join(hits) + "\n[... limite de resultados]")
        return mask("\n".join(hits)) or "(nenhuma ocorrência)"

    def write_file(self, path: str, content: str) -> str:
        rel = self._normalize(path)
        if not any(r.fullmatch(rel) for r in self._write_res):
            raise ToolError(f"fora do escopo de escrita deste agent: {rel}")
        data = content.replace("\r\n", "\n").encode("utf-8")
        if len(data) > MAX_WRITE_BYTES:
            raise ToolError(f"conteúdo acima de {MAX_WRITE_BYTES} bytes: {rel}")
        findings = scan_bytes(data, rel)
        if findings:
            where = ", ".join(f"linha {f.line}" for f in findings[:5])
            raise ToolError(f"gravação recusada: possível segredo/PII em {rel} ({where})")
        full = self._resolve(rel)
        full.parent.mkdir(parents=True, exist_ok=True)
        if is_unsafe_link(full.parent):
            raise ToolError(f"symlink/junction recusado: {rel}")
        tmp = full.with_name(full.name + ".refold-tmp")
        tmp.write_bytes(data)
        tmp.replace(full)
        if rel not in self.written:
            self.written.append(rel)
        return f"gravado: {rel} ({len(data)} bytes)"

    def call(self, name: str, args: dict) -> str:
        try:
            if name == "read_file":
                return self.read_file(str(args["path"]), int(args.get("offset") or 1))
            if name == "list_files":
                return self.list_files(str(args["pattern"]))
            if name == "grep":
                return self.grep(str(args["regex"]), str(args["pattern"]))
            if name == "write_file":
                return self.write_file(str(args["path"]), str(args["content"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ToolError(f"argumentos inválidos para {name}: {exc}") from exc
        raise ToolError(f"ferramenta desconhecida: {name}")


def truncate(text: str) -> str:
    if len(text) <= MAX_RESULT_CHARS:
        return text
    return text[:MAX_RESULT_CHARS] + f"\n[... cortado em {MAX_RESULT_CHARS} caracteres]"
