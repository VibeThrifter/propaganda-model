#!/usr/bin/env python3
"""Test voor scripts/naamcontrole.py op een tijdelijke SQLite (geen echte db, geen API)."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import naamcontrole as nc  # noqa: E402


def maak():
    c = sqlite3.connect(":memory:")
    c.executescript("""
    CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT, status TEXT DEFAULT 'goedgekeurd',
                           vervangen BOOLEAN DEFAULT 0);
    CREATE TABLE externe_ids (id INTEGER PRIMARY KEY, entity_id INT, stelsel TEXT, waarde TEXT);
    """)
    c.executemany("INSERT INTO entities (id, name, type) VALUES (?, ?, 'persoon')", [
        (1, "Bouke Geersing"),          # register kent Bauke Geersing
        (2, "Marije van Dijk"),         # exact in register: niet verdacht
        (3, "Pieter de Vries"),         # id-koppeling met afwijkende voornaam
        (4, "Jan Smit"),                # te kort voor de controle
        (5, "Marieke Jansen"),          # model-paar
        (6, "Marieka Jansen"),
        (7, "B. Onbekend"),             # voorletters: overgeslagen
    ])
    c.execute("INSERT INTO externe_ids (entity_id, stelsel, waarde) VALUES (3, 'tk_persoon', 'TK-1')")
    return c


REF = {
    "achternaam": {
        "geersing": {"bauke": {"naam": "Bauke Geersing", "bron": "wikidata 2026-10-13 Q1"}},
        "van dijk": {"marije": {"naam": "Marije van Dijk", "bron": "tk_persoon x TK-2"}},
        "de vries": {"pieter": {"naam": "Pieter de Vries", "bron": "tk_persoon x TK-1"}},
    },
    "id": {("tk_persoon", "TK-1"): {"naam": "Pieter de Vries", "voornamen": ["pieter"],
                                     "achternaam": "de vries", "bron": "tk_persoon x TK-1"}},
}


def test():
    rap = {r["entiteit_id"]: r for r in nc.controleer(maak(), REF)}
    assert 1 in rap and rap[1]["voorstel"] == "Bauke Geersing" and rap[1]["vertrouwen"] == "midden", rap
    assert 2 not in rap, "exacte schrijfwijze mag niet gemeld worden"
    assert 3 not in rap or rap[3]["vertrouwen"] != "laag"  # voornaam gelijk: geen id-melding
    assert 4 not in rap and 7 not in rap
    assert 5 in rap and rap[5]["voorstel"] == "Marieka Jansen" and rap[5]["vertrouwen"] == "laag", rap
    assert 6 not in rap  # een paar wordt één keer gemeld (bij het kleinste id)
    # id-koppeling: afwijkende voornaam bij hetzelfde id
    c = maak()
    c.execute("UPDATE entities SET name = 'Pietr de Vries' WHERE id = 3")
    rap = {r["entiteit_id"]: r for r in nc.controleer(c, REF)}
    assert rap[3]["vertrouwen"] == "hoog" and rap[3]["voorstel"] == "Pieter de Vries", rap
    assert nc.editafstand("bouke", "bauke") == 1 and nc.editafstand("jan", "jansen") >= 3
    print("test_naamcontrole: ok")


if __name__ == "__main__":
    test()
