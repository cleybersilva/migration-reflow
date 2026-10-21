"""Dashboard local opcional: teste textual honesto do fluxo/pipeline, isolado de output/.

Reaproveita `reflow/` (extração determinística, mascaramento, scan) mas nunca é
reaproveitado por ele — a dependência é de mão única. A única chamada de rede ao
LLM fica isolada em `dashboard/ollama_worker.ps1`, um subprocesso externo fixo e
confiável, nunca dentro deste processo Python. Ver `dashboard/README.md`.
"""

from __future__ import annotations
