"""Teto de entrada da extração real — falha **antes** de ler, não durante.

`reflow extract` não tinha limite nenhum de arquivo, profundidade ou bytes:
uma árvore enorme seria lida inteira em memória (`read_bytes` por arquivo,
tanto no extractor quanto no hash do manifesto). Estes são os tetos do
caminho real, generosos de propósito (um export A360 legítimo cabe com
folga) mas finitos — a ideia nunca foi dimensionar robô reais, e sim
impedir exaustão de recurso sem aviso.

O `dashboard/` mantém um orçamento próprio e mais apertado
(`dashboard/pipeline.py`: 500 arquivos / 12 níveis / 20 MB) porque é um
smoke test local; ele roda **antes** destes aqui. Ver ADR-021.
"""

from __future__ import annotations

import os
from pathlib import Path

MAX_INPUT_FILE_COUNT = 5000
MAX_INPUT_DEPTH = 30
MAX_INPUT_TOTAL_BYTES = 512 * 1024 * 1024
MAX_INPUT_FILE_BYTES = 64 * 1024 * 1024


def check_input_budget(root: Path) -> None:
    """Levanta `ValueError` (restritivo) se `root` passa de qualquer teto.

    Mede só metadados (`stat`), nunca lê conteúdo. Caminhos são varridos com
    `os.walk(followlinks=False)` e **depois** de `reject_unsafe_links()` —
    esta checagem não decide o que é seguro ler, só quanto pode ser lido.
    Os tetos são lidos dos nomes do módulo em tempo de chamada, então um
    teste pode rebaixá-los com `monkeypatch.setattr` sem criar arquivo grande.
    """
    root = Path(root)
    file_count = 0
    total_bytes = 0
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        depth = len(current.relative_to(root).parts)
        if depth > MAX_INPUT_DEPTH:
            raise ValueError(
                f"{root}: mais de {MAX_INPUT_DEPTH} níveis de profundidade "
                f"(encontrado {depth}) — fora do orçamento da extração."
            )
        for name in filenames:
            file = current / name
            try:
                size = file.stat().st_size
            except OSError:
                raise ValueError(f"{root}: não foi possível medir {file}") from None
            file_count += 1
            if file_count > MAX_INPUT_FILE_COUNT:
                raise ValueError(
                    f"{root}: mais de {MAX_INPUT_FILE_COUNT} arquivos — "
                    "fora do orçamento da extração."
                )
            if size > MAX_INPUT_FILE_BYTES:
                raise ValueError(
                    f"{file}: {size} bytes acima do teto de "
                    f"{MAX_INPUT_FILE_BYTES} bytes por arquivo."
                )
            total_bytes += size
            if total_bytes > MAX_INPUT_TOTAL_BYTES:
                raise ValueError(
                    f"{root}: mais de {MAX_INPUT_TOTAL_BYTES} bytes no total — "
                    "fora do orçamento da extração."
                )
