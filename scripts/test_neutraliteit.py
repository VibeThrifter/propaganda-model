#!/usr/bin/env python3
"""test_neutraliteit.py — unit-test voor de J3-neutraliteitscheck (validation.check_neutraliteit).

Bouwt een kleine in-memory DB met een `type='persoon'`-entiteit en enkele
argumenten/relaties, en controleert dat:
  * een beschuldigende zin in de eigen stem over die persoon → GEVLAGD;
  * dezelfde beschuldiging mét in-zin bron-attributie ("volgens …" / citaat) → NIET;
  * een negatieve zin zónder genoemde persoon → NIET;
  * een neutrale zin over de persoon → NIET.

Draait standalone (geen live DB nodig): `python3 scripts/test_neutraliteit.py`.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import validation  # noqa: E402


def _mini_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT,
                               description TEXT, vervangen INTEGER DEFAULT 0,
                               status TEXT DEFAULT 'goedgekeurd');
        CREATE TABLE relations (id INTEGER PRIMARY KEY, description TEXT,
                                vervangen INTEGER DEFAULT 0);
        CREATE TABLE arguments (id INTEGER PRIMARY KEY, claim TEXT, reasoning TEXT,
                                vervangen INTEGER DEFAULT 0, status TEXT DEFAULT 'geverifieerd');
    """)
    conn.execute("INSERT INTO entities (id, name, type) VALUES (1, 'Jan Jansen', 'persoon')")
    # organisatie (geen persoon) — negatieve claim hierover mag NIET vlaggen
    conn.execute("INSERT INTO entities (id, name, type) VALUES (2, 'Acme BV', 'bedrijf')")
    return conn


def _codes_items(conn):
    bev = validation.check_neutraliteit(conn)[0]
    return bev["voorbeelden"], bev["aantal"]


def run():
    fouten = []

    # 1. Beschuldiging in de eigen stem over een persoon → gevlagd.
    conn = _mini_db()
    conn.execute("INSERT INTO arguments (id, claim) VALUES "
                 "(10, 'Jan Jansen pleegde fraude en is corrupt.')")
    items, aantal = _codes_items(conn)
    if aantal != 1:
        fouten.append(f"1) verwachtte 1 vlag voor kale beschuldiging, kreeg {aantal}: {items}")

    # 2. Zelfde beschuldiging mét in-zin attributie → niet gevlagd.
    conn = _mini_db()
    conn.execute("INSERT INTO arguments (id, claim) VALUES "
                 "(11, 'Volgens het OM pleegde Jan Jansen fraude.')")
    _, aantal = _codes_items(conn)
    if aantal != 0:
        fouten.append(f"2) 'volgens'-attributie zou niet mogen vlaggen, kreeg {aantal}")

    # 3. Citaat (aanhalingstekens) → niet gevlagd.
    conn = _mini_db()
    conn.execute('INSERT INTO arguments (id, claim) VALUES '
                 "(12, 'De rechter noemde Jan Jansen \"corrupt\".')")
    _, aantal = _codes_items(conn)
    if aantal != 0:
        fouten.append(f"3) citaat/attributie zou niet mogen vlaggen, kreeg {aantal}")

    # 4. Negatief woord zonder genoemde persoon → niet gevlagd.
    conn = _mini_db()
    conn.execute("INSERT INTO relations (id, description) VALUES "
                 "(20, 'De organisatie pleegde jarenlang fraude en corruptie.')")
    _, aantal = _codes_items(conn)
    if aantal != 0:
        fouten.append(f"4) negatief zonder persoonsnaam zou niet mogen vlaggen, kreeg {aantal}")

    # 5. Neutrale zin over de persoon → niet gevlagd.
    conn = _mini_db()
    conn.execute("INSERT INTO arguments (id, claim) VALUES "
                 "(13, 'Jan Jansen is sinds 2020 voorzitter van de raad van toezicht.')")
    _, aantal = _codes_items(conn)
    if aantal != 0:
        fouten.append(f"5) neutrale zin zou niet mogen vlaggen, kreeg {aantal}")

    # 6. Negatieve claim over een organisatie (geen persoon) → niet gevlagd.
    conn = _mini_db()
    conn.execute("INSERT INTO arguments (id, claim) VALUES "
                 "(14, 'Acme BV pleegde fraude.')")
    _, aantal = _codes_items(conn)
    if aantal != 0:
        fouten.append(f"6) negatieve org-claim (geen persoon) zou niet mogen vlaggen, kreeg {aantal}")

    if fouten:
        print("test_neutraliteit FAALT:")
        for f in fouten:
            print("  -", f)
        sys.exit(1)
    print("test_neutraliteit: groen (6 scenario's)")


if __name__ == "__main__":
    run()
