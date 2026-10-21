"""Isolated smoke tests; only the PowerShell worker calls the loopback LLM API."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from reflow.cli import extract_to
from reflow.security.masking import mask_data
from reflow.security.scan import scan_bytes

PROJECT_NAME_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class DashboardRunner:
    def __init__(self, root: Path, model: str = "llama3.1:8b") -> None:
        self.root = root
        self.model = model
        self.cache: dict = {"available": False, "model": model, "message": "Verificação pendente"}
        self.checked_at = 0.0
        self.health_lock = threading.Lock()

    def projects(self, selection: str | None) -> list[str]:
        source = self.root / "input"
        if not source.exists():
            return []
        if source.is_symlink() or source.is_junction():
            raise ValueError("Diretório de entrada inseguro.")
        names = sorted(
            path.name
            for path in source.iterdir()
            if path.is_dir() and PROJECT_NAME_RE.fullmatch(path.name)
        )
        if selection is not None:
            if selection not in names:
                raise ValueError("Projeto não disponível.")
            return [selection]
        return names

    def _worker(
        self,
        mode: str,
        payload: dict | None = None,
        cancel: threading.Event | None = None,
        hint: str | None = None,
    ) -> dict:
        executable = shutil.which("pwsh")
        if not executable:
            raise ValueError("PowerShell 7 não encontrado.")
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        command = [
            executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(self.root / "dashboard" / "ollama_worker.ps1"),
            "-Mode",
            mode,
            "-Model",
            self.model,
        ]
        if hint:
            command += ["-Hint", hint]
        # Only this fixed, trusted script is executed; never any legacy file or command from input.
        with subprocess.Popen(  # noqa: S603 -- Fixed project worker, shell=False.
            command,
            cwd=self.root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=environment,
        ) as process:
            started = time.monotonic()
            content = json.dumps(payload or {}, ensure_ascii=False)
            first = True
            while True:
                try:
                    stdout, stderr = process.communicate(
                        input=content if first else None, timeout=0.5
                    )
                    break
                except subprocess.TimeoutExpired:
                    first = False
                    if (cancel and cancel.is_set()) or time.monotonic() - started > (
                        15 if mode == "Probe" else 200
                    ):
                        process.kill()
                        process.communicate()
                        raise ValueError("Teste cancelado ou prazo excedido.") from None
            if process.returncode:
                lines = (stderr or "").strip().splitlines()
                detail = next(
                    (line for line in reversed(lines) if line.startswith("Worker Ollama:")),
                    "",
                )
                suffix = f" {detail[:200]}" if detail else ""
                raise ValueError(f"O worker local falhou.{suffix}")
        data = json.loads(stdout)
        if not isinstance(data, dict):
            raise ValueError("Resposta local inválida.")
        return data

    @staticmethod
    def _retry_hint(error: Exception) -> str:
        message = str(error).lower()
        if "evidência" in message:
            return "retry_evidence"
        if "repetiu instruções" in message:
            return "retry_echo"
        if "direção" in message:
            return "retry_direction"
        if "texto" in message or "justificativa" in message:
            return "retry_text"
        return "retry_schema"

    @staticmethod
    def _validate_inference(step: str, data: dict, evidence: list[tuple[str, int]]) -> dict:
        """Accept only schema-compatible text and citations from the masked inventory."""
        if not isinstance(data, dict):
            raise ValueError("Resposta do modelo inválida.")
        text_key = "summary" if step == "document" else "reason"
        text = data.get(text_key)
        if not isinstance(text, str) or not 20 <= len(text.strip()) <= 6000:
            raise ValueError("Texto do modelo ausente ou inválido.")
        result = dict(data)
        result[text_key] = text.strip()
        lowered = result[text_key].lower()
        if step == "document":
            if any(
                marker in lowered
                for marker in (
                    "assistente técnico do reflow",
                    "a migração do reflow vai",
                    "não recomende converter",
                    "tarefa (document)",
                )
            ):
                raise ValueError("Resumo documental repetiu instruções.")
            match = re.search(
                r"\b(converter|convertido|migrar|migrado|levar)\b[^.\n]{0,80}"
                r"\bpara\s+(o\s+)?a360\b",
                result[text_key],
                re.IGNORECASE,
            )
            prefix = (
                result[text_key][max(0, match.start() - 30) : match.start()].lower()
                if match
                else ""
            )
            if match and "não" not in prefix and "nao" not in prefix:
                raise ValueError("Documentação com direção de migração incorreta.")
        if step == "classify":
            if any(
                marker in lowered
                for marker in (
                    "assistente técnico do reflow",
                    "tarefa (classify)",
                    "aplique a rubrica contida",
                )
            ):
                raise ValueError("Justificativa repetiu instruções.")
            verdict = result.get("verdict")
            if not isinstance(verdict, str) or verdict.strip().upper() not in {
                "PAD",
                "PARTIAL",
                "NOT_PAD",
            }:
                raise ValueError("Veredito do modelo inválido.")
            result["verdict"] = verdict.strip().upper()
            if result[text_key].upper() == result["verdict"]:
                raise ValueError("Justificativa do modelo insuficiente.")
        cited = result.get("evidence")
        if not isinstance(cited, list) or not cited:
            raise ValueError("Evidência obrigatória ausente.")
        allowed = {
            (str(file).replace("\\", "/").removeprefix("./").lower(), int(line))
            for file, line in evidence
        }
        normalized = []
        seen = set()
        for fact in cited:
            if not isinstance(fact, dict):
                raise ValueError("Evidência inválida.")
            file, line = fact.get("file"), fact.get("line")
            if not isinstance(file, str) or isinstance(line, bool):
                raise ValueError("Evidência inválida.")
            try:
                line = int(line)
            except (TypeError, ValueError):
                raise ValueError("Evidência inválida.") from None
            key = (file.replace("\\", "/").removeprefix("./").lower(), line)
            if key not in allowed:
                raise ValueError("Evidência não encontrada no inventário.")
            if key not in seen:
                seen.add(key)
                normalized.append({"file": file.replace("\\", "/"), "line": line})
        result["evidence"] = normalized
        return result

    def health(self) -> dict:
        with self.health_lock:
            if time.monotonic() - self.checked_at < 8:
                return self.cache
            try:
                data = self._worker("Probe")
                models = data.get("models")
                if not isinstance(models, list):
                    raise ValueError("Lista de modelos inválida.")
                ready = self.model in models
                self.cache = {
                    "available": ready,
                    "model": self.model,
                    "message": "Modelo disponível" if ready else "Modelo não instalado",
                }
            except (ValueError, OSError):
                self.cache = {
                    "available": False,
                    "model": self.model,
                    "message": "Ollama ou PowerShell 7 indisponível",
                }
            self.checked_at = time.monotonic()
            return self.cache

    def execute(self, run_id: str, project: str, step: str, cancel: threading.Event) -> dict:
        folder = self.root / ".dashboard-runs" / run_id / project
        if step == "ollama_check":
            if not self.health()["available"]:
                raise ValueError("Modelo indisponível.")
            return {"detail": "Ollama disponível; nenhum modelo será baixado automaticamente."}
        if step == "extract":
            extract_to(self.root / "input" / project, folder)
            return {"detail": "Inventário mascarado criado na área isolada deste teste."}
        if step in {"document", "classify"}:
            path = folder / "01-inventory" / "inventory.json"
            content = path.read_bytes()
            if len(content) > 24000 or scan_bytes(content, "inventory.json"):
                raise ValueError(
                    "Inventário sensível ou maior que o orçamento local; nada foi truncado."
                )
            inventory = json.loads(content)
            evidence = sorted(
                {
                    (fact["file"], fact["line"])
                    for values in inventory.values()
                    if isinstance(values, list)
                    for fact in values
                    if isinstance(fact, dict)
                    and isinstance(fact.get("file"), str)
                    and isinstance(fact.get("line"), int)
                }
            )
            payload = {
                "inventory": inventory,
                "evidence_catalog": [{"file": file, "line": line} for file, line in evidence],
            }
            if step == "classify":
                payload["rubric"] = (self.root / "reference/classification-rubric.md").read_text(
                    "utf-8"
                )
            mode = "Document" if step == "document" else "Classify"
            failures = []
            hint = None
            for attempt in range(2):
                try:
                    data = self._worker(mode, payload, cancel, hint)
                    safe = mask_data(self._validate_inference(step, data, evidence))
                    break
                except (ValueError, OSError) as exc:
                    reason = (str(exc) if isinstance(exc, ValueError) else type(exc).__name__)[:300]
                    entry = {"attempt": attempt + 1, "reason": reason}
                    if attempt == 0:
                        hint = self._retry_hint(exc)
                        entry["retry_hint"] = hint
                    failures.append(entry)
                    if cancel.is_set():
                        raise ValueError("Teste cancelado.") from None
                    if attempt == 1:
                        _write_json(
                            folder / f"failure-{step}.json",
                            {"step": step, "attempts": failures},
                        )
                        raise ValueError(
                            "O modelo não retornou prévia válida após duas tentativas."
                        ) from None
                    time.sleep(1)
            _write_json(folder / f"preview-{step}.json", safe)
            suffix = f" Sugestão: {safe['verdict']}." if step == "classify" else ""
            return {
                "detail": (
                    f"Prévia recebida; revisão humana necessária.{suffix} "
                    + safe["summary" if step == "document" else "reason"][:1200]
                )
            }
        if step == "security":
            for path in folder.rglob("*"):
                if path.is_file() and scan_bytes(path.read_bytes(), path.name):
                    raise ValueError("Saída do teste contém achado de segurança.")
            return {"detail": "Nenhum achado reconhecido nas saídas isoladas deste teste."}
        if step == "lint":
            # This smoke test does not convert robots or reuse historical flows as new output.
            return {
                "status": "skipped",
                "detail": "Não aplicável: este teste não converte nem executa flows PAD.",
            }
        if step == "report":
            _write_json(
                folder / "test-report.json",
                {
                    "project": project,
                    "model": self.model,
                    "kind": "local-text-smoke-test",
                    "pad_executed": False,
                    "migration_completed": False,
                    "review_required": True,
                },
            )
            return {
                "detail": "Relatório do teste salvo em .dashboard-runs/. Migração não homologada."
            }
        raise ValueError("Etapa desconhecida.")
