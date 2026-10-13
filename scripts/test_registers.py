#!/usr/bin/env python3
"""Test van de registerpijplijn (Uitbreiding C, eigenaarsbesluit 2026-10-07).

Op een verse database (schema.sql + theorie-seed) met een klein, zelfgebouwd register van
overheidsorganisaties:
  1. naamontleding en partijtabel (tools/registers/common.py);
  2. het plan (naar_model.Plan): selectie, rollen, verbanden, voorletters met toevoeging,
     geen koppeling op naam alleen (het "Mw. A. van Dam ≠ Marcel van Dam"-geval, vijf
     "J. de Vries"-bestuurders tegen één "Jack de Vries");
  3. indienen via REST onder `register-import` (Flask test_client);
  4. de registercheck: 'klopt' op de echte regels, 'klopt-niet' op een vervalst citaat;
  5. de bronchecker en de bronzoeker slaan registerargumenten over;
  6. A7 merget registerfeiten zonder A2/smaadtoets en de automatische beoordeling keurt ze
     goed binnen het eigen registerplafond;
  7. de Tweede Kamer (tk.py, tk_naar_model.py): Kamerleden (dubbele achternaam, naamgenoot),
     fractie, nevenfunctie, loopbaan, geschenk; partij-eigen, politieke ambten en de Kamer als
     betaler blijven weg; idempotent; de registercheck ziet een verlegd ambt;
  8. het Europees Parlement (ep.py, ep_naar_model.py): zetel en nationale partij;
  9. het lobbyistenregister (lobby.py, lobby_naar_model.py): de pdf-tabel, lobbyt → Tweede Kamer;
 10. de registers-sync: een ambt dat verdwijnt loopt af; de stroomonderbreker bij een halve uitgave.
De live database wordt niet aangeraakt.

Gebruik: python3 scripts/test_registers.py   (exit 0 = alles groen)
"""
import importlib.util
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "registers"))

NS = "https://organisaties.overheid.nl/static/schema/oo/export/2.6.13"


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def laad_script(naam):
    spec = importlib.util.spec_from_file_location(naam, ROOT / "scripts" / f"{naam}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def org(sid, naam, typ, inhoud="", ministerie=None, functies="", kinderen="", afk=None):
    rel = (f'<p:relatieMetMinisterie p:systeemId="{ministerie[0]}">{ministerie[1]}'
           f'</p:relatieMetMinisterie>' if ministerie else "")
    return (f'<p:organisatie p:systeemId="{sid}"><p:naam>{naam}</p:naam>'
            + (f"<p:afkorting>{afk}</p:afkorting>" if afk else "")
            + f"<p:types><p:type>{typ}</p:type></p:types>{rel}{inhoud}"
            + f'<p:identificatiecodes><p:resourceIdentifier p:naam="Organisatiecode">oorg{sid}'
              f"</p:resourceIdentifier></p:identificatiecodes>"
            + (f"<p:functies>{functies}</p:functies>" if functies else "")
            + (f"<p:organisaties>{kinderen}</p:organisaties>" if kinderen else "")
            + "</p:organisatie>")


def functie(fid, naam, mensen):
    meds = "".join(
        f'<p:medewerker p:systeemId="{mid}"><p:naam>{n}</p:naam>'
        + (f"<p:partijLidmaatschap>{partij}</p:partijLidmaatschap>" if partij else "")
        + (f"<p:startDatum>{start}</p:startDatum>" if start else "")
        + "<p:adressen><p:adres><p:woonplaats>NIET-INLEZEN</p:woonplaats></p:adres></p:adressen>"
        + "</p:medewerker>"
        for mid, n, partij, start in mensen)
    return f'<p:functie p:systeemId="{fid}"><p:naam>{naam}</p:naam><p:medewerkers>{meds}</p:medewerkers></p:functie>'


def fixture_xml() -> str:
    fin = ("100", "Financiën")
    orgs = [
        org("100", "Financiën", "Ministerie",
            functies=functie(1, "Minister van Financiën", [(11, "dhr. E. (Eelco) Heinen MSc", "VVD", "2024-07-02")])
            + functie(2, "Secretaris-generaal", [(12, "mw. drs. A. (Anna) Proef", None, "2023-01-01")]),
            kinderen=org("101", "Directoraat-generaal Toeslagen", "Organisatieonderdeel",
                         functies=functie(3, "Directeur-generaal", [(13, "dhr. C. (Coen) van Louw", None, None)]))),
        org("200", "Testagentschap", "Agentschap", ministerie=fin,
            functies=functie(4, "Directeur-generaal", [(14, "mw. B. (Bea) Voorbeeld", None, "2022-05-01")])),
        org("300", "Testautoriteit", "Zelfstandig bestuursorgaan", ministerie=fin, afk="TA",
            functies=functie(5, "Voorzitter", [(15, "dhr. mr. C.D. Ezel", None, None)])),
        org("301", "Keuringsinstanties ex Testwet", "Zelfstandig bestuursorgaan", ministerie=fin),
        org("400", "Testraad", "Adviescollege", ministerie=fin,
            functies=functie(6, "Voorzitter", [(16, "mw. prof. dr. D. (Dora) Advies", None, None)])),
        org("500", "Gemeente Teststad", "Gemeente",
            functies=functie(7, "Burgemeester", [(17, "Dhr. B.C.M. Vostermans", "CDA", None)])
            + functie(8, "Wethouder", [(18, "Mw. A. van Dam", "Lokaal Belang", None),
                                       (19, "Dhr. Fortuin", "CDA", None)])
            + functie(9, "Raadslid", [(20, "Dhr. R. Raad", "CDA", None)])),
    ]
    # vijf verschillende "J. … de Vries"-bestuurders in vijf gemeenten
    for i, vl in enumerate(("J.", "J.M.", "J.G.", "J.D.", "J.A."), start=1):
        orgs.append(org(str(600 + i), f"Gemeente Vries{i}", "Gemeente",
                        functies=functie(60 + i, "Burgemeester", [(600 + i, f"Dhr. {vl} de Vries", None, None)])))
    return (f'<?xml version="1.0" encoding="UTF-8"?><p:overheidsorganisaties p:timestamp="2026-01-01T00:00:00+01:00" '
            f'xmlns:p="{NS}"><p:organisaties>{"".join(orgs)}</p:organisaties></p:overheidsorganisaties>')


THEORIE_ROLLEN = [("departement", "formele_macht"), ("uitvoeringsorganisatie", "formele_macht"),
                  ("adviesorgaan", "kennis_advies"), ("controleorgaan", "tegenmacht"),
                  ("parlementair_controleur", "tegenmacht"), ("bestuursrechter", "tegenmacht"),
                  ("decentrale_overheid", "formele_macht"), ("toezichthouder", "tegenmacht"),
                  ("elite_forum", "ideologie"), ("bewindspersoon", "formele_macht"),
                  ("topambtenaar", "formele_macht"), ("lokale_bestuurder", "formele_macht"),
                  ("politicus", "systeemactor"), ("partij", "systeemactor")]
THEORIE_MECH = [("hierarchische_aansturing", "formele_macht", "departement", "uitvoeringsorganisatie"),
                ("verzelfstandigd_bestuur", "formele_macht", "departement", "uitvoeringsorganisatie"),
                ("institutioneel_advies", "kennis_advies", "adviesorgaan", "departement"),
                ("ministeriele_verantwoordelijkheid", "formele_macht", "bewindspersoon", "departement"),
                ("ambtelijke_leiding", "formele_macht", "topambtenaar", "departement"),
                ("lokaal_bestuursmandaat", "formele_macht", "lokale_bestuurder", "decentrale_overheid"),
                ("kamerzetel", "formele_macht", "politicus", "parlementair_controleur"),
                ("partijlijn", "sourcing", "partij", "politicus")]


def tk_fixture() -> dict:
    """Een kleine Kamer-uitgave in het formaat van tk.haal()."""
    def zetel(pid, roep, achter, fractie, afk, functie="Lid"):
        return {"Id": f"z-{pid}", "Functie": functie, "Van": "2023-12-06T00:00:00Z", "Persoon_Id": pid,
                "Persoon": {"Id": pid, "Titels": None, "Initialen": f"{roep[0]}.", "Roepnaam": roep,
                            "Voornamen": roep, "Tussenvoegsel": None, "Achternaam": achter},
                "FractieZetel": {"Fractie": {"Id": f"f-{afk}", "NaamNL": fractie, "Afkorting": afk}}}

    def neven(nid, pid, tekst):
        return {"Id": nid, "PersoonId": pid, "Omschrijving": tekst, "PeriodeVan": "2024-01-01T00:00:00Z",
                "PeriodeTotEnMet": None, "IsActief": True, "VergoedingSoort": "Onbezoldigd"}
    return {
        "bron": "tk", "opgehaald": "2026-01-01",
        "zetels": [zetel("p1", "Jan", "Testlid", "Christen-Democratisch Appèl", "CDA", "Fractievoorzitter"),
                   zetel("p2", "Anna", "Dubbel-Naam", "Volkspartij voor Vrijheid en Democratie", "VVD"),
                   zetel("p3", "Klaas", "Kamer", "Groep Testsplitsing", "Groep Testsplitsing")],
        "nevenfuncties": [neven("n1", "p1", "Bestuurslid Stichting Testfonds"),
                          neven("n2", "p1", "Voorzitter Stichting Ondersteuning Tweede Kamerfractie CDA"),
                          neven("n3", "p2", "Voorzitter Vrienden van de Testbank")],
        "loopbaan": [{"Id": "l1", "Persoon_Id": "p1", "Functie": "Directeur", "Werkgever": "Testbank Nederland",
                      "Van": "2015", "TotEnMet": "2020"},
                     {"Id": "l2", "Persoon_Id": "p2", "Functie": "Wethouder", "Werkgever": "Gemeente Teststad",
                      "Van": "2018", "TotEnMet": "2022"}],
        "reizen": [{"Id": "r1", "Persoon_Id": "p1", "Bestemming": "Brussel", "Doel": "Conferentie",
                    "Van": "2024-02-01T00:00:00Z", "TotEnMet": "2024-02-02T00:00:00Z",
                    "BetaaldDoor": "Tweede Kamer der Staten-Generaal"}],
        "geschenken": [{"Id": "g1", "Persoon_Id": "p2", "Datum": "2024-03-01T00:00:00Z",
                        "Omschrijving": "Ontvangen van de Gemeente Teststad een mok. De waarde is onbekend."},
                       {"Id": "g2", "Persoon_Id": "p2", "Datum": "2024-03-02T00:00:00Z",
                        "Omschrijving": "Ontvangen van de VVD een fles wijn."}],
    }


def lobby_pdf(pad):
    """Een pdf zoals het lobbyistenregister: drie kolommen, een cel die doorloopt."""
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    for x, y, tekst in ((36, 190, "Naam"), (164, 190, "Werkzaam bij / voor"), (320, 190, "Behartigt belangen voor"),
                        (43, 220, "A.B. Lobby"), (164, 220, "Testbank Nederland"), (320, 220, "Idem"),
                        (43, 231, "C.D. Bureau"), (164, 231, "Testlobby B.V."),
                        (320, 231, "Testbank, Dak- en thuisloze jongeren,"), (320, 242, "Gemeente Teststad"),
                        (43, 253, "E.F. Zelf"), (164, 253, "Fractiebureau CDA"), (320, 253, "Idem"),
                        (36, 800, "Laatst bijgewerkt: 01-01-2026")):
        page.insert_text((x, y), tekst, fontsize=8)
    doc.save(pad)


def ep_fixture() -> dict:
    """Een kleine EP-uitgave in het formaat van ep.haal()."""
    def lid(eid, voor, achter, fractie, org):
        return {"id": eid, "voornaam": voor, "achternaam": achter, "fractie": fractie,
                "lidmaatschappen": [{"soort": "parlement", "org": "org/ep-10", "van": "2024-07-16"},
                                    {"soort": "partij", "org": org, "van": "2024-07-16"}]}
    return {"bron": "ep", "opgehaald": "2026-01-01",
            "leden": [lid("e1", "Els", "Europa", "PPE", "org/1"), lid("e2", "Kim", "Van Kandidaat", "Renew", "org/2")],
            "organisaties": {"org/1": {"afkorting": "CDA", "naam": "Christen Democratisch Appèl"},
                             "org/2": {"afkorting": "VVD", "naam": "Volkspartij voor Vrijheid en Democratie"}}}


def tweede_kamer_en_theorie(conn):
    """Wat de Kamerimport in het model verwacht: de Tweede Kamer met oo:19432, de mechanismen voor
    belangen en werving, en een paar bestaande knopen om (niet) aan te koppelen."""
    for naam, cat in (("maatschappelijke_organisatie", "systeemactor"), ("belanghebbende", "systeemactor"),
                      ("kennisinstituut", "ideologie")):
        conn.execute("INSERT OR IGNORE INTO roles (name, category, description) VALUES (?, ?, 'test')", (naam, cat))
    rol = {n: i for i, n in conn.execute("SELECT id, name FROM roles")}
    for naam, filt in (("draaideurconstructie", "cross_filter"), ("nevenfunctie_verstrengeling", "belangen"),
                       ("geschenk_en_gastvrijheid", "belangen")):
        conn.execute("INSERT OR IGNORE INTO mechanisms (name, filter, description, effect, source_role_id, "
                     "target_role_id) VALUES (?, ?, 'test', 'test', ?, ?)",
                     (naam, filt, rol["politicus"], rol["belanghebbende"]))
    conn.execute("INSERT INTO entities (name, type, primary_role_id, status) VALUES "
                 "('Tweede Kamer der Staten-Generaal', 'overheidsinstelling', ?, 'goedgekeurd'), "
                 "('Testbank', 'bedrijf', ?, 'goedgekeurd'), ('Anna Dubbel', 'persoon', ?, 'goedgekeurd'), "
                 "('Klaas Kamer', 'persoon', ?, 'goedgekeurd')",
                 (rol["parlementair_controleur"], rol["belanghebbende"], rol["politicus"], rol["elite_forum"]))
    conn.execute("INSERT INTO externe_ids (entity_id, stelsel, waarde) SELECT id, 'oo', '19432' FROM entities "
                 "WHERE name = 'Tweede Kamer der Staten-Generaal'")
    conn.commit()


def main():
    import common
    print("1. Naamontleding en partijtabel")
    o = common.ontleed_naam
    eis(o("dhr. drs. A.C.C. (Christiaan) Rebergen")["weergave"] == "Christiaan Rebergen", "roepnaam tussen haakjes")
    eis(o("Mw. A. van Dam")["weergave"] == "A. van Dam" and not o("Mw. A. van Dam")["volledig"],
        "alleen voorletters blijft voorletters")
    eis(o("Dhr. Fortuin")["alleen_achternaam"], "aanhef + één naam = alleen achternaam")
    eis(o("Bgen (b.d.) drs. A.J.A. Beukering")["weergave"] == "A.J.A. Beukering", "(b.d.) is geen roepnaam")
    eis(o("Mw. Olde Meule")["achternaam"] == "Olde Meule", "aanhef + twee woorden = achternaam")
    eis(common.partij_naam("Volkspartij voor Vrijheid en Democratie (VVD)") == "VVD", "partij uit fractienaam")
    eis(common.partij_naam("Lokaal Belang") is None, "lokale partij krijgt geen knoop")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        db = tmp / "registers.db"
        for naam, fn in (("init_db", "init_db"), ("seed_theoretical_model", "seed")):
            m = laad_script(naam)
            m.DB_PATH = db
            getattr(m, fn)()
        conn = sqlite3.connect(db)
        for naam, cat in THEORIE_ROLLEN:
            conn.execute("INSERT OR IGNORE INTO roles (name, category, description) VALUES (?, ?, 'test')",
                         (naam, cat))
        rol = {n: i for i, n in conn.execute("SELECT id, name FROM roles")}
        for naam, filt, src, tgt in THEORIE_MECH:
            conn.execute("INSERT OR IGNORE INTO mechanisms (name, filter, description, effect, "
                         "source_role_id, target_role_id) VALUES (?, ?, 'test', 'test', ?, ?)",
                         (naam, filt, rol[src], rol[tgt]))
            conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) "
                         "SELECT id, ? FROM mechanisms WHERE name = ?", (filt, naam))
        conn.execute("INSERT INTO entities (name, type, primary_role_id, status) VALUES "
                     "('CDA', 'partij', ?, 'goedgekeurd'), ('VVD', 'partij', ?, 'goedgekeurd'), "
                     "('Marcel van Dam', 'persoon', ?, 'goedgekeurd'), "
                     "('Jack de Vries', 'persoon', ?, 'goedgekeurd')",
                     (rol["partij"], rol["partij"], rol["politicus"], rol["politicus"]))
        import auth
        tokens = {}
        for naam, rolnaam in (("maint", "maintainer"), ("register-import", "bijdrager"),
                              ("registercheck", "bijdrager"), ("merge-service", "reviewer")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT INTO users (username, kind, role, token_hash, provenance) "
                         "VALUES (?, 'agent', ?, ?, 'test')",
                         (naam, rolnaam, auth.hash_token(tokens[naam])))
        conn.commit()
        conn.close()

        import oo
        oo.MAP = tmp / "registers" / "oo"
        oo.MAP.mkdir(parents=True)
        pad = oo.MAP / "exportOO_2026-01-01.xml"
        pad.write_text(fixture_xml(), encoding="utf-8")
        (oo.MAP / "exportOO_2026-01-01.sha256").write_text(common.sha256_bestand(pad) + "\n")
        data = oo.lees(pad)
        eis(data["uitgave"] == "2026-01-01" and len(data["organisaties"]) == 12,
            f"uitgave gelezen ({len(data['organisaties'])} organisaties, {len(data['functies'])} functies)")
        eis("NIET-INLEZEN" not in json.dumps(data), "adresgegevens van medewerkers worden niet gelezen")

        print("2. Het plan")
        import naar_model
        naar_model.DB_PATH = db
        rconn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        naar_model.KOPPELINGEN = tmp / "koppelingen.json"
        naar_model.KOPPELINGEN.write_text(json.dumps({"organisaties": {}, "personen": {}}))
        plan = naar_model.Plan(data, rconn).maak()
        namen = {o_["naam"] for o_ in plan.orgs.values()}
        eis("Ministerie van Financiën" in namen and "Directoraat-generaal Toeslagen" in namen,
            "ministerie en directoraat-generaal geselecteerd")
        eis("Keuringsinstanties ex Testwet" not in namen, "zbo-categorie overgeslagen")
        personen = {p_["naam"]: p_ for p_ in plan.personen_plan.values()}
        eis("Eelco Heinen" in personen and "Anna Proef" in personen, "bewindspersoon en SG met volledige naam")
        eis("B.C.M. Vostermans (burgemeester Teststad)" in personen, "voorletters krijgen een toevoeging")
        eis(personen["A. van Dam (wethouder Teststad)"]["bestaand"] is None,
            "Mw. A. van Dam wordt NIET gekoppeld aan Marcel van Dam")
        vries = [p_ for n, p_ in personen.items() if "de Vries" in n]
        eis(len(vries) == 5 and all(p_["bestaand"] is None for p_ in vries),
            "vijf verschillende J. de Vries'en blijven vijf knopen (geen koppeling aan Jack de Vries)")
        eis(not any("Fortuin" in n or "Raad" in n for n in personen), "alleen-achternaam en raadsleden overgeslagen")
        soorten = {f"{r['type']}/{r['mechanisme']}" for r in plan.relaties}
        eis({"zeggenschap/hierarchische_aansturing", "zeggenschap/verzelfstandigd_bestuur",
             "adviseur/institutioneel_advies", "ambt/ministeriele_verantwoordelijkheid",
             "ambt/ambtelijke_leiding", "ambt/lokaal_bestuursmandaat", "lidmaatschap/partijlijn"} <= soorten,
            f"alle verbandsoorten in het plan ({len(plan.relaties)} verbanden)")
        eis(not any("Lokaal Belang" in r["claim"] for r in plan.relaties if r["type"] == "lidmaatschap"),
            "lokale partij geeft geen lidmaatschap")

        print("3. Indienen via REST (register-import)")
        import server
        server.DB_PATH = db
        server._rate_emmers.clear()
        client = server.app.test_client()

        def rest_voor(token):
            def rest(methode, pad, body=None):
                r = client.open(pad, method=methode, json=body,
                                headers={"Authorization": f"Bearer {token}"})
                return r.status_code, (r.get_json() or {})
            return rest

        ind = naar_model.Indiener(plan, rest_voor(tokens["register-import"]), None, print)
        bron_id = ind.bron()
        ind.organisaties()
        ind.personen()
        ind.relaties(bron_id)
        eis(ind.tel["relatie nieuw"] == len(plan.relaties) and not any(k.endswith("fout") for k in ind.tel),
            f"alles ingediend: {dict(ind.tel)}")
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        eis(conn.execute("SELECT COUNT(*) FROM externe_ids").fetchone()[0] >= 6, "externe id's vastgelegd")
        eis(conn.execute("SELECT bestuurslaag FROM entities WHERE name = 'Gemeente Teststad'").fetchone()[0]
            == "gemeente", "bestuurslaag gezet")
        eis(conn.execute("SELECT functie FROM relations WHERE relation_type = 'ambt' AND functie = "
                         "'Secretaris-generaal'").fetchone() is not None, "ambtstitel in relations.functie")
        # idempotent: tweede keer niets nieuws
        ind2 = naar_model.Indiener(naar_model.Plan(data, rconn).maak(),
                                   rest_voor(tokens["register-import"]), None, print)
        ind2.bron()
        ind2.organisaties()
        ind2.personen()
        ind2.relaties(bron_id)
        eis(ind2.tel["relatie nieuw"] == 0 and ind2.tel["org nieuw"] == 0, "een tweede run maakt niets dubbel")

        print("4. Registercheck")
        import registercheck
        registercheck.DB_PATH = db
        registercheck.post = lambda token, arg_id, body, api=None: (
            lambda r: (r.status_code, r.get_json() or {}))(
                client.post(f"/api/arguments/{arg_id}/herverificatie", json=body,
                            headers={"Authorization": f"Bearer {tokens['registercheck']}"}))
        registercheck.TOKEN = tmp / "rc.token"
        registercheck.TOKEN.write_text(tokens["registercheck"])
        # één citaat vervalsen: de registercheck moet dat zien
        vals = conn.execute("SELECT c.id, c.argument_id FROM citations c JOIN arguments a ON a.id = "
                            "c.argument_id JOIN relations r ON r.id = a.relation_id WHERE "
                            "r.relation_type = 'adviseur' LIMIT 1").fetchone()
        conn.execute("UPDATE citations SET quote = quote || ' (aangevuld)' WHERE id = ?", (vals["id"],))
        conn.commit()
        tel = registercheck.draai()
        eis(tel["klopt-niet"] == 1 and tel["klopt"] == len(plan.relaties) - 1,
            f"registercheck: {tel}")
        oordeel = conn.execute("SELECT verdict FROM immuun_oordelen WHERE argument_id = ? AND door = "
                               "'registercheck'", (vals["argument_id"],)).fetchone()[0]
        eis(oordeel == "klopt-niet", "vervalst citaat → klopt-niet")
        eis(registercheck.draai()["klopt"] == 0, "een tweede ronde beoordeelt niets opnieuw")

        print("5. Bronchecker en bronzoeker slaan registerfeiten over")
        import bronchecker
        import bronzoeker
        bronchecker.DB_PATH = db
        bronzoeker.DB_PATH = db
        # een gewoon argument (citatie zónder methode, niet-registerbron) blijft wél werk voor
        # de bronchecker — regressie op de NULL-valkuil in REGISTER_ARG_SQL
        conn.execute("INSERT INTO sources (title, source_type) VALUES ('Gewone bron', 'website')")
        gewone_bron = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO arguments (entity_id, stance, claim, status, contributed_by) "
                     "VALUES ((SELECT MIN(id) FROM entities), 'supporting', 'Gewone claim', "
                     "'voorgesteld', 'maint')")
        gewoon = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO citations (argument_id, source_id, quote) VALUES (?, ?, 'iets')",
                     (gewoon, gewone_bron))
        conn.commit()
        rc = registercheck.db()
        eis([k["id"] for k in bronchecker.kandidaten(rc)] == [gewoon],
            "bronchecker: alleen het gewone argument, geen registerargumenten in de wachtrij")
        eis(not [k for k in bronzoeker.kandidaten(rc) if k.get("id")],
            "bronzoeker: geen registerargumenten in de wachtrij")
        rc.close()

        print("6. A7 en goedkeuren")
        conn.execute("DELETE FROM citations WHERE argument_id = ?", (gewoon,))
        conn.execute("DELETE FROM arguments WHERE id = ?", (gewoon,))
        conn.commit()
        kop = {"Authorization": f"Bearer {tokens['merge-service']}"}
        gemerged = 0
        for (aid,) in conn.execute("SELECT id FROM arguments WHERE status = 'voorgesteld'").fetchall():
            r = client.post(f"/api/arguments/{aid}/auto_merge", headers=kop)
            gemerged += r.status_code == 200 and r.get_json().get("merged")
        eis(gemerged == len(plan.relaties) - 1, f"A7 merget de registerfeiten zonder A2/smaadtoets ({gemerged})")
        goed = 0
        for tabel in ("entities", "relations"):
            for (rid,) in conn.execute(f"SELECT id FROM {tabel} WHERE status = 'voorgesteld'").fetchall():
                r = client.post(f"/api/beoordeling/autokeur/{tabel}/{rid}", headers=kop)
                goed += bool(r.get_json().get("goedgekeurd"))
        nog = conn.execute("SELECT COUNT(*) FROM relations WHERE status = 'voorgesteld'").fetchone()[0]
        eis(nog == 1, f"alle registerverbanden goedgekeurd behalve het vervalste ({goed} goedgekeurd)")
        reg = conn.execute("SELECT COUNT(*) FROM edit_log WHERE reason LIKE "
                           "'automatische beoordeling (register)%'").fetchone()[0]
        eis(reg == goed, f"goedkeuringen tellen tegen het registerplafond ({reg})")

        print("7. Tweede Kamer (tk.py + tk_naar_model.py)")
        tweede_kamer_en_theorie(conn)
        import tk
        tk.MAP = tmp / "registers" / "tk"
        tk.MAP.mkdir(parents=True)
        pad = tk.MAP / "tk_2026-01-01.json"
        pad.write_text(json.dumps(tk_fixture(), ensure_ascii=False), encoding="utf-8")
        (tk.MAP / "tk_2026-01-01.sha256").write_text(common.sha256_bestand(pad) + "\n")
        tkdata = tk.lees(pad)
        import tk_naar_model
        rconn.close()
        rconn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        tplan = tk_naar_model.Plan(tkdata, rconn, {}).maak()
        tpers = {p_["naam"]: p_ for p_ in tplan.personen.values()}
        dubbel = conn.execute("SELECT id FROM entities WHERE name = 'Anna Dubbel'").fetchone()[0]
        eis(tpers["Anna Dubbel-Naam"]["bestaand"] == dubbel,
            "dubbele achternaam koppelt aan de bestaande politicus 'Anna Dubbel'")
        eis("Klaas Kamer (Tweede Kamerlid)" in tpers, "naamgenoot met een andere rol krijgt een toevoeging")
        tsoorten = sorted(f"{r['type']}/{r['mechanisme']}" for r in tplan.relaties)
        eis(tsoorten == sorted(["ambt/kamerzetel"] * 3 + ["lidmaatschap/partijlijn"] * 2
                               + ["bestuurder/nevenfunctie_verstrengeling", "bestuurder/draaideurconstructie",
                                  "geschenk/geschenk_en_gastvrijheid"]), f"Kamerverbanden: {tsoorten}")
        eis(list(tplan.nieuwe_orgs.values())[0]["naam"] == "Stichting Testfonds" and len(tplan.nieuwe_orgs) == 1,
            "alleen een organisatie met rechtsvorm komt er nieuw bij")
        redenen = {o_["reden"] for o_ in tplan.overgeslagen}
        eis({"uitgesloten", "politiek ambt", "partij", "uitgesloten of leeg"} <= redenen,
            "partij-eigen stichting, politiek ambt, eigen partij als gever en de Kamer als betaler overgeslagen")
        eis(not any("Vrienden" in str(k_.get("tekst")) for k_ in tplan.koppelingen),
            "'Voorzitter Vrienden van de Testbank' wordt niet de Testbank")
        tind = tk_naar_model.Indiener(tplan, rest_voor(tokens["register-import"]))
        tbron = tind.bron()
        tind.entiteiten()
        tind.relaties(tbron)
        eis(tind.tel["relatie nieuw"] == len(tplan.relaties) and not any("fout" in k for k in tind.tel),
            f"Kamerfeiten ingediend: {dict(tind.tel)}")
        rconn.close()
        rconn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        tind2 = tk_naar_model.Indiener(tk_naar_model.Plan(tkdata, rconn, {}).maak(),
                                       rest_voor(tokens["register-import"]))
        eis(not tind2.p.nieuwe_orgs, "tweede run: de stichting bestaat al")
        tind2.bron()
        tind2.entiteiten()
        tind2.relaties(tbron)
        eis(tind2.tel["relatie nieuw"] == 0 and tind2.tel["persoon nieuw"] == 0, "tweede run maakt niets dubbel")
        # het ambt van Klaas Kamer verleggen naar een gemeente: de registercheck moet dat zien
        verlegd = conn.execute("""SELECT r.id, a.id FROM relations r JOIN arguments a ON a.relation_id = r.id
            JOIN entities e ON e.id = r.source_id WHERE r.relation_type = 'ambt' AND e.name LIKE 'Klaas Kamer%'""").fetchone()
        conn.execute("UPDATE relations SET target_id = (SELECT id FROM entities WHERE name = 'Gemeente Teststad') "
                     "WHERE id = ?", (verlegd[0],))
        conn.commit()
        ttel = registercheck.draai()
        eis(ttel["klopt"] == len(tplan.relaties) - 1 and ttel["klopt-niet"] == 1, f"registercheck Kamer: {ttel}")
        eis(conn.execute("SELECT verdict FROM immuun_oordelen WHERE argument_id = ? AND door = 'registercheck'",
                         (verlegd[1],)).fetchone()[0] == "klopt-niet", "verlegd ambt → klopt-niet")
        tgemerged = 0
        for (aid,) in conn.execute("SELECT id FROM arguments WHERE status = 'voorgesteld'").fetchall():
            r = client.post(f"/api/arguments/{aid}/auto_merge", headers=kop)
            tgemerged += r.status_code == 200 and r.get_json().get("merged")
        eis(tgemerged == len(tplan.relaties) - 1, f"A7 merget de Kamerfeiten ({tgemerged})")

        print("8. Europees Parlement (ep.py + ep_naar_model.py)")
        conn.execute("INSERT INTO entities (name, type, primary_role_id, status) VALUES "
                     "('Europees Parlement', 'overheidsinstelling', ?, 'goedgekeurd'), "
                     "('Kim Kandidaat', 'persoon', ?, 'goedgekeurd')",
                     (conn.execute("SELECT id FROM roles WHERE name = 'parlementair_controleur'").fetchone()[0],
                      conn.execute("SELECT id FROM roles WHERE name = 'politicus'").fetchone()[0]))
        conn.commit()
        import ep
        import ep_naar_model
        ep.MAP = tmp / "registers" / "ep"
        ep.MAP.mkdir(parents=True)
        pad = ep.MAP / "ep_2026-01-01.json"
        pad.write_text(json.dumps(ep_fixture(), ensure_ascii=False), encoding="utf-8")
        (ep.MAP / "ep_2026-01-01.sha256").write_text(common.sha256_bestand(pad) + "\n")
        epdata = ep.lees(pad)
        eis(epdata["personen"]["e2"]["naam"] == "Kim van Kandidaat", "EP-tussenvoegsel wordt klein ('Van' → 'van')")
        rconn.close()
        rconn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        eplan = ep_naar_model.Plan(epdata, rconn).maak()
        eis(sorted(f"{r['type']}/{r['mechanisme']}" for r in eplan.relaties)
            == ["ambt/kamerzetel", "ambt/kamerzetel", "lidmaatschap/partijlijn", "lidmaatschap/partijlijn"],
            "zetel en nationale partij per Europarlementariër")
        eis(eplan.personen["e2"]["bestaand"] is None, "'Kim van Kandidaat' koppelt niet aan 'Kim Kandidaat'")
        eind = ep_naar_model.Indiener(eplan, rest_voor(tokens["register-import"]))
        eind.entiteiten()
        eind.relaties(eind.bron())
        eis(eind.tel["relatie nieuw"] == 4 and not any("fout" in k for k in eind.tel), f"EP ingediend: {dict(eind.tel)}")
        etel = registercheck.draai()
        eis(etel["klopt"] == 4 and etel["klopt-niet"] == 0, f"registercheck EP: {etel}")

        print("9. Lobbyistenregister (lobby.py + lobby_naar_model.py)")
        conn.execute("INSERT OR IGNORE INTO roles (name, category, description) VALUES ('lobbyist', 'sourcing', 'test')")
        conn.execute("INSERT OR IGNORE INTO mechanisms (name, filter, description, effect, source_role_id, target_role_id) "
                     "SELECT 'lobbytoegang', 'belangen', 'test', 'test', l.id, k.id FROM roles l, roles k "
                     "WHERE l.name = 'lobbyist' AND k.name = 'parlementair_controleur'")
        conn.commit()
        import lobby
        import lobby_naar_model
        lobby.MAP = tmp / "registers" / "lobby"
        lobby.MAP.mkdir(parents=True)
        pad = lobby.MAP / "lobby_2026-01-01.pdf"
        lobby_pdf(pad)
        (lobby.MAP / "lobby_2026-01-01.sha256").write_text(common.sha256_bestand(pad) + "\n")
        ldata = lobby.lees(pad)
        rijen = {r["naam"]: r for r in ldata["records"].values()}
        eis(ldata["uitgave"] == "2026-01-01" and len(rijen) == 3, f"pdf-tabel gelezen ({len(rijen)} rijen)")
        eis(rijen["C.D. Bureau"]["belangen"].endswith("Gemeente Teststad"), "een doorlopende cel hoort bij de rij erboven")
        rconn.close()
        rconn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        lplan = lobby_naar_model.Plan(ldata, rconn, {}).maak()
        lnamen = sorted(k_.get("model") or k_.get("nieuw") for k_ in lplan.koppelingen)
        eis(lnamen == ["Gemeente Teststad", "Testbank", "Testbank", "Testlobby B.V."], f"lobbyorganisaties: {lnamen}")
        eis(len(lplan.relaties) == 3 and all(r["type"] == "lobbyt" for r in lplan.relaties),
            "drie keer lobbyt → Tweede Kamer (de fractie niet, een opdrachtgever één keer)")
        lind = tk_naar_model.Indiener(lplan, rest_voor(tokens["register-import"]), bron=lobby,
                                      cluster=lobby_naar_model.CLUSTER)
        lind.entiteiten()
        lind.relaties(lind.bron())
        eis(lind.tel["relatie nieuw"] == 3 and not any("fout" in k for k in lind.tel), f"lobby ingediend: {dict(lind.tel)}")
        ltel = registercheck.draai()
        eis(ltel["klopt"] == 3 and ltel["klopt-niet"] == 0, f"registercheck lobby (pdf opnieuw gelezen): {ltel}")

        print("10. Registers-sync: een ambt dat uit het register verdwijnt, loopt af")
        import registers_sync
        registers_sync.DB_PATH = db
        pad = oo.MAP / "exportOO_2026-01-08.xml"
        pad.write_text(fixture_xml().replace(
            functie(6, "Voorzitter", [(16, "mw. prof. dr. D. (Dora) Advies", None, None)]), ""), encoding="utf-8")
        (oo.MAP / "exportOO_2026-01-08.sha256").write_text(common.sha256_bestand(pad) + "\n")
        rconn.close()
        uit = registers_sync.draai(alleen=["oo"], ophalen_aan=False, meld=print,
                                   rest=rest_voor(tokens["register-import"]), check_rest=rest_voor(tokens["registercheck"]))
        eis(uit["oo"]["afgelopen"] == 1 and not uit["oo"].get("fouten"), f"sync: {uit['oo']}")
        tot = conn.execute("""SELECT r.active_until FROM relations r JOIN entities e ON e.id = r.source_id
            WHERE e.name = 'Dora Advies' AND r.relation_type = 'ambt'""").fetchone()[0]
        eis(tot == "2026-01-08", "de voorzitter die het register niet meer noemt, krijgt de datum van de uitgave als einde")
        eis(conn.execute("SELECT COUNT(*) FROM edit_log WHERE reason LIKE 'registers-sync:%'").fetchone()[0] == 1,
            "met de reden in edit_log")
        r = client.post("/api/relations/1/looptijd", json={"active_until": "2026", "reden": "x"},
                        headers={"Authorization": f"Bearer {tokens['register-import']}"})
        eis(r.status_code == 403, "alleen de registercheck (of een maintainer) zet een einddatum")
        pad.write_text(fixture_xml().split("<p:organisaties>")[0] + "<p:organisaties>" + org("100", "Financiën", "Ministerie")
                       + "</p:organisaties></p:overheidsorganisaties>", encoding="utf-8")
        (oo.MAP / "exportOO_2026-01-08.sha256").write_text(common.sha256_bestand(pad) + "\n")
        oo._CACHE.clear() if hasattr(oo, "_CACHE") else None
        uit = registers_sync.draai(alleen=["oo"], ophalen_aan=False, meld=print,
                                   rest=rest_voor(tokens["register-import"]), check_rest=rest_voor(tokens["registercheck"]))
        eis("onderbreker" in uit["oo"], f"een halve uitgave haalt het model niet leeg: {uit['oo'].get('onderbreker')}")

        print("11. Looptijd uit het record (eigenaarsbesluit 2026-10-09)")
        import registers_looptijd
        pad.write_text(fixture_xml(), encoding="utf-8")
        (oo.MAP / "exportOO_2026-01-08.sha256").write_text(common.sha256_bestand(pad) + "\n")
        oo._CACHE.clear() if hasattr(oo, "_CACHE") else None
        heinen = conn.execute("""SELECT r.id, r.active_from FROM relations r JOIN entities e ON e.id = r.source_id
            WHERE e.name = 'Eelco Heinen' AND r.relation_type = 'ambt'""").fetchone()
        eis(heinen["active_from"] == "2024-07-02", "de import geeft een ambt het begin uit het record")
        conn.execute("UPDATE relations SET active_from = NULL WHERE id = ?", (heinen["id"],))  # een oude import
        conn.commit()
        uit = registers_looptijd.draai(alleen=["oo"], meld=print, rest=rest_voor(tokens["registercheck"]))
        eis(uit["oo"]["gezet"] >= 1 and not uit["oo"]["fouten"], f"backfill: {uit['oo']}")
        eis(conn.execute("SELECT active_from FROM relations WHERE id = ?", (heinen["id"],)).fetchone()[0]
            == "2024-07-02", "een verband zonder datum krijgt het begin uit zijn eigen record terug")
        eis(conn.execute("""SELECT COUNT(*) FROM edit_log WHERE table_name = 'relations' AND record_id = ?
            AND reason LIKE 'register-looptijd:%' AND old_value LIKE '%null%'""", (heinen["id"],)).fetchone()[0] == 1,
            "met oud/nieuw en de uitgave in edit_log")
        partij = conn.execute("""SELECT r.id FROM relations r JOIN entities e ON e.id = r.target_id
            WHERE e.name = 'Eelco Heinen' AND r.relation_type = 'lidmaatschap'""").fetchone()[0]
        eis(conn.execute("SELECT active_from FROM relations WHERE id = ?", (partij,)).fetchone()[0] is None
            and conn.execute("SELECT status FROM looptijd_onderzoek WHERE relation_id = ?", (partij,)).fetchone()[0]
            == "register_zonder_datum",
            "noemt het register geen begin (de partij van een minister), dan geen nep-begin maar een vastgelegde stand")
        uit = registers_looptijd.draai(alleen=["oo"], meld=print, rest=rest_voor(tokens["registercheck"]))
        eis(uit["oo"]["gezet"] == 0 and uit["oo"]["zonder_datum"] == 0, "een tweede run doet niets (idempotent)")
        r = client.post(f"/api/relations/{heinen['id']}/looptijd", json={"active_from": "2020", "reden": "x"},
                        headers={"Authorization": f"Bearer {tokens['registercheck']}"})
        eis(r.status_code == 400, "een datum wordt nooit overschreven")
        r = client.post(f"/api/relations/{heinen['id']}/looptijd", json={"active_from": "2024-07-02", "reden": "x"},
                        headers={"Authorization": f"Bearer {tokens['registercheck']}"})
        eis(r.status_code == 200 and r.get_json()["gewijzigd"] == [], "dezelfde datum is een no-op")
        conn.close()
    print("\nRegisterpijplijn: alles groen.")


if __name__ == "__main__":
    main()
