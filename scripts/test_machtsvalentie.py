#!/usr/bin/env python3
"""test_machtsvalentie.py — machtsvalentie: tegenmacht als gerichte edge-valentie.

Dekt de parser (beide vormen + afwijzingen) en de afleiding (compute_machtsvalentie):
per actor een contra-hegemonische valentie-per-as (opent/sluit) uit `machtsvalentie`-
aspect-argumenten op relaties, plus welke filter-concentraties ze verantwoordt.
Zelfstandig — bouwt een minimale in-memory DB, raakt de echte DB niet aan.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import tegenmacht  # noqa: E402


def test_parser():
    P = tegenmacht.parse_machtsvalentie
    # Verantwoording (soort 1)
    v = P("filter:eigendom")
    assert v and v["soort"] == "verantwoording" and v["doel"] == "eigendom", v
    # Contra-hegemonie (soort 2)
    o = P("as:establishment:opent")
    assert o and o["soort"] == "contra_hegemonie" and o["as"] == "establishment"
    assert o["teken"] == 1.0, o
    s = P("as:economisch:sluit")
    assert s and s["teken"] == -1.0, s
    # Afwijzingen
    for bad in ("", None, "filter:tegenmacht", "filter:onzin", "as:onbekend:opent",
                "as:economisch:misschien", "as:economisch", "politieke_positie", "eigendom"):
        assert P(bad) is None, f"zou None moeten zijn: {bad!r}"
    print("  parser: OK")


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT);
        CREATE TABLE mechanisms (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE relations (id INTEGER PRIMARY KEY, source_id INT, target_id INT,
            mechanism_id INT, vervangen INT DEFAULT 0);
        CREATE TABLE sources (id INTEGER PRIMARY KEY, reliability TEXT, onderwerp TEXT);
        CREATE TABLE arguments (
            id INTEGER PRIMARY KEY, relation_id INT, mechanism_id INT, entity_id INT,
            property TEXT, property_value TEXT, status TEXT, claim TEXT,
            parent_argument_id INT, vervangen INT DEFAULT 0);
        CREATE TABLE citations (id INTEGER PRIMARY KEY, argument_id INT, source_id INT);
    """)
    conn.executemany("INSERT INTO entities VALUES (?,?,?)", [
        (1, "Forum voor Democratie", "partij"),
        (2, "NOS", "omroep"),
        (3, "Stichting Democratie en Media", "stichting"),
        (4, "DPG Media", "bedrijf"),
    ])
    conn.execute("INSERT INTO mechanisms VALUES (50, 'redactiestatuut_borging')")
    conn.executemany("INSERT INTO relations (id, source_id, target_id, mechanism_id) "
                     "VALUES (?,?,?,?)", [
        (10, 1, 2, None),  # FvD -> NOS  (actor = FvD)
        (11, 3, 4, None),  # borgingsstichting -> DPG (actor = stichting)
    ])
    conn.execute("INSERT INTO sources VALUES (1,'wit','nl_systeem')")
    return conn


def _arg(conn, aid, rel, pval, status="geverifieerd", mech=None):
    conn.execute("INSERT INTO arguments (id, relation_id, mechanism_id, property, "
                 "property_value, status, claim) VALUES (?,?,?,?,?,?,?)",
                 (aid, rel, mech, "machtsvalentie", pval, status, pval))
    conn.execute("INSERT INTO citations (argument_id, source_id) VALUES (?,1)", (aid,))


def test_afleiding():
    conn = _db()
    # FvD opent de establishment-consensus (twee signalen), maar sluit één keer.
    _arg(conn, 100, 10, "as:establishment:opent")
    _arg(conn, 101, 10, "as:establishment:opent")
    _arg(conn, 102, 10, "as:establishment:sluit")
    # Borgingsstichting verantwoordt de eigendom-concentratie.
    _arg(conn, 200, 11, "filter:eigendom")
    conn.commit()

    res = tegenmacht.compute_machtsvalentie(conn)
    actoren = {a["naam"]: a for a in res["actoren"]}

    fvd = actoren["Forum voor Democratie"]
    est = fvd["valentie"]["establishment"]
    assert est is not None and est > 0, f"netto opent verwacht, kreeg {est}"
    assert fvd["duiding"]["establishment"] in ("opent", "opent sterk"), fvd["duiding"]
    assert fvd["valentie"]["economisch"] is None, "geen economisch signaal"
    assert fvd["verantwoordt"] == [], "FvD verantwoordt geen filter"

    stg = actoren["Stichting Democratie en Media"]
    assert stg["verantwoordt"] == ["eigendom"], stg["verantwoordt"]
    assert all(v is None for v in stg["valentie"].values()), "geen as-signaal"

    # edges bevat elke annotatie met bron-context (incl. bron_id).
    assert len(res["edges"]) == 4, res["edges"]
    assert all("bron_id" in e for e in res["edges"]), res["edges"]

    # Per-edge netto valentie: relatie 10 (FvD→NOS) opent netto (+), relatie 11
    # (borgingsstichting→DPG) verantwoordt eigendom en heeft géén as-teken.
    r10 = res["relaties"][10]
    assert r10["teken"] == 1 and r10["valentie"]["establishment"] > 0, r10
    r11 = res["relaties"][11]
    assert r11["teken"] == 0 and r11["verantwoordt"] == ["eigendom"], r11
    print("  afleiding: OK")


def test_voorgesteld_telt_pas_na_merge():
    conn = _db()
    _arg(conn, 300, 10, "as:cultureel:opent", status="voorgesteld")
    conn.commit()
    # Zonder preview: voorgesteld telt in niets → geen actoren.
    assert tegenmacht.compute_machtsvalentie(conn)["actoren"] == []
    # Met preview: voorlopig zichtbaar.
    prev = tegenmacht.compute_machtsvalentie(conn, include_voorgesteld=True)
    assert prev["actoren"], "preview zou voorgesteld moeten tonen"
    assert prev["actoren"][0]["valentie"]["cultureel"] > 0
    print("  voorgesteld-poort: OK")


def test_overerving_verantwoording():
    """Een verantwoording-annotatie op een MECHANISME erft naar zijn instanties
    (het `aard`-patroon): de relatie en haar bron-actor krijgen het doel als geërfd
    (`n_geerfd`, niet `n_annotaties`). Opent/sluit erft bewust niet (casus-niveau)."""
    conn = _db()
    # Relatie 12 is een instantie van redactiestatuut_borging (mech 50), zonder eigen
    # annotatie; relatie 13 is vervangen en mag NIET erven.
    conn.execute("INSERT INTO relations (id, source_id, target_id, mechanism_id) "
                 "VALUES (12, 3, 4, 50)")
    conn.execute("INSERT INTO relations (id, source_id, target_id, mechanism_id, vervangen) "
                 "VALUES (13, 1, 2, 50, 1)")
    # Op het mechanisme: verantwoording (erft) én een as-signaal (erft niet).
    _arg(conn, 400, None, "filter:eigendom", mech=50)
    _arg(conn, 401, None, "as:establishment:opent", mech=50)
    conn.commit()

    res = tegenmacht.compute_machtsvalentie(conn)
    # Theorie-edge draagt beide zelf.
    m = res["mechanismen"][50]
    assert m["verantwoordt"] == ["eigendom"] and m["teken"] == 1, m
    # Instantie erft alléén de verantwoording, als geërfd geteld.
    r12 = res["relaties"][12]
    assert r12["verantwoordt"] == ["eigendom"], r12
    assert r12["n_annotaties"] == 0 and r12["n_geerfd"] == 1, r12
    assert all(v is None for v in r12["valentie"].values()), "as-signaal mag niet erven"
    # Vervangen instantie erft niet.
    assert 13 not in res["relaties"], res["relaties"].keys()
    # De bron-actor van de instantie krijgt de geërfde chip.
    stg = {a["naam"]: a for a in res["actoren"]}["Stichting Democratie en Media"]
    assert stg["verantwoordt"] == ["eigendom"] and stg["n_geerfd"] == 1, stg
    print("  overerving: OK")


if __name__ == "__main__":
    print("test_machtsvalentie:")
    test_parser()
    test_afleiding()
    test_voorgesteld_telt_pas_na_merge()
    test_overerving_verantwoording()
    print("ALLE TESTS GESLAAGD")
