"""Exemplo sintético; somente parsear, nunca executar durante a migração."""

from urllib.request import urlopen
import csv


def collect_quotes():
    with urlopen("https://example.invalid/quotes") as response:
        content = response.read()
    with open("quotes.csv", "w", encoding="utf-8", newline="") as output:
        csv.writer(output).writerow([content])
