#!/usr/bin/env python3
"""test_partijen.py — partijnetwerk: wie is aan welke partij verbonden en welke posities.

Dekt de positie-indeling (klasse), de tellingen per partij ('alle' en 'nu'), de tijdtoets
(een positie buiten de periode van de partijband telt niet), de gedeelde organisaties, de
ontdubbeling en titels in het detail, en dat alleen goedgekeurde, niet-vervangen verbanden
meetellen. Sinds 2026-10-13 ook: het bestaan van een partij begrenst haar banden (een
ongedateerd lidmaatschap van een opgeheven partij loopt niet meer) en fusies ('opgegaan_in')
vouwen een voorganger in bij de kolom van haar opvolger. En het mandaat per positie (gekozen,
afgeleid, benoemd, buiten het bestuur, onbepaald) met zijn tellingen. Zelfstandig — bouwt een minimale
in-memory DB (zelfde aanpak als test_bereik.py).
"""
import json
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
    assert K("ambt", "Secretaris-generaal", min_fin) == "ambtelijke_top"
    assert K("personeel", "Beleidsmedewerker", min_fin) == "ministerie"
    assert K("ambt", "Kamerlid", tk) == "tweede_kamer"
    assert K("lidmaatschap", None, ek) == "eerste_kamer"
    assert K("ambt", "Europarlementariër (Renew)", ep) == "europarlement"
    assert K("personeel", "Beleidsmedewerker", ep) == "politieke_staf"  # medewerker ≠ parlementariër
    assert K("ambt", "Wethouder", gem) == "wethouder"
    assert K("ambt", "Burgemeester (waarnemend)", gem) == "burgemeester"
    assert K("bestuurder", None, gem) == "decentraal_overig"
    assert K("draaideur", None, cvdm) == "mediabestel"   # media, ook al is het overheid
    assert K("draaideur", None, navo) == "internationaal"
    assert K("bestuurder", None, {"name": "ING", "type": "bedrijf"}) == "financieel"
    assert K("bestuurder", None, {"name": "Heineken", "type": "bedrijf"}) == "bedrijfsleven"
    assert K("draaideur", None, {"name": "NTR", "type": "omroep"}) == "publieke_omroep"
    assert K("lidmaatschap", None, {"name": "Bilderberg", "type": "elite_netwerk"}) == "elite_netwerk"
    # De benoemde staat: ambtelijke top, dan een bekende naam, dan de registersoort.
    def org(naam, oo=None, type_="overheidsinstelling"):
        return {"name": naam, "type": type_, "bestuurslaag": "rijk",
                "metadata": json.dumps({"oo_type": oo}) if oo else None}
    assert K("ambt", "Directeur-generaal", org("Directoraat-Generaal Politie en Veiligheidregio's (DGPenV)",
                                               "Organisatieonderdeel")) == "ambtelijke_top"
    assert K("ambt", "Directeur", org("CPB (Centraal Planbureau)", "Organisatieonderdeel")) == "planbureau"
    assert K("ambt", "Directeur-generaal", org("AIVD (Algemene Inlichtingen- en Veiligheidsdienst)")) == "veiligheid"
    assert K("ambt", "Voorzitter", org("ACM (Autoriteit Consument & Markt)", "Zelfstandig bestuursorgaan",
                                       "toezichthouder")) == "toezicht"
    assert K("ambt", "Voorzitter", org("Uitvoeringsinstituut Werknemersverzekeringen",
                                       "Zelfstandig bestuursorgaan")) == "uitvoering"
    assert K("ambt", "Inspecteur-generaal", org("IGJ (Inspectie Gezondheidszorg en Jeugd)", "Inspectie",
                                                "toezichthouder")) == "inspectie"
    assert K("ambt", "Vicepresident", org("Raad van State", "Hoog College van Staat")) == "hoge_colleges"
    assert K("ambt", "Voorzitter", org("Gezondheidsraad", "Adviescollege")) == "advies"
    assert K("ambt", "President", org("Hoge Raad der Nederlanden", "Rechtspraak", "rechterlijke_macht")) == "rechtspraak"
    assert K("ambt", "Directeur", org("Belastingdienst", "Organisatieonderdeel")) == "uitvoering"
    assert K("bestuurder", None, org("TU Delft")) == "onderwijs"
    # Kennisinstituten ook buiten de overheid (het Lareb is een stichting).
    assert K("bestuurder", None, {"name": "Bijwerkingencentrum Lareb", "type": "stichting"}) == "kennis"
    # Media apart: publieke omroep, pers en commercieel, mediaconcerns, het bestel.
    assert K("bestuurder", None, {"name": "NPO", "type": "stichting"}) == "publieke_omroep"
    assert K("personeel", None, {"name": "RTL Nieuws", "type": "omroep"}) == "pers_media"
    assert K("bestuurder", None, {"name": "DPG Media Group NV", "type": "bedrijf"}) == "pers_media"
    assert K("bestuurder", None, {"name": "Raad voor de Journalistiek", "type": "toezichthouder"}) == "mediabestel"
    assert K("personeel", None, {"name": "KPMG", "type": "bedrijf"}) == "consultancy"
    assert K("bestuurder", None, {"name": "FNV", "type": "vakbond"}) == "vakbond"
    assert K("lidmaatschap", None, {"name": "NAVO Parlementaire Assemblee", "type": "elite_netwerk"}) == "assemblee"
    assert {k for k, _, _ in partijen.KLASSEN} >= set(partijen.SLEUTEL_KLASSEN)
    print("  klasse: OK")


def test_mandaat():
    M = partijen.mandaat
    assert M("tweede_kamer", "ambt", "Kamerlid") == "kiezers"
    assert M("europarlement", "ambt", "Europarlementariër (Renew)") == "kiezers"
    assert M("eerste_kamer", "ambt", "Kamerlid") == "afgeleid"
    assert M("kabinet", "ambt", "Staatssecretaris van Financiën") == "afgeleid"   # niet 'secretaris'
    assert M("wethouder", "ambt", "Wethouder") == "afgeleid"
    assert M("burgemeester", "ambt", "Burgemeester (waarnemend)") == "benoemd"
    assert M("ambtelijke_top", "ambt", "Directeur-generaal") == "benoemd"
    assert M("overheid", "personeel", "Beleidsmedewerker") == "benoemd"
    assert M("bedrijfsleven", "bestuurder", None) == "buiten"
    assert M("mediabestel", "ambt", "Voorzitter", {"name": "CvdM", "type": "toezichthouder"}) == "benoemd"
    assert M("mediabestel", "bestuurder", None, {"name": "NVJ", "type": "vakbond"}) == "buiten"
    assert M("assemblee", "lidmaatschap", None) == "afgeleid"   # delegatie uit het parlement
    # Gemeente, provincie, waterschap: de ambtstitel beslist over klasse én mandaat.
    def KM(rel, functie, laag):
        org = {"name": f"{laag.title()} X", "type": "overheidsinstelling", "bestuurslaag": laag}
        k = partijen.klasse(rel, functie, org)
        return k, M(k, rel, functie, org)
    assert KM("ambt", "Statenlid", "provincie") == ("staten", "kiezers")
    assert KM("ambt", "Gedeputeerde", "provincie") == ("gedeputeerde", "afgeleid")
    assert KM("ambt", "Commissaris van de Koning", "provincie") == ("cdk_dijkgraaf", "benoemd")
    assert KM("ambt", "Raadslid gemeente Teylingen", "gemeente") == ("gemeenteraad", "kiezers")
    assert KM("ambt", "Duo-raadslid", "gemeente") == ("decentraal_overig", "afgeleid")   # benoemd door de raad
    assert KM("personeel", "Gemeentesecretaris", "gemeente") == ("decentraal_overig", "benoemd")
    assert KM("ambt", "Dijkgraaf", "waterschap") == ("cdk_dijkgraaf", "benoemd")
    assert KM("ambt", "Hoogheemraad", "waterschap") == ("gedeputeerde", "afgeleid")
    assert KM("ambt", "Lid algemeen bestuur", "waterschap") == ("waterschap_ab", "kiezers")
    assert KM("ambt", "Lid algemeen bestuur (geborgde zetel)", "waterschap") == ("decentraal_overig", "benoemd")
    # Zonder titel: een kaal lid zit in de raad, personeel is benoemd, een kale bestuurder
    # kan burgemeester of wethouder zijn → onbepaald (nooit gokken).
    assert KM("lidmaatschap", None, "gemeente") == ("gemeenteraad", "kiezers")
    assert KM("personeel", None, "gemeente") == ("decentraal_overig", "benoemd")
    assert KM("bestuurder", None, "gemeente") == ("decentraal_overig", "onbepaald")
    assert KM("draaideur", None, "gemeente") == ("decentraal_overig", "onbepaald")
    assert KM("lidmaatschap", "Lid rekenkamercommissie", "gemeente") == ("decentraal_overig", "onbepaald")
    # Een Kamercommissie is volksvertegenwoordiging, geen overige overheid.
    assert partijen.klasse("ambt", "Lid", {"name": "Vaste commissie voor Financiën (Tweede Kamer)",
                                           "type": "overheidsinstelling", "bestuurslaag": "rijk"}) == "kamercommissie"
    # De Commandant der Strijdkrachten is een functie bij Defensie, in het domein veiligheid.
    assert partijen.klasse("ambt", "Commandant der Strijdkrachten",
                           {"name": "Ministerie van Defensie", "type": "overheidsinstelling", "bestuurslaag": "rijk"}) == "veiligheid"
    assert {m["key"] for m in partijen._mandaten_lijst()} == set(partijen.MANDAAT_BLOK)
    print("  mandaat: OK")


def _db():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT, bestuurslaag TEXT,
            description TEXT, metadata TEXT, status TEXT DEFAULT 'goedgekeurd', vervangen INT DEFAULT 0,
            active_from TEXT, active_until TEXT);
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
    assert a["telling"]["financieel"] == [1, 1], a["telling"]
    # Dirk's ING-positie begon na zijn lidmaatschap → telt niet voor B.
    assert b["n_personen"] == [2, 1], b["n_personen"]
    assert b["telling"]["financieel"] == [1, 1], b["telling"]
    # ING: mensen uit A én B → gedeeld; vervangen relatie (Oud bedrijf) telt nergens.
    gedeeld = {g["naam"]: g for g in o["gedeelde_organisaties"]}
    assert set(gedeeld) == {"ING"}, gedeeld
    assert gedeeld["ING"]["partijen"] == {"1": {"alle": 1, "nu": 1}, "2": {"alle": 1, "nu": 1}}
    assert [k["key"] for k in o["klassen"]][:3] == ["burgemeester", "cdk_dijkgraaf", "ambtelijke_top"]
    # Mandaat: Anna minister (afgeleid) + ING (buiten), Bert oud-Kamerlid (kiezers, afgelopen).
    assert a["telling_mandaat"] == {"afgeleid": [1, 1], "buiten": [1, 1], "kiezers": [1, 0]}, a
    assert a["telling_blok"] == {"gekozen": [2, 1], "ongekozen": [1, 1]}, a["telling_blok"]
    assert a["telling_mk"]["afgeleid|kabinet"] == [1, 1], a["telling_mk"]
    assert [m["key"] for m in o["mandaten"]][:3] == ["kiezers", "afgeleid", "benoemd"]
    # Domein: Anna kabinet + bank, Bert oud-Kamerlid.
    # Domeinen: Anna kabinet (politiek bestuur) + bank, Bert oud-Kamerlid (volksvertegenwoordiging).
    assert a["telling_groep"] == {"bestuur": [1, 1], "markt": [1, 1], "volk": [1, 0]}, a["telling_groep"]
    assert a["telling_dblok"] == {"gekozen": [2, 1], "buiten": [1, 1]}, a["telling_dblok"]
    # Concreet in plaats van 'meer dan één domein': Anna is gekozen-politiek én in een netwerk.
    assert a["telling_kruis"] == {"gekozen_buiten": [1, 1]}, a["telling_kruis"]
    assert [g["blok"] for g in o["groepen"]][:1] == ["staat"] and [b["key"] for b in o["domeinblokken"]] == ["staat", "buiten", "gekozen"]
    print("  overzicht: OK")


def test_sleutelposities():
    """Kees is secretaris-generaal en lid van Partij A; Lena is directeur-generaal zonder
    partijband; een plaatsvervanger telt niet. Het CPB staat niet in het model."""
    conn = _db()
    conn.executescript("""
        INSERT INTO entities (id, name, type, bestuurslaag) VALUES
            (30, 'Kees', 'persoon', NULL), (31, 'Lena', 'persoon', NULL), (32, 'Piet', 'persoon', NULL);
        INSERT INTO relations (id, source_id, target_id, relation_type, functie, active_from, active_until, mechanism_id) VALUES
            (130, 1, 30, 'lidmaatschap', NULL, '1990', NULL, 92),
            (230, 30, 20, 'ambt', 'Secretaris-generaal', '2020', NULL, NULL),
            (231, 31, 20, 'ambt', 'Directeur-generaal Rijksbegroting', '2022', NULL, NULL),
            (232, 32, 20, 'ambt', 'Plaatsvervangend secretaris-generaal', '2021', NULL, NULL),
            (233, 31, 20, 'ambt', 'Secretaris-Generaal', '2015', NULL, NULL);
    """)
    o = partijen.compute_overzicht(conn, peiljaar=PEILJAAR)
    sp = o["sleutelposities"]
    f = {x["functie"]: x for x in sp["functies"]}
    assert list(f) == ["Secretaris-generaal", "Directeur-generaal Rijksbegroting"], f.keys()   # SG eerst
    sg = f["Secretaris-generaal"]
    assert sg["klasse"] == "ambtelijke_top" and [h["persoon"]["naam"] for h in sg["houders"]] == ["Kees", "Lena"], sg
    assert sg["houders"][0]["partijen"] == [{"id": 1, "naam": "Partij A", "afgelopen": False}], sg
    assert len(sp["functies"]) == 2   # 'Secretaris-Generaal' is dezelfde functie
    lena = f["Directeur-generaal Rijksbegroting"]["houders"][0]
    assert lena["persoon"]["naam"] == "Lena" and lena["partijen"] == [] and not lena["afgelopen"], lena
    cpb = {i["naam"]: i for i in sp["instituten"]}["Centraal Planbureau"]
    assert cpb["id"] is None and cpb["met_functie"] == [False, False], cpb
    # Kees telt ook in de partijmatrix, onder de ambtelijke top (benoemd).
    a = {p["naam"]: p for p in o["partijen"]}["Partij A"]
    assert a["telling"]["ambtelijke_top"] == [1, 1] and a["telling_dblok"]["staat"] == [1, 1], a
    assert "gekozen_staat" not in a["telling_kruis"], a["telling_kruis"]   # Kees is alleen SG
    print("  sleutelposities: OK")

    # De gaten als onderzoeksdoelen (scripts/sleutelposities_doelen.py): het ministerie krijgt
    # één doel met twee gaten (twee lopende SG's, politieke achtergrond), het CPB een instituut-doel.
    sys.path.insert(0, str(Path(__file__).parent))
    import sleutelposities_doelen as sd
    ds = {d["sleutel"]: d for d in sd.doelen(conn)}
    fin = ds["leiding:20"]
    assert fin["context"]["gaten"] == ["meerdere_houders", "politieke_achtergrond"], fin["context"]
    assert {h["persoon"] for h in fin["context"]["bekend_in_model"]} == {"Kees", "Lena"}, fin
    assert fin["soort"] == "organisatie" and fin["entity_id"] == 20 and fin["context"]["soort_doel"] == "sleutelpositie"
    assert ds["instituut:centraal-planbureau"]["entity_id"] is None
    assert ds["instituut:centraal-planbureau"]["context"]["gaten"] == ["ontbreekt"]
    print("  sleutelposities als doelen: OK")


def test_mandaat_gemeente():
    """Gijs: kale 'bestuurder' van Gemeente X naast het registerambt 'Burgemeester' → beide
    benoemd (dezelfde functie). Hans: alleen een kale bestuurder → onbepaald, in geen blok.
    Ilse: kaal lid van de gemeente (raadslid, rechtstreeks gekozen) en daarna wethouder."""
    conn = _db()
    conn.executescript("""
        INSERT INTO entities (id, name, type, bestuurslaag) VALUES
            (16, 'Gijs', 'persoon', NULL), (17, 'Hans', 'persoon', NULL), (18, 'Ilse', 'persoon', NULL),
            (25, 'Gemeente X', 'overheidsinstelling', 'gemeente');
        INSERT INTO relations (id, source_id, target_id, relation_type, functie, active_from, active_until, mechanism_id) VALUES
            (120, 2, 16, 'lidmaatschap', NULL, NULL, NULL, 92),
            (121, 2, 17, 'lidmaatschap', NULL, NULL, NULL, 92),
            (122, 2, 18, 'lidmaatschap', NULL, NULL, NULL, 92),
            (220, 16, 25, 'bestuurder', NULL, '2018', NULL, NULL),
            (221, 16, 25, 'ambt', 'Burgemeester', NULL, NULL, NULL),
            (222, 17, 25, 'bestuurder', NULL, '2019', NULL, NULL),
            (223, 18, 25, 'lidmaatschap', NULL, '2010', '2018', NULL),
            (224, 18, 25, 'ambt', 'Wethouder', '2018', NULL, NULL);
    """)
    b = {p["naam"]: p for p in partijen.compute_overzicht(conn, peiljaar=PEILJAAR)["partijen"]}["Partij B"]
    assert b["telling_mandaat"]["benoemd"] == [1, 1], b["telling_mandaat"]      # alleen Gijs
    assert b["telling_mandaat"]["onbepaald"] == [1, 1], b["telling_mandaat"]    # Hans
    assert b["telling_mandaat"]["kiezers"] == [1, 0], b["telling_mandaat"]      # Ilse, afgelopen
    assert b["telling_mandaat"]["afgeleid"] == [1, 1], b["telling_mandaat"]     # Ilse, wethouder
    assert b["telling_mk"]["kiezers|gemeenteraad"] == [1, 0], b["telling_mk"]
    # Blokken: Gijs + Cees (ING) niet gekozen, Ilse gekozen; Hans telt in geen van beide.
    assert b["telling_blok"] == {"ongekozen": [2, 2], "gekozen": [1, 1]}, b["telling_blok"]
    d = {p["naam"]: p for p in partijen.compute_partij(conn, 2, peiljaar=PEILJAAR)["personen"]}
    assert {x["mandaat"] for x in d["Gijs"]["posities"]} == {"benoemd"}, d["Gijs"]["posities"]
    assert [x["mandaat"] for x in d["Hans"]["posities"]] == ["onbepaald"], d["Hans"]["posities"]
    print("  mandaat gemeente: OK")


def test_bestaan_en_fusie():
    """Partij C (2000–2020-06-01) ging op in Partij A. Fien is ongedateerd lid van C en was
    in 2010 bestuurder bij ING: met fusies telt ze bij A ('alle', niet 'nu'), zonder fusies
    staat C apart met 'opgegaan_in'. Haar band eindigt effectief op het einde van C."""
    conn = _db()
    conn.executescript("""
        CREATE TABLE arguments (id INTEGER PRIMARY KEY, entity_id INT, relation_id INT,
            parent_argument_id INT, property TEXT, property_value TEXT, stance TEXT,
            status TEXT, vervangen INT DEFAULT 0);
        INSERT INTO entities (id, name, type, active_from, active_until)
            VALUES (3, 'Partij C', 'partij', '2000', '2020-06-01'), (15, 'Fien', 'persoon', NULL, NULL);
        INSERT INTO relations (id, source_id, target_id, relation_type, active_from, active_until, mechanism_id)
            VALUES (110, 15, 3, 'lidmaatschap', NULL, NULL, 92),
                   (210, 15, 22, 'bestuurder', '2010', '2012', NULL);
        INSERT INTO arguments (id, entity_id, property, property_value, stance, status)
            VALUES (1, 3, 'opgegaan_in', '1', 'supporting', 'ongecontroleerd'),
                   (2, 3, 'opgegaan_in', '2', 'supporting', 'voorgesteld');  -- telt niet
    """)
    o = partijen.compute_overzicht(conn, peiljaar=PEILJAAR)
    per = {p["naam"]: p for p in o["partijen"]}
    assert "Partij C" not in per, per.keys()                       # opgevouwen in A
    a = per["Partij A"]
    assert a["voorgangers"] == [{"id": 3, "naam": "Partij C", "looptijd": "2000–2020"}], a
    assert a["n_personen"] == [3, 1], a["n_personen"]              # Anna, Bert, Fien; nu: Anna
    assert a["telling"]["financieel"] == [2, 1], a["telling"]   # Anna (nu) + Fien (2010)
    los = {p["naam"]: p for p in partijen.compute_overzicht(conn, peiljaar=PEILJAAR, fusies=False)["partijen"]}
    assert los["Partij C"]["n_personen"] == [1, 0], los["Partij C"]   # band afgelopen met C
    assert los["Partij C"]["opgegaan_in"][0]["naam"] == "Partij A", los["Partij C"]
    assert los["Partij A"]["n_personen"] == [2, 1], los["Partij A"]
    d = partijen.compute_partij(conn, 1, peiljaar=PEILJAAR)
    fien = {p["naam"]: p for p in d["personen"]}["Fien"]
    assert fien["band"][0]["partij"]["naam"] == "Partij C" and fien["band"][0]["afgelopen"], fien
    assert fien["band"][0]["looptijd"] == "tot 2020", fien["band"][0]
    assert fien["band"][0]["einde_door"]["naam"] == "Partij C", fien["band"][0]
    assert d["partij"]["voorgangers"][0]["naam"] == "Partij C", d["partij"]
    assert {p["naam"] for p in partijen.compute_partij(conn, 1, peiljaar=PEILJAAR, fusies=False)["personen"]} \
        == {"Anna", "Bert"}
    # Op de dag: in 2020 zelf liep C nog (jaarprecisie), vandaag (na 2020-06-01) niet meer.
    assert partijen.compute_overzicht(conn, peiljaar=2020, fusies=False)["partijen"][-1] is not None
    c2020 = {p["naam"]: p for p in partijen.compute_overzicht(conn, peiljaar=2020, fusies=False)["partijen"]}
    assert c2020["Partij C"]["n_personen"] == [1, 1], c2020["Partij C"]
    vandaag = {p["naam"]: p for p in partijen.compute_overzicht(conn, fusies=False)["partijen"]}
    assert vandaag["Partij C"]["n_personen"] == [1, 0], vandaag["Partij C"]
    print("  bestaan en fusie: OK")


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
    assert anna["hoofdklasse"] == "financieel"   # ongekozen staat en netwerken gaan vóór
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


def test_per_jaar():
    """Per jaar: wat pas later begint, telt niet mee; een fusie telt pas als ze toen al was.
    Bert (lid 2000–2010, Kamerlid 2002–2006) is in 2004 lopend Kamerlid, in 1995 nog niets.
    Anna's ministerschap (sinds 2024) bestaat in 2004 nog niet."""
    conn = _db()
    a04 = {p["naam"]: p for p in partijen.compute_overzicht(conn, peiljaar=2004)["partijen"]}["Partij A"]
    assert a04["telling"]["tweede_kamer"] == [1, 1], a04["telling"]
    assert a04["n_personen"] == [2, 2], a04["n_personen"]          # Anna (ongedateerd) en Bert
    anna04 = {p["naam"]: p for p in partijen.compute_partij(conn, 1, peiljaar=2004)["personen"]}["Anna"]
    assert "Minister van Financiën" not in [x["label"] for x in anna04["posities"]], anna04["posities"]
    # Terugblik (gedateerd): alleen wat een begin heeft. Anna's band is ongedateerd → niet in 2004.
    o04 = partijen.compute_overzicht(conn, peiljaar=2004, gedateerd=True)
    a04g = {p["naam"]: p for p in o04["partijen"]}["Partij A"]
    assert a04g["n_personen"] == [1, 1] and o04["gedateerd"], a04g["n_personen"]   # alleen Bert
    assert o04["zonder_begin"]["banden"] >= 2, o04["zonder_begin"]               # Anna, Cees
    a95 = {p["naam"]: p for p in partijen.compute_overzicht(conn, peiljaar=1995)["partijen"]}["Partij A"]
    assert a95["n_personen"] == [1, 1], a95["n_personen"]          # Bert nog geen lid
    # Fusie: Partij C ging op 2020-06-01 op in A. In 2015 staat C apart, vandaag niet.
    conn.executescript("""
        CREATE TABLE arguments (id INTEGER PRIMARY KEY, entity_id INT, relation_id INT,
            parent_argument_id INT, property TEXT, property_value TEXT, stance TEXT,
            status TEXT, vervangen INT DEFAULT 0);
        INSERT INTO entities (id, name, type, active_from, active_until)
            VALUES (3, 'Partij C', 'partij', '2000', '2020-06-01'), (15, 'Fien', 'persoon', NULL, NULL);
        INSERT INTO relations (id, source_id, target_id, relation_type, active_from, active_until, mechanism_id)
            VALUES (110, 15, 3, 'lidmaatschap', '2005', NULL, 92);
        INSERT INTO arguments (id, entity_id, property, property_value, stance, status)
            VALUES (1, 3, 'opgegaan_in', '1', 'supporting', 'ongecontroleerd');
    """)
    in2015 = {p["naam"] for p in partijen.compute_overzicht(conn, peiljaar=2015)["partijen"]}
    assert "Partij C" in in2015, in2015
    assert "Partij C" not in {p["naam"] for p in partijen.compute_overzicht(conn)["partijen"]}
    print("  per jaar: OK")


if __name__ == "__main__":
    test_klasse()
    test_mandaat()
    test_overzicht()
    test_mandaat_gemeente()
    test_sleutelposities()
    test_partij_detail()
    test_bestaan_en_fusie()
    test_per_jaar()
    print("test_partijen: alles OK")
