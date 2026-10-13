#!/usr/bin/env python3
"""
End-to-end-test van de looptijdregel (eigenaarsbesluit 2026-10-09: "vul bij alles de goede
jaartallen in he want het model kijkt gewoon per tijdsvak wat de relaties zijn.. zorg ook dat dit
overal wordt gehandhaafd"):

  * de goedkeurpoort (looptijd_reden): geen begin → niet goedkeurbaar, behalve een registerfeit
    of een vastgelegde vergeefse zoektocht; kill-switch PROPAGANDA_LOOPTIJD_POORT=0;
  * POST /api/looptijd_onderzoek: alleen de datumzoeker (gezocht/niets_gevonden/fout), de
    registercheck (register_zonder_datum) of een maintainer;
  * een datum-aspect moet JJJJ[-MM[-DD]] zijn;
  * /api/beoordeling/looptijd/<arg>: pas na A1 'klopt' en de stemtoets; zet alleen een leeg veld
    (oud/nieuw in edit_log), merget het argument, weigert een begin na het einde;
  * scripts/datumzoeker.py: kandidaten en volgorde, wachttijden, de eigen-bronnenronde (alleen
    een letterlijk stuk van een bestaand citaat dat het jaar noemt), de webronde (natrekken,
    beide partijen) en de ronde met een nagebootst model;
  * scripts/automatische_beoordeling.py: stap 10c zet de datum, looptijd-argumenten wachten niet
    op de aanklager;
  * de geratchete controle RELATIE-ZONDER-JAAR;
  * scripts/nieuws_redactieleiding_doelen.py --periodiek: alleen wat > 90 dagen afgerond is.

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt. Geen
modelaanroepen: het taalmodel wordt nagebootst.

Gebruik: python3 scripts/test_datumzoeker.py
Exit-code 0 = alles groen.
"""
import argparse
import datetime
import importlib.util
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def laad_script(naam):
    spec = importlib.util.spec_from_file_location(naam, ROOT / "scripts" / f"{naam}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def main():
    os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
    os.environ["PROPAGANDA_STEMTOETS"] = "1"
    os.environ["PROPAGANDA_LOOPTIJD_POORT"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "vers.db"
        print("1. Verse build (schema → theorie → instanties)")
        for naam, functie in (("init_db", "init_db"), ("seed_theoretical_model", "seed"),
                              ("seed_from_ai_source", "seed")):
            module = laad_script(naam)
            module.DB_PATH = db
            getattr(module, functie)()

        import auth
        import server
        import validation
        import automatische_beoordeling as ab
        import bronchecker as bc
        import bronzoeker as bz
        import datumzoeker as dz
        import stemtoets as st
        import nieuws_redactieleiding_doelen as rl
        server.DB_PATH = db
        server._rate_emmers.clear()
        for module in (ab, bc, bz, dz, st, rl):
            module.DB_PATH = db

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        eis(conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'looptijd_onderzoek'").fetchone()
            is not None, "schema.sql heeft de tabel looptijd_onderzoek")
        tokens = {}
        for naam, rol, kind in (("nieuws-scout", "bijdrager", "agent"),
                                ("bronchecker", "bijdrager", "agent"),
                                ("merge-service", "reviewer", "agent"),
                                ("datumzoeker", "bijdrager", "agent"),
                                ("registercheck", "bijdrager", "agent"),
                                ("stemtoets", "bijdrager", "agent"),
                                ("t-admin", "maintainer", "mens")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT OR IGNORE INTO users (username, kind, role, provenance, "
                         "token_hash) VALUES (?, ?, ?, 'test', ?)",
                         (naam, kind, rol, auth.hash_token(tokens[naam])))
            conn.execute("UPDATE users SET role = ?, kind = ?, token_hash = ? WHERE username = ?",
                         (rol, kind, auth.hash_token(tokens[naam]), naam))
        conn.commit()
        MECH = conn.execute("SELECT id FROM mechanisms WHERE NOT vervangen ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

        client = server.app.test_client()
        kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

        def api(methode, pad, naam, body=None):
            server._rate_emmers.clear()
            r = getattr(client, methode)(pad, json=body, headers=kop[naam])
            return r.status_code, (r.get_json() or {})

        def via_client(method, pad, token, body=None):
            server._rate_emmers.clear()
            r = client.open(pad, method=method, json=body, headers={"Authorization": f"Bearer {token}"})
            return r.status_code, (r.get_json() or {})

        ab.req = via_client
        bz.api_post = lambda api_url, token, pad, body: via_client("POST", pad, token, body)
        dz.bz.api_post = bz.api_post
        tokpad = Path(tmp) / "datumzoeker.token"
        tokpad.write_text(tokens["datumzoeker"])
        dz.DEFAULT_TOKEN = tokpad
        dz.LOG_PATH = Path(tmp) / "datumzoeker_log.jsonl"

        def lees():
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            return c

        def rij(tabel, rid):
            c = lees()
            try:
                return c.execute(f"SELECT * FROM {tabel} WHERE id = ?", (rid,)).fetchone()
            finally:
                c.close()

        teller = {"n": 0}

        def bron():
            teller["n"] += 1
            s, j = api("post", "/api/sources", "nieuws-scout",
                       {"title": f"Testbron {teller['n']}", "source_type": "nieuwsartikel",
                        "location": {"type": "url", "value": f"https://bron.test/{teller['n']}"}})
            assert s == 201, (s, j)
            return j["id"]

        def entiteit(naam_ent, typ="persoon"):
            s, j = api("post", "/api/entities", "nieuws-scout", {"name": naam_ent, "type": typ})
            assert s == 201, (s, j)
            api("patch", f"/api/entities/{j['id']}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
            return j["id"]

        def relatie(src, tgt, rtype="personeel", **extra):
            s, j = api("post", "/api/relations", "nieuws-scout",
                       {"source_id": src, "target_id": tgt, "relation_type": rtype, "mechanism_id": MECH, **extra})
            assert s == 201, (s, j)
            return j["id"]

        def bewijs(rid, quote="Jan Proef werkt bij Testkrant."):
            s, j = api("post", "/api/arguments", "nieuws-scout",
                       {"relation_id": rid, "stance": "supporting", "negeer_duplicaten": True,
                        "claim": f"Jan Proef werkt bij Testkrant (verband {rid}).",
                        "citations": [{"source_id": bron(), "quote": quote}]})
            assert s == 201, (s, j)
            s2, _ = api("post", f"/api/arguments/{j['id']}/merge", "t-admin")
            assert s2 == 200, s2
            return j["id"]

        def a1(arg_id, verdict="klopt"):
            s, j = api("post", f"/api/arguments/{arg_id}/herverificatie", "bronchecker",
                       {"verdict": verdict, "detail": "[bronchecker v3] test"})
            assert s in (200, 201), (s, j)

        def neutraal(arg_id):
            s, j = api("post", "/api/stemtoets", "stemtoets",
                       {"soort": "argument", "doel_id": arg_id, "verdict": "neutraal", "reden": "test",
                        "tekst_hash": st.tekst_hash(rij("arguments", arg_id)["claim"])})
            assert s in (200, 201), (s, j)

        print("2. De goedkeurpoort: zonder jaartal geen verband")
        c = lees()
        basis = validation.check_looptijd(c)[0]["aantal"]  # de seed draagt zelf verbanden zonder jaar
        c.close()
        jan, krant = entiteit("Jan Proef"), entiteit("Testkrant", "mediaorganisatie")
        r1 = relatie(jan, krant)
        bewijs(r1)
        c = lees()
        ok, redenen = server.bewijs_autokeur_toegestaan(c, "relations", r1)
        eis(not ok and any("looptijd" in x for x in redenen), f"geen begin → niet goedkeurbaar ({redenen[-1][:60]}…)")
        os.environ["PROPAGANDA_LOOPTIJD_POORT"] = "0"
        eis(not any("looptijd" in x for x in server.bewijs_autokeur_toegestaan(c, "relations", r1)[1]),
            "kill-switch PROPAGANDA_LOOPTIJD_POORT=0 zet de poort uit")
        os.environ["PROPAGANDA_LOOPTIJD_POORT"] = "1"
        c.close()
        s, j = api("post", "/api/looptijd_onderzoek", "nieuws-scout", {"relation_id": r1, "status": "niets_gevonden"})
        eis(s == 403, "alleen de datumzoeker, de registercheck of een maintainer legt zoekwerk vast")
        s, j = api("post", "/api/looptijd_onderzoek", "registercheck", {"relation_id": r1, "status": "niets_gevonden"})
        eis(s == 400, "de registercheck mag alleen 'register_zonder_datum' vastleggen")
        s, j = api("post", "/api/looptijd_onderzoek", "datumzoeker",
                   {"relation_id": r1, "status": "niets_gevonden", "detail": "Parlement.com, Villamedia"})
        eis(s == 201, "de datumzoeker legt een vergeefse zoektocht vast")
        c = lees()
        eis(not any("looptijd" in x for x in server.bewijs_autokeur_toegestaan(c, "relations", r1)[1]),
            "na een vastgelegde vergeefse zoektocht mag het verband zonder begin door")
        eis(validation.check_looptijd(c)[0]["aantal"] == basis, "RELATIE-ZONDER-JAAR telt een voorgesteld verband niet")
        c.close()
        r2 = relatie(jan, krant, "bestuurder", active_from="2019")
        bewijs(r2)
        c = lees()
        eis(not any("looptijd" in x for x in server.bewijs_autokeur_toegestaan(c, "relations", r2)[1]),
            "met een begin is de looptijd in orde")
        c.close()

        print("3. Een datum-aspect en het toepassen ervan")
        r3 = relatie(jan, krant, "adviseur")
        bewijs(r3)
        api("patch", f"/api/relations/{r3}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
        c = lees()
        eis(validation.check_looptijd(c)[0]["aantal"] == basis + 1, "RELATIE-ZONDER-JAAR telt een goedgekeurd verband zonder begin")
        c.close()
        s, j = api("post", "/api/arguments", "datumzoeker",
                   {"relation_id": r3, "property": "active_from", "property_value": "sinds kort",
                    "stance": "supporting", "claim": "Jan Proef adviseert Testkrant sinds 2021.",
                    "citations": [{"source_id": bron(), "quote": "Proef is sinds 2021 adviseur van Testkrant."}]})
        eis(s == 400, "een datum-aspect moet JJJJ, JJJJ-MM of JJJJ-MM-DD zijn")
        s, j = api("post", "/api/arguments", "datumzoeker",
                   {"relation_id": r3, "property": "active_from", "property_value": "2021-03",
                    "stance": "supporting", "claim": "Jan Proef adviseert Testkrant sinds maart 2021.",
                    "negeer_duplicaten": True,
                    "citations": [{"source_id": bron(), "quote": "Proef is sinds maart 2021 adviseur van Testkrant."}]})
        assert s == 201, (s, j)
        arg = j["id"]
        s, j = api("get", f"/api/beoordeling/looptijd/{arg}", "merge-service")
        eis(not j["toegestaan"] and any("A1" in x for x in j["redenen"]), "eerst A1 (bronchecker)")
        a1(arg)
        s, j = api("get", f"/api/beoordeling/looptijd/{arg}", "merge-service")
        eis(not j["toegestaan"] and any("stemtoets" in x for x in j["redenen"]), "dan de stemtoets")
        neutraal(arg)
        c = lees()
        eis(arg not in {a["id"] for a in ab.a2_wachtrij(c)}, "een looptijd-argument wacht niet op de aanklager")
        c.close()
        args = argparse.Namespace(droog=False)
        tel = ab.stap_looptijd(tokens["merge-service"], args, print)
        eis(tel["gezet"] == 1 and rij("relations", r3)["active_from"] == "2021-03",
            "stap 10c zet de datum (zo precies als de bron: jaar-maand)")
        eis(rij("arguments", arg)["status"] in ("ongecontroleerd", "geverifieerd"), "en merget het argument")
        c = lees()
        eis(c.execute("""SELECT COUNT(*) FROM edit_log WHERE table_name = 'relations' AND record_id = ?
                         AND reason LIKE 'automatische beoordeling: looptijd%'""", (r3,)).fetchone()[0] == 1,
            "met oud/nieuw en de reden in edit_log")
        eis(c.execute("SELECT status FROM looptijd_onderzoek WHERE relation_id = ?", (r3,)).fetchone()[0]
            == "gevonden", "looptijd_onderzoek: gevonden")
        eis(validation.check_looptijd(c)[0]["aantal"] == basis, "RELATIE-ZONDER-JAAR telt het niet meer")
        c.close()
        s, j = api("post", "/api/arguments", "datumzoeker",
                   {"relation_id": r3, "property": "active_from", "property_value": "2015",
                    "stance": "supporting", "claim": "Jan Proef adviseert Testkrant sinds 2015.",
                    "negeer_duplicaten": True,
                    "citations": [{"source_id": bron(), "quote": "Proef adviseert Testkrant al sinds 2015."}]})
        a1(j["id"])
        neutraal(j["id"])
        s, k = api("post", f"/api/beoordeling/looptijd/{j['id']}", "merge-service")
        eis(s == 409 and any("nooit overschrijven" in x for x in k["redenen"]), "een datum wordt nooit overschreven")
        s, j = api("post", "/api/arguments", "datumzoeker",
                   {"relation_id": r3, "property": "active_until", "property_value": "2020",
                    "stance": "supporting", "claim": "Jan Proef stopte in 2020 als adviseur van Testkrant.",
                    "negeer_duplicaten": True,
                    "citations": [{"source_id": bron(), "quote": "Proef stopte in 2020 bij Testkrant."}]})
        a1(j["id"])
        neutraal(j["id"])
        s, k = api("post", f"/api/beoordeling/looptijd/{j['id']}", "merge-service")
        eis(s == 409 and any("na het einde" in x for x in k["redenen"]), "een begin na het einde wordt geweigerd")

        print("4. De datumzoeker (nagebootst model)")
        piet, partij = entiteit("Piet Proef"), entiteit("Testpartij", "partij")
        r4 = relatie(piet, partij, "lidmaatschap")
        bewijs(r4, quote="Piet Proef is sinds 2011 lid van de Testpartij en zat van 2014 tot 2018 in het bestuur.")
        api("patch", f"/api/relations/{r4}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
        kees = entiteit("Kees Proef")
        r5 = relatie(kees, partij, "lidmaatschap")
        bewijs(r5, quote="Kees Proef is lid van de Testpartij.")
        api("patch", f"/api/relations/{r5}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
        c = lees()
        c.execute("INSERT OR REPLACE INTO nieuws_voorrang (relation_id, gevraagd_op, aantal) VALUES (?, '2026-10-09', 1)", (r5,))
        c.commit()
        kand = dz.kandidaten(c)
        eis(kand and kand[0]["id"] == r5, "wat het nieuws toont, gaat voor")
        eis(r3 not in {k["id"] for k in kand} and r2 not in {k["id"] for k in kand},
            "een verband met een begin is geen kandidaat")
        eis(r1 not in {k["id"] for k in kand}, "na 'niets gevonden' pas na 30 dagen opnieuw")
        nu = datetime.datetime.now()
        eis(dz.mag_weer({"status": "niets_gevonden", "laatste_poging": (nu - datetime.timedelta(days=31)).isoformat()}, nu)
            and not dz.mag_weer({"status": "fout", "laatste_poging": (nu - datetime.timedelta(hours=2)).isoformat()}, nu)
            and dz.mag_weer({"status": "register_zonder_datum", "laatste_poging": nu.isoformat()}, nu),
            "wachttijden: 30 dagen na niets, 20 uur na een fout, een registerfeit zonder begin meteen (als laatste)")
        c.close()
        eis(dz.schone_datum("2011") == "2011" and dz.schone_datum("per 2023-06-01") == "2023-06-01"
            and dz.schone_datum("2999") is None and dz.schone_datum("") is None,
            "alleen mogelijke datums (niet in de toekomst)")

        antwoorden = []

        def nep_vraag(prompt, schema, tools):
            antwoorden.append(tools)
            if not tools:  # de eigen-bronnenronde
                nummers = [int(r.split(".")[0]) for r in prompt.split("\n\n")[1:] if r[:1].isdigit()]
                uit = []
                for nr in nummers:
                    if "Piet Proef" in prompt.split("\n\n")[nummers.index(nr) + 1]:
                        uit.append({"nr": nr, "begin": "2011", "begin_citaat_nr": 1,
                                    "begin_citaat": "Piet Proef is sinds 2011 lid van de Testpartij",
                                    "eind": "2018", "eind_citaat_nr": 1,
                                    "eind_citaat": "verzonnen stuk dat niet in het citaat staat 2018",
                                    "bewering": "Piet Proef is sinds 2011 lid van de Testpartij."})
                    else:
                        uit.append({"nr": nr, "begin": "", "begin_citaat_nr": 0, "begin_citaat": "",
                                    "eind": "", "eind_citaat_nr": 0, "eind_citaat": "", "bewering": ""})
                return {"uitkomsten": uit}
            leeg = {"url": "", "titel": "", "uitgever": "", "datum": "", "soort": "website", "citaat": ""}
            return {"gevonden": False, "begin": "", "begin_bron": leeg, "eind": "", "eind_bron": leeg,
                    "bewering": "", "toelichting": "niets gevonden"}

        dz.vraag = nep_vraag
        tel = dz.draai(max_eigen=10, max_web=5, meld=print)
        eis(tel["uit_eigen_bronnen"] == 1 and tel["ingediend"] == 1,
            f"de eigen bron gaf het begin; een stuk dat niet letterlijk in het citaat staat telt niet ({tel})")
        c = lees()
        nieuw = c.execute("""SELECT * FROM arguments WHERE relation_id = ? AND property = 'active_from'""", (r4,)).fetchone()
        eis(nieuw is not None and nieuw["property_value"] == "2011" and nieuw["status"] == "voorgesteld"
            and nieuw["contributed_by"] == "datumzoeker", "een voorgesteld looptijd-argument van de datumzoeker")
        eis(c.execute("SELECT quote FROM citations WHERE argument_id = ?", (nieuw["id"],)).fetchone()[0]
            == "Piet Proef is sinds 2011 lid van de Testpartij", "met het letterlijke stuk van het bestaande citaat")
        eis(c.execute("SELECT status FROM looptijd_onderzoek WHERE relation_id = ?", (r5,)).fetchone()[0]
            == "niets_gevonden", "het web gaf niets: vastgelegd (niets_gevonden)")
        eis(True in antwoorden and False in antwoorden, "eerst de eigen bronnen (zonder tools), dan het web")
        c.close()

        def nep_web(prompt, schema, tools):
            b = {"url": "https://bron.test/kees", "titel": "Kees Proef", "uitgever": "Testkrant",
                 "datum": "2012-05-01", "soort": "nieuwsartikel",
                 "citaat": "Kees Proef werd in 2012 lid van de Testpartij, meldt de partij."}
            leeg = {**b, "url": "", "citaat": ""}
            return {"gevonden": True, "begin": "2012", "begin_bron": b, "eind": "", "eind_bron": leeg,
                    "bewering": "Kees Proef werd in 2012 lid van de Testpartij.", "toelichting": "persbericht"}

        dz.vraag = nep_web
        dz.bz.natrekken = lambda bron_, partijen=None: ({**bron_, "letterlijk": True, "datum": "2012-05-01"}, "ok")
        dz.bz.registreer_bron = lambda api_url, token, b: bron()
        tel = dz.draai(ids=[r5], max_eigen=0, max_web=3, meld=print)
        c = lees()
        web_arg = c.execute("""SELECT * FROM arguments WHERE relation_id = ? AND property = 'active_from'""", (r5,)).fetchone()
        eis(tel["van_het_web"] == 1 and web_arg is not None and web_arg["property_value"] == "2012",
            "met --ids zoekt hij ook na 'niets gevonden'; een webbron met het jaartal levert een argument")
        c.close()

        print("5. Redactieleiding elk kwartaal")
        c = lees()
        lijst = [{"sleutel": "redactieleiding:testkrant", "naam": "x"}, {"sleutel": "redactieleiding:nieuw", "naam": "y"},
                 {"sleutel": "redactieleiding:open", "naam": "z"}]
        oud = (datetime.datetime.now() - datetime.timedelta(days=100)).isoformat(timespec="seconds")
        for sleutel, status, wanneer in (("redactieleiding:testkrant", "klaar", oud),
                                         ("redactieleiding:open", "open", oud)):
            c.execute("""INSERT INTO nieuws_doelen (sleutel, naam, soort, status, aangemaakt, bijgewerkt)
                         VALUES (?, 'x', 'organisatie', ?, ?, ?)""", (sleutel, status, wanneer, wanneer))
        c.commit()
        beurt = rl.aan_de_beurt(c, lijst)
        eis([(d["sleutel"], d.get("opnieuw", False)) for d in beurt]
            == [("redactieleiding:testkrant", True), ("redactieleiding:nieuw", False)],
            "afgerond > 90 dagen geleden: opnieuw; nieuw: erbij; open: blijft staan")
        c.execute("UPDATE nieuws_doelen SET bijgewerkt = ? WHERE sleutel = 'redactieleiding:testkrant'",
                  (datetime.datetime.now().isoformat(timespec="seconds"),))
        c.commit()
        eis([d["sleutel"] for d in rl.aan_de_beurt(c, lijst)] == ["redactieleiding:nieuw"],
            "pas net afgerond: nog niet opnieuw")
        c.close()
    print("\nLooptijd: alles groen.")


if __name__ == "__main__":
    main()
