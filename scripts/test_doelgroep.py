#!/usr/bin/env python3
"""test_doelgroep.py — welstandsmeter: getargette marketing-/welstandsklasse per outlet.

Dekt de parser (klasse + meting + afwijzingen) en de afleiding (compute_doelgroepmeter):
per outlet een afgeleide positie op de welstand-as (hoog A ↔ laag D) uit `doelgroepklasse`-
aspect-argumenten op entiteiten. Zelfstandig — bouwt een minimale in-memory DB.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import doelgroep  # noqa: E402


def test_parser():
    P = doelgroep._parse
    assert P("welstand:A") == ("welstand", "klasse", 1.0), P("welstand:A")
    assert P("welstand:B2") == ("welstand", "klasse", 0.0), P("welstand:B2")
    assert P("welstand:D") == ("welstand", "klasse", -1.0), P("welstand:D")
    assert P("welstand:meting:0.7") == ("welstand", "meting", 0.7), P("welstand:meting:0.7")
    for bad in ("", None, "welstand:E", "welstand:onzin", "welstand:", "A", "welstand:meting:x"):
        try:
            P(bad)
            assert False, f"zou ValueError moeten geven: {bad!r}"
        except (ValueError, AttributeError):
            pass
    print("  parser: OK")


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT);
        CREATE TABLE sources (id INTEGER PRIMARY KEY, reliability TEXT, onderwerp TEXT);
        CREATE TABLE arguments (
            id INTEGER PRIMARY KEY, relation_id INT, mechanism_id INT, entity_id INT,
            property TEXT, property_value TEXT, status TEXT, claim TEXT,
            parent_argument_id INT, vervangen INT DEFAULT 0);
        CREATE TABLE citations (id INTEGER PRIMARY KEY, argument_id INT, source_id INT);
    """)
    conn.executemany("INSERT INTO entities VALUES (?,?,?)", [
        (1, "NRC", "mediaorganisatie"),
        (2, "Metro", "mediaorganisatie"),
    ])
    conn.execute("INSERT INTO sources VALUES (1,'primair','nl_systeem')")
    return conn


def _arg(conn, aid, eid, pval, status="geverifieerd"):
    conn.execute("INSERT INTO arguments (id, entity_id, property, property_value, status, "
                 "claim) VALUES (?,?,?,?,?,?)",
                 (aid, eid, "doelgroepklasse", pval, status, pval))
    conn.execute("INSERT INTO citations (argument_id, source_id) VALUES (?,1)", (aid,))


def test_afleiding():
    conn = _db()
    # NRC target de bovenlaag (twee A-signalen) → positie duidelijk hoog.
    _arg(conn, 100, 1, "welstand:A")
    _arg(conn, 101, 1, "welstand:A")
    # Metro lager op de as (C).
    _arg(conn, 200, 2, "welstand:C")
    conn.commit()

    res = doelgroep.compute_doelgroepmeter(conn)
    outlets = {o["naam"]: o for o in res["outlets"]}

    # Ongekrompen: één autoritatieve A-opgave plaatst NRC direct hoog (label A).
    nrc = outlets["NRC"]
    assert nrc["positie"] == 1.0, f"NRC positie 1.0 verwacht (2x A), kreeg {nrc['positie']}"
    assert nrc["as_soort"] == "opgave" and nrc["n_signalen"] == 2, nrc
    assert nrc["klasse_label"].startswith("A"), nrc["klasse_label"]

    metro = outlets["Metro"]
    assert metro["positie"] < 0, f"Metro lager verwacht, kreeg {metro['positie']}"

    # Bron-gewogen gemiddelde: klasse-opgave + NOM-meting (gelijk gewicht) → gemiddeld.
    conn2 = _db()
    _arg(conn2, 300, 1, "welstand:A")               # opgave hoog (+1)
    _arg(conn2, 301, 1, "welstand:meting:0.0")      # meting standaard (0) — zelfde bron/gewicht
    conn2.commit()
    m = {o["naam"]: o for o in doelgroep.compute_doelgroepmeter(conn2)["outlets"]}["NRC"]
    assert m["as_soort"] == "meting" and abs(m["positie"] - 0.5) < 1e-6, m
    print("  afleiding: OK")


def test_voorgesteld_telt_pas_na_merge():
    conn = _db()
    _arg(conn, 400, 1, "welstand:A", status="voorgesteld")
    conn.commit()
    assert doelgroep.compute_doelgroepmeter(conn)["outlets"] == [], "voorgesteld telt in niets"
    prev = doelgroep.compute_doelgroepmeter(conn, include_voorgesteld=True)
    assert prev["outlets"] and prev["outlets"][0]["positie"] > 0, "preview zou voorgesteld moeten tonen"
    print("  voorgesteld-poort: OK")


if __name__ == "__main__":
    print("test_doelgroep:")
    test_parser()
    test_afleiding()
    test_voorgesteld_telt_pas_na_merge()
    print("ALLE TESTS GESLAAGD")
