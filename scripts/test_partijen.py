#!/usr/bin/env python3
"""test_partijen.py — partijnetwerk: wie is aan welke partij verbonden en welke posities.

Dekt de positie-indeling (klasse), de tellingen per partij ('alle' en 'nu'), de tijdtoets
(een positie buiten de periode van de partijband telt niet), de gedeelde organisaties, de
ontdubbeling en titels in het detail, en dat alleen goedgekeurde, niet-vervangen verbanden
meetellen. Zelfstandig — bouwt een minimale in-memory DB (zelfde aanpak als test_bereik.py).
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import partijen  # noqa: E402

PEILJAAR = 2026


def test_klasse():
    K = partijen.klasse
    min_fin = {"name": "Ministerie van Financiën", "type": "overheidsinstelling", "bestuurslaag": "rijk"}
    tk = {"name": "Tweede Kamer", "type": "overheidsinstelling", "bestuurslaag": "rijk"}
    ek = {"name": "Eerste Kamer", "type": "overheidsinstelling", "bestuurslaag": "rijk"}
    ep = {"name": "Europees Parlement", "type": "overheidsinstelling", "bestuurslaag": "eu"}
    gem = {"name": "Gemeente Utrecht", "type": "overheidsinstelling", "bestuurslaag": "gemeente"}
    cvdm = {"name": "CvdM", "type": "toezichthouder", "bestuurslaag": "rijk"}
    navo = {"name": "NAVO", "type": "overheidsinstelling", "bestuurslaag": None}
    assert K("ambt", "Minister van Financiën", min_fin) == "kabinet"
    assert K("ambt", "Staatssecretaris van Financiën", min_fin) == "kabinet"
    assert K("bestuurder", None, min_fin) == "kabinet"          # seed: bewindspersoon
    assert K("ambt", None, min_fin) == "kabinet"
    assert K("ambt", "Secretaris-generaal", min_fin) == "topambt"
    assert K("personeel", "Beleidsmedewerker", min_fin) == "overheid"
    assert K("ambt", "Kamerlid", tk) == "tweede_kamer"
    assert K("lidmaatschap", None, ek) == "eerste_kamer"
    assert K("ambt", "Europarlementariër (Renew)", ep) == "europarlement"
    assert K("personeel", "Beleidsmedewerker", ep) == "overheid"  # medewerker ≠ parlementariër
    assert K("ambt", "Wethouder", gem) == "wethouder"
    assert K("ambt", "Burgemeester (waarnemend)", gem) == "burgemeester"
    assert K("bestuurder", None, gem) == "gemeente"
    assert K("draaideur", None, cvdm) == "topambt"
    assert K("draaideur", None, navo) == "overheid"
    assert K("bestuurder", None, {"name": "ING", "type": "bedrijf"}) == "bedrijfsleven"
    assert K("draaideur", None, {"name": "NTR", "type": "omroep"}) == "media"
    assert K("lidmaatschap", None, {"name": "Bilderberg", "type": "elite_netwerk"}) == "elite_netwerk"
    print("  klasse: OK")


def _db():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT, bestuurslaag TEXT,
            description TEXT, status TEXT DEFAULT 'goedgekeurd', vervangen INT DEFAULT 0);
        CREATE TABLE mechanisms (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE relations (id INTEGER PRIMARY KEY, source_id INT, target_id INT,
            relation_type TEXT, functie TEXT, active_from TEXT, active_until TEXT,
            active INT DEFAULT 1, mechanism_id INT, status TEXT DEFAULT 'goedgekeurd',
            vervangen INT DEFAULT 0);
    """)
    conn.executemany("INSERT INTO entities (id, name, type, bestuurslaag) VALUES (?,?,?,?)", [
        (1, "Partij A", "partij", None),
        (2, "Partij B", "partij", None),
        (10, "Anna", "persoon", None),      # A, minister + bestuurder ING
        (11, "Bert", "persoon", None),      # A, oud-lid; Kamerlid tijdens lidmaatschap
        (12, "Cees", "persoon", None),      # B, bestuurder ING
        (13, "Dirk", "persoon", None),      # B, positie ná zijn lidmaatschap
        (14, "Eva", "persoon", None),       # alleen een voorgestelde band → telt niet
        (20, "Ministerie van Financiën", "overheidsinstelling", "rijk"),
        (21, "Tweede Kamer", "overheidsinstelling", "rijk"),
        (22, "ING", "bedrijf", None),
        (23, "Denktank A", "denktank", None),
        (24, "Oud bedrijf", "bedrijf", None),
    ])
    conn.execute("INSERT INTO mechanisms VALUES (92, 'partijlijn')")
    conn.executemany(
        "INSERT INTO relations (id, source_id, target_id, relation_type, functie, active_from, "
        "active_until, status, vervangen, mechanism_id) VALUES (?,?,?,?,?,?,?,?,?,?)", [
            # partijbanden (register: partij → persoon; seed: persoon → partij)
            (100, 1, 10, "lidmaatschap", None, None, None, "goedgekeurd", 0, 92),
            (101, 11, 1, "lidmaatschap", None, "2000", "2010", "goedgekeurd", 0, 92),
            (102, 2, 12, "lidmaatschap", None, None, None, "goedgekeurd", 0, 92),
            (103, 2, 13, "lidmaatschap", None, "1990", "1995", "goedgekeurd", 0, 92),
            (104, 1, 14, "lidmaatschap", None, None, None, "voorgesteld", 0, 92),
            # posities
            (200, 10, 20, "bestuurder", None, None, None, "goedgekeurd", 0, None),
            (201, 10, 20, "ambt", "Minister van Financiën", "2024", None, "goedgekeurd", 0, None),
            (202, 10, 22, "bestuurder", None, None, None, "goedgekeurd", 0, None),
            (203, 11, 21, "lidmaatschap", None, "2002", "2006", "goedgekeurd", 0, None),
            (204, 12, 22, "bestuurder", None, "2020", None, "goedgekeurd", 0, None),
            (205, 13, 22, "bestuurder", None, "2015", None, "goedgekeurd", 0, None),
            (206, 12, 24, "bestuurder", None, None, None, "goedgekeurd", 1, None),  # vervangen
            # banden van de partij zelf + een overige relatie van een lid
            (300, 1, 23, "alliantie", None, "1954", None, "goedgekeurd", 0, None),
            (301, 22, 10, "geschenk", None, "2025", "2025", "goedgekeurd", 0, None),
        ])
    conn.commit()
    return conn


def test_overzicht():
    o = partijen.compute_overzicht(_db(), peiljaar=PEILJAAR)
    per = {p["naam"]: p for p in o["partijen"]}
    a, b = per["Partij A"], per["Partij B"]
    # Eva's band is voorgesteld → niet verbonden; Bert is oud-lid (alle, niet nu).
    assert a["n_personen"] == [2, 1], a["n_personen"]
    assert a["telling"]["kabinet"] == [1, 1], a["telling"]
    assert a["telling"]["tweede_kamer"] == [1, 0], a["telling"]   # Bert: afgelopen
    assert a["telling"]["bedrijfsleven"] == [1, 1], a["telling"]
    # Dirk's ING-positie begon na zijn lidmaatschap → telt niet voor B.
    assert b["n_personen"] == [2, 1], b["n_personen"]
    assert b["telling"]["bedrijfsleven"] == [1, 1], b["telling"]
    # ING: mensen uit A én B → gedeeld; vervangen relatie (Oud bedrijf) telt nergens.
    gedeeld = {g["naam"]: g for g in o["gedeelde_organisaties"]}
    assert set(gedeeld) == {"ING"}, gedeeld
    assert gedeeld["ING"]["partijen"] == {"1": {"alle": 1, "nu": 1}, "2": {"alle": 1, "nu": 1}}
    assert [k["key"] for k in o["klassen"]][:3] == ["kabinet", "tweede_kamer", "eerste_kamer"]
    print("  overzicht: OK")


def test_partij_detail():
    conn = _db()
    d = partijen.compute_partij(conn, 1, peiljaar=PEILJAAR)
    pers = {p["naam"]: p for p in d["personen"]}
    assert set(pers) == {"Anna", "Bert"}, pers.keys()
    anna = pers["Anna"]
    # Ontdubbeld: de kale 'bestuurder' naast het registerambt valt weg uit de weergave.
    labels = [(x["label"], x["org"]["naam"]) for x in anna["posities"]]
    assert ("Minister van Financiën", "Ministerie van Financiën") in labels, labels
    assert ("bewindspersoon", "Ministerie van Financiën") not in labels, labels
    assert anna["hoofdklasse"] == "kabinet"
    assert [o["type"] for o in anna["overig"]] == ["geschenk"], anna["overig"]
    assert anna["overig"][0]["richting"] == "in"
    bert = pers["Bert"]
    assert bert["band_afgelopen"] and bert["posities"][0]["label"] == "Kamerlid", bert
    # Volgorde: lopende banden eerst.
    assert d["personen"][0]["naam"] == "Anna"
    assert [(o["type"], o["ander"]["naam"]) for o in d["organisaties"]] == [("alliantie", "Denktank A")]
    assert d["telling"]["kabinet"] == [1, 1]
    # Detail-tellingen = overzicht-tellingen.
    o = {p["id"]: p for p in partijen.compute_overzicht(conn, peiljaar=PEILJAAR)["partijen"]}
    assert d["telling"] == o[1]["telling"], (d["telling"], o[1]["telling"])
    # Dirk's positie staat wél bij hem, maar buiten de band.
    dirk = {p["naam"]: p for p in partijen.compute_partij(conn, 2, peiljaar=PEILJAAR)["personen"]}["Dirk"]
    assert dirk["posities"][0]["binnen_band"] is False and dirk["hoofdklasse"] is None, dirk
    assert partijen.compute_partij(conn, 10) is None      # persoon, geen partij
    assert partijen.compute_partij(conn, 999) is None
    print("  partij-detail: OK")


if __name__ == "__main__":
    test_klasse()
    test_overzicht()
    test_partij_detail()
    print("test_partijen: alles OK")
