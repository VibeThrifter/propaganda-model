#!/usr/bin/env python3
"""test_bereik.py — bereikmeter: gesourcet publieksbereik per media-entiteit, per jaar.

Dekt de parser ('<maat>:<aantal>:<jaar>' + afwijzingen) en de afleiding (compute_bereik):
per entiteit een jaarreeks {jaar → grootste publieksmaat} + nieuwste punt uit `bereik`-
aspect-argumenten. Zelfstandig — bouwt een minimale in-memory DB (zelfde skelet als
test_doelgroep.py; de bereikmeter leest geen citaties/gewichten, alleen statussen).
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bereik  # noqa: E402


def test_parser():
    P = bereik._parse
    assert P("kijkers:650000:2024") == ("kijkers", 650000, 2024)
    assert P("oplage:350000:2015") == ("oplage", 350000, 2015)
    assert P("invullers:7800000:2023") == ("invullers", 7800000, 2023)
    for bad in ("", None, "kijkers:650000", "kijkers:650000:24", "kijkers:650000:20244",
                "kijkers:x:2024", "kijkers:-5:2024", "kijkers:0:2024",
                "lezersgroep:100:2024", "kijkers:650000:2024:extra", "kijkers:650000:17__"):
        try:
            P(bad)
            assert False, f"zou ValueError moeten geven: {bad!r}"
        except (ValueError, AttributeError, TypeError):
            pass
    print("  parser: OK")


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT);
        CREATE TABLE arguments (
            id INTEGER PRIMARY KEY, relation_id INT, mechanism_id INT, entity_id INT,
            property TEXT, property_value TEXT, status TEXT, claim TEXT,
            parent_argument_id INT, vervangen INT DEFAULT 0);
    """)
    conn.executemany("INSERT INTO entities VALUES (?,?,?)", [
        (1, "De Wereld Draait Door", "mediaorganisatie"),
        (2, "NRC", "mediaorganisatie"),
    ])
    return conn


def _arg(conn, aid, eid, pval, status="geverifieerd"):
    conn.execute("INSERT INTO arguments (id, entity_id, property, property_value, status, "
                 "claim) VALUES (?,?,?,?,?,?)",
                 (aid, eid, "bereik", pval, status, pval))


def test_afleiding():
    conn = _db()
    # DWDD: twee jaren, en in 2019 twee maten — de grootste publieksmaat wint per jaar.
    _arg(conn, 100, 1, "kijkers:1500000:2010")
    _arg(conn, 101, 1, "kijkers:900000:2019")
    _arg(conn, 102, 1, "online:400000:2019")     # kleiner → wint 2019 niet
    # NRC: oplage.
    _arg(conn, 200, 2, "oplage:350000:2015")
    conn.commit()

    res = bereik.compute_bereik(conn)
    ents = {o["naam"]: o for o in res["entiteiten"]}

    dwdd = ents["De Wereld Draait Door"]
    assert dwdd["reeks"] == {2010: 1500000, 2019: 900000}, dwdd["reeks"]
    assert dwdd["nieuwste"] == {"jaar": 2019, "aantal": 900000, "maat": "kijkers"}, dwdd["nieuwste"]
    assert dwdd["n_signalen"] == 3, dwdd["n_signalen"]

    nrc = ents["NRC"]
    assert nrc["reeks"] == {2015: 350000} and nrc["nieuwste"]["maat"] == "oplage", nrc

    # Onbruikbare property_value wordt overgeslagen, niet fataal.
    _arg(conn, 300, 2, "kijkers:onzin:2020")
    conn.commit()
    nrc2 = {o["naam"]: o for o in bereik.compute_bereik(conn)["entiteiten"]}["NRC"]
    assert nrc2["n_signalen"] == 1, nrc2
    print("  afleiding: OK")


def test_voorgesteld_telt_pas_na_merge():
    conn = _db()
    _arg(conn, 400, 1, "kijkers:1000000:2012", status="voorgesteld")
    conn.commit()
    assert bereik.compute_bereik(conn)["entiteiten"] == [], "voorgesteld telt in niets"
    prev = bereik.compute_bereik(conn, include_voorgesteld=True)
    assert prev["preview"] and prev["entiteiten"][0]["reeks"] == {2012: 1000000}, prev
    print("  voorgesteld-poort: OK")


if __name__ == "__main__":
    print("test_bereik:")
    test_parser()
    test_afleiding()
    test_voorgesteld_telt_pas_na_merge()
    print("ALLE TESTS GESLAAGD")
