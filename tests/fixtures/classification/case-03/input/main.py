"""Exemplo sintético; somente parsear, nunca executar durante a migração."""

import csv
import sqlite3


def load_orders():
    with open("orders.csv", encoding="utf-8", newline="") as source:
        rows = list(csv.reader(source))
    connection = sqlite3.connect("orders.db")
    connection.executemany("INSERT INTO orders VALUES (?, ?)", rows)
    connection.commit()
