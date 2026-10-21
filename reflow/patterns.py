"""Padrões de classificação usados pelos extractors: UI, HTTP, dados e credenciais.

Base conservadora, construída a partir das fixtures e de convenções conhecidas do
A360/.NET/Python. Não equivale a uma whitelist Robin (ver reference/robin-actions.md)
e não substitui a tabela verdade (reference/a360-to-pad.md, Fase 4) — comandos A360
fora deste registro caem em `unknown_commands` e alimentam essa tabela.
"""

from __future__ import annotations

# A360: (packageName, commandName) -> categoria do inventário.
A360_REGISTRY: dict[tuple[str, str], str] = {
    # Interações de UI (Recorder/Browser/Window/Mouse-Keyboard/Excel UI)
    ("Browser", "open"): "ui_interactions",
    ("Browser", "close"): "ui_interactions",
    ("Browser", "click"): "ui_interactions",
    ("Window", "activate"): "ui_interactions",
    ("Window", "close"): "ui_interactions",
    ("Recorder", "playback"): "ui_interactions",
    ("MouseKeyboard", "click"): "ui_interactions",
    ("MouseKeyboard", "type"): "ui_interactions",
    ("Excel", "activate"): "ui_interactions",
    # Chamadas HTTP/SOAP
    ("REST", "get"): "http_calls",
    ("REST", "post"): "http_calls",
    ("REST", "put"): "http_calls",
    ("REST", "delete"): "http_calls",
    ("SOAP", "call"): "http_calls",
    # Fontes de dados (Excel, CSV, banco de dados, arquivos)
    ("Excel", "open"): "data_sources",
    ("Excel", "read"): "data_sources",
    ("Excel", "write"): "data_sources",
    ("CSV", "read"): "data_sources",
    ("CSV", "write"): "data_sources",
    ("Database", "connect"): "data_sources",
    ("Database", "query"): "data_sources",
    ("File", "read"): "data_sources",
    ("File", "write"): "data_sources",
    # Credenciais: só a referência ao cofre, nunca o valor
    ("CredentialVault", "getCredential"): "credentials",
    ("CredentialVault", "get"): "credentials",
    # Dependência entre bots (TaskBot acionando outro bot)
    ("TaskBot", "run"): "dependencies",
}

# Python: operação resolvida (via alias de import) -> categoria.
PYTHON_HTTP_OPERATIONS: frozenset[str] = frozenset(
    {
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.patch",
        "requests.head",
        "requests.options",
        "httpx.get",
        "httpx.post",
        "httpx.put",
        "httpx.delete",
        "urllib.request.urlopen",
        "http.client.HTTPConnection",
    }
)
PYTHON_DATA_SOURCE_OPERATIONS: frozenset[str] = frozenset(
    {
        "open",
        "csv.writer",
        "csv.reader",
        "sqlite3.connect",
        "pandas.read_csv",
        "pandas.read_excel",
        "openpyxl.load_workbook",
    }
)

# .NET: heurísticas por linha (sem compilador).
DOTNET_SOURCE_SUFFIXES: tuple[str, ...] = (".cs", ".vb")
DOTNET_BINARY_SUFFIXES: tuple[str, ...] = (".dll", ".exe")
DOTNET_HTTP_MARKERS: tuple[str, ...] = (
    "HttpClient",
    "WebClient",
    "HttpWebRequest",
    "HttpRequestMessage",
)
DOTNET_IO_MARKERS: tuple[str, ...] = (
    "File.ReadAllText",
    "File.ReadAllLines",
    "File.ReadAllBytes",
    "File.WriteAllText",
    "StreamReader",
    "StreamWriter",
)
