#!/usr/bin/env python3
"""
End-to-end-test van "instituut of persoon" (eigenaarsbesluit 2026-10-19: "denktank of instituut
zoals clingendael en universiteit stuurt experts naar de media … ook de experts zelf zou in het
propaganda model moeten komen … invloed gaat wss van clingendael via die expert naar media …
beide erin zetten?" — "voer uit"):

  * relations.namens_id: de API neemt hem aan bij een persoon als bron en weigert wat niet kan
    (geen persoon als bron, namens een persoon, de bron of het doel zelf, op een band);
    een maintainer zet of wist hem; omdraaien met een hoedanigheid die niet meer past, faalt;
  * de richtingtoets draait een verband met een hoedanigheid niet automatisch om;
  * ontdubbelen: een andere pet is een ander feit;
  * via_medewerkers.py: een route telt alleen met een goedgekeurde band die in die periode liep
    (een oud-medewerker niet), GET /api/via_medewerkers/<id>, viz_data neemt namens_id mee;
  * de controles NAMENS-ONGELDIG, NAMENS-ZONDER-BAND en INSTITUUT-VIA-PERSOON;
  * stap 10e (opschonen.overgezet_besluit, /api/beoordeling/overgezet): het oude argument gaat pas
    op vervangen als de opvolger gemerged is, zijn verband goedgekeurd en de band goedgekeurd; een
    verband zonder eigen bewijs daarna wordt afgewezen, een verband met institutioneel bewijs
    blijft; A1 'klopt-niet' op de opvolger telt niet; de ronde-stap telt mee.

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt. Geen
modelaanroepen.

Gebruik: python3 scripts/test_namens.py
Exit-code 0 = alles groen.
"""
import argparse
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
        import viz_data
        import opschonen
        import via_medewerkers
        import automatische_beoordeling as ab
        server.DB_PATH = db
        server._rate_emmers.clear()
        ab.DB_PATH = db

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        eis("namens_id" in {r[1] for r in conn.execute("PRAGMA table_info(relations)")},
            "schema.sql kent relations.namens_id")
        tokens = {}
        for naam, rol, kind in (("assistent", "bijdrager", "agent"),
                                ("bronchecker", "bijdrager", "agent"),
                                ("richtingtoets", "bijdrager", "agent"),
                                ("merge-service", "reviewer", "agent"),
                                ("t-admin", "maintainer", "mens")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT OR IGNORE INTO users (username, kind, role, provenance, "
                         "token_hash) VALUES (?, ?, ?, 'test', ?)",
                         (naam, kind, rol, auth.hash_token(tokens[naam])))
            conn.execute("UPDATE users SET role = ?, kind = ?, token_hash = ? WHERE username = ?",
                         (rol, kind, auth.hash_token(tokens[naam]), naam))
        conn.commit()
        mech = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM mechanisms WHERE NOT vervangen")}
        expert = mech.get("expert_framing") or next(iter(mech.values()))
        band_mech = mech.get("denktank_levert_expert") or expert
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
            s, j = api("post", "/api/sources", "assistent",
                       {"title": f"Testbron {teller['n']}", "source_type": "nieuwsartikel",
                        "location": {"type": "url", "value": f"https://bron.test/{teller['n']}"}})
            assert s == 201, (s, j)
            return j["id"]

        def entiteit(naam_ent, typ):
            s, j = api("post", "/api/entities", "assistent", {"name": naam_ent, "type": typ})
            assert s == 201, (s, j)
            api("patch", f"/api/entities/{j['id']}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
            return j["id"]

        def relatie(src, tgt, rtype, wie="t-admin", **extra):
            body = {"source_id": src, "target_id": tgt, "relation_type": rtype,
                    "mechanism_id": extra.pop("mechanism_id", expert), "active_from": extra.pop("active_from", "2020")}
            body.update(extra)
            return api("post", "/api/relations", wie, body)

        def argument(rid, claim, wie="t-admin", **extra):
            s, j = api("post", "/api/arguments", wie,
                       {"relation_id": rid, "stance": "supporting", "claim": claim,
                        "citations": [{"source_id": bron(), "quote": claim[:60]}], **extra})
            assert s == 201, (s, j)
            return j["id"]

        print("2. De API: namens_id aannemen en weigeren")
        inst = entiteit("Testinstituut Clingenhof", "denktank")
        ander = entiteit("Andere Denktank", "denktank")
        krant = entiteit("Testkrant", "mediaorganisatie")
        piet = entiteit("Piet Deskundige", "persoon")
        jan = entiteit("Jan Collega", "persoon")
        s, j = relatie(inst, krant, "beinvloeding", namens_id=ander)
        eis(s == 400 and "alleen een persoon" in j.get("error", ""), "een organisatie als bron draagt geen namens")
        s, j = relatie(piet, krant, "beinvloeding", namens_id=jan)
        eis(s == 400 and "geen persoon" in j.get("error", ""), "namens een persoon kan niet")
        s, j = relatie(piet, krant, "beinvloeding", namens_id=krant)
        eis(s == 400 and "derde organisatie" in j.get("error", ""), "namens het doel zelf kan niet")
        s, j = relatie(piet, inst, "personeel", namens_id=ander)
        eis(s == 400 and "band" in j.get("error", ""), "op een band (personeel) hoort geen namens")
        s, j = relatie(piet, krant, "beinvloeding", namens_id="abc")
        eis(s == 400, "namens_id moet een getal zijn")
        s, j = relatie(piet, krant, "beinvloeding", namens_id=inst, active_from="2018")
        eis(s == 201 and j.get("namens_id") == inst and j.get("status") == "goedgekeurd",
            "persoon → medium namens het instituut (maintainer: meteen goedgekeurd)")
        optreden = j["id"]
        s, j = api("patch", f"/api/relations/{optreden}", "t-admin", {"namens_id": jan, "motivatie": "test"})
        eis(s == 400, "PATCH naar een persoon als namens: 400")
        s, j = api("patch", f"/api/relations/{optreden}", "t-admin", {"namens_id": ander, "motivatie": "test"})
        eis(s == 200 and rij("relations", optreden)["namens_id"] == ander, "PATCH zet een andere pet")
        s, j = api("patch", f"/api/relations/{optreden}", "t-admin", {"omdraaien": True, "motivatie": "test"})
        eis(s == 400 and "namens_id" in j.get("error", ""), "omdraaien met een pet die niet meer past: 400")
        s, j = api("patch", f"/api/relations/{optreden}", "t-admin", {"namens_id": None, "motivatie": "test"})
        eis(s == 200 and rij("relations", optreden)["namens_id"] is None, "PATCH null wist de pet")
        api("patch", f"/api/relations/{optreden}", "t-admin", {"namens_id": inst, "motivatie": "test"})

        print("3. Richtingtoets: een verband met een hoedanigheid niet automatisch omdraaien")
        s, j = relatie(jan, krant, "beinvloeding", wie="assistent", namens_id=inst)
        eis(s == 201 and j["status"] == "voorgesteld", "agent dient persoon → medium namens in (voorgesteld)")
        c = lees()
        r = c.execute("SELECT * FROM relations WHERE id = ?", (j["id"],)).fetchone()
        c.execute("INSERT INTO richting_toetsen (relation_id, relatie_hash, verdict, reden, model, door) "
                  "VALUES (?, ?, 'omgekeerd', 'test', 'haiku+sonnet', 'richtingtoets')",
                  (r["id"], server.richting_hash(r)))
        c.commit()
        actie, redenen, _ = server.richting_besluit(c, r["id"])
        c.close()
        eis(actie is None and any("hoedanigheid" in x for x in redenen), "omgekeerd-oordeel → niet omgedraaid")

        print("4. Ontdubbelen: een andere pet is een ander feit")
        s, j = relatie(piet, krant, "beinvloeding", namens_id=ander, active_from="2018")
        andere_pet = j["id"]
        c = lees()
        _, kand = opschonen.dubbel_kandidaten(c, andere_pet)
        eis(not kand, "zelfde paar, type en mechanisme, andere namens: geen dubbel")
        c.execute("UPDATE relations SET namens_id = ? WHERE id = ?", (inst, andere_pet))
        c.commit()
        _, kand = opschonen.dubbel_kandidaten(c, andere_pet)
        eis(any(k["id"] == optreden for k, _ in kand), "dezelfde pet: wél dubbel")
        c.execute("UPDATE relations SET namens_id = ?, status = 'afgewezen' WHERE id = ?", (ander, andere_pet))
        c.commit()
        c.close()

        print("5. via_medewerkers.py: de route via de medewerker")
        c = lees()
        eis(not via_medewerkers.routes(c, inst), "zonder band geen route")
        eis(any(f"#{optreden}" in x for x in via_medewerkers.zonder_band(c)), "NAMENS-ZONDER-BAND meldt het")
        c.close()
        s, j = relatie(piet, inst, "personeel", mechanism_id=band_mech, active_from="2015", active_until="2020",
                       functie="onderzoeker")
        band = j["id"]
        eis(s == 201, "band persoon — instituut (2015–2020)")
        c = lees()
        rs = via_medewerkers.routes(c, inst)
        eis(len(rs) == 1 and rs[0]["relation_id"] == optreden and rs[0]["band_id"] == band
            and rs[0]["band_functie"] == "onderzoeker", "met de band: één route, met functie")
        eis(not via_medewerkers.zonder_band(c), "NAMENS-ZONDER-BAND is leeg")
        c.close()
        s, j = relatie(piet, krant, "beinvloeding", namens_id=inst, active_from="2023",
                       mechanism_id=band_mech)
        laat = j["id"]
        c = lees()
        eis(all(x["relation_id"] != laat for x in via_medewerkers.routes(c, inst)),
            "een optreden na het einde van de band telt niet als route (oud-medewerker)")
        eis(any(f"#{laat}" in x and "buiten de band" in x for x in via_medewerkers.zonder_band(c)),
            "NAMENS-ZONDER-BAND meldt de pet die niet meer klopt")
        c.close()
        api("patch", f"/api/relations/{laat}", "t-admin", {"namens_id": None, "motivatie": "oud-medewerker"})
        s, j = api("get", f"/api/via_medewerkers/{inst}", "assistent")
        eis(s == 200 and j["aantal"]["als_instituut"] == 1 and j["als_instituut"][0]["id"] == krant,
            "GET /api/via_medewerkers: het instituut via zijn medewerker naar het medium")
        s, j = api("get", f"/api/via_medewerkers/{krant}", "assistent")
        eis(s == 200 and j["als_doel"] and j["als_doel"][0]["id"] == inst, "… en vanaf het medium")
        s, j = api("get", "/api/via_medewerkers/999999", "assistent")
        eis(s == 404, "onbekende entiteit: 404")
        c = sqlite3.connect(db)
        export = viz_data.export_data(c)
        c.close()
        r = next(x for x in export["relations"] if x["id"] == optreden)
        eis(r.get("namens_id") == inst, "viz_data neemt namens_id mee")
        eis(any(x["id"] == optreden and x.get("namens_id") == inst
                for x in viz_data.compact_viz(export)["relations"]), "… ook in het compacte viz-2-formaat")

        print("6. Controles")
        c = lees()
        c.execute("INSERT INTO relations (source_id, target_id, relation_type, mechanism_id, namens_id, "
                  "active_from, status) VALUES (?, ?, 'beinvloeding', ?, ?, '2020', 'goedgekeurd')",
                  (inst, krant, expert, ander))
        c.commit()
        eis(any("alleen een persoon" in x for x in via_medewerkers.ongeldig(c)),
            "NAMENS-ONGELDIG vangt wat langs de API heen binnenkwam")
        c.execute("UPDATE relations SET namens_id = NULL WHERE namens_id = ? AND source_id = ?", (ander, inst))
        c.commit()
        c.close()
        s, j = relatie(inst, krant, "beinvloeding")
        inst_rel = j["id"]
        a_persoon = argument(inst_rel, "De Testkrant voert Piet Deskundige van het Testinstituut op als duider.")
        c = lees()
        eis(any(f"#{inst_rel}" in x and "Piet Deskundige" in x for x in via_medewerkers.instituut_via_persoon(c)),
            "INSTITUUT-VIA-PERSOON: bewijs over één medewerker")
        codes = {b["code"] for b in validation.check_hoedanigheid(c)}
        eis({"NAMENS-ONGELDIG", "NAMENS-ZONDER-BAND", "INSTITUUT-VIA-PERSOON"} <= codes,
            "check_hoedanigheid levert de drie controles")
        c.close()

        print("7. Stap 10e: overgezet")
        c = lees()
        ok, redenen, _, _ = opschonen.overgezet_besluit(c, inst_rel)
        eis(not ok and "geen gemergede opvolger" in redenen[0], "zonder opvolger niets te doen")
        c.close()
        a_opv = argument(optreden, "Piet Deskundige, onderzoeker van het Testinstituut, duidde in de Testkrant.",
                         reasoning=opschonen.OVERGEZET.format(id=a_persoon) + " (test)")
        c = lees()
        eis(opschonen.overgezet_van(rij("arguments", a_opv)["reasoning"]) == [a_persoon], "de marker wordt gelezen")
        eis(opschonen.overgezet_van("Overgezet van #12, #36 en #7 (test)") == [12, 36, 7]
            and opschonen.overgezet_van("Bron voor verband #12") == [], "meer ids in één marker; andere markers niet")
        eis(inst_rel in opschonen.overgezet_kandidaten(c), "het oude verband is kandidaat")
        # Zonder goedgekeurde band telt de opvolger niet
        c.execute("UPDATE relations SET status = 'voorgesteld' WHERE id = ?", (band,))
        c.commit()
        ok, redenen, _, _ = opschonen.overgezet_besluit(c, inst_rel)
        eis(not ok, "zonder goedgekeurde band geen overzetting")
        c.execute("UPDATE relations SET status = 'goedgekeurd' WHERE id = ?", (band,))
        # A1 'klopt-niet' op de opvolger telt niet
        c.execute("INSERT INTO immuun_oordelen (argument_id, fase, verdict, door, detail) "
                  "VALUES (?, 'herverificatie', 'klopt-niet', 'bronchecker', 'test')", (a_opv,))
        c.commit()
        ok, _, _, _ = opschonen.overgezet_besluit(c, inst_rel)
        eis(not ok, "een opvolger met A1 'klopt-niet' telt niet")
        c.execute("UPDATE immuun_oordelen SET verdict = 'klopt' WHERE argument_id = ? "
                  "AND fase = 'herverificatie' AND door = 'bronchecker'", (a_opv,))
        c.commit()
        ok, _, motivatie, info = opschonen.overgezet_besluit(c, inst_rel)
        eis(ok and info["afwijzen"] and info["overgezet"][0]["opvolger_id"] == a_opv,
            "opvolger gemerged + verband en band goedgekeurd: overzetten en afwijzen")
        c.close()
        s, j = api("get", f"/api/beoordeling/overgezet/{inst_rel}", "merge-service")
        eis(s == 200 and j["toegestaan"] and rij("relations", inst_rel)["status"] == "goedgekeurd",
            "GET is een droogloop")
        tel = ab.stap_overgezet(tokens["merge-service"], argparse.Namespace(droog=False, max_overgezet=50), print)
        eis(tel["overgezet"] == 1 and tel["afgewezen"] == 1, "de ronde-stap zet over en wijst af")
        oud = rij("arguments", a_persoon)
        eis(oud["status"] == "verouderd" and oud["vervangen"], "het oude argument: verouderd + vervangen")
        eis(rij("relations", inst_rel)["status"] == "afgewezen", "het oude verband: afgewezen")
        eis(rij("arguments", a_opv)["status"] in ("ongecontroleerd", "geverifieerd") and not rij("arguments", a_opv)["vervangen"],
            "de opvolger leeft")
        # Een verband met eigen, institutioneel bewijs blijft staan
        s, j = relatie(ander, krant, "beinvloeding")
        gemengd = j["id"]
        a_jan = argument(gemengd, "De Testkrant voert Jan Collega van Andere Denktank op als duider.")
        argument(gemengd, "De Testkrant publiceerde het rapport van Andere Denktank over defensie.")
        relatie(jan, ander, "personeel", mechanism_id=band_mech, active_from="2019")
        s, j = relatie(jan, krant, "beinvloeding", namens_id=ander, active_from="2021")
        argument(j["id"], "Jan Collega van Andere Denktank duidde in de Testkrant.",
                 reasoning=opschonen.OVERGEZET.format(id=a_jan))
        s, j = api("post", f"/api/beoordeling/overgezet/{gemengd}", "merge-service")
        eis(s == 200 and j["overgezet"] and not j["afgewezen"], "institutioneel bewijs blijft: niet afgewezen")
        eis(rij("relations", gemengd)["status"] == "goedgekeurd" and rij("arguments", a_jan)["vervangen"],
            "… alleen het overgezette argument gaat op vervangen")
        s, j = api("post", f"/api/beoordeling/overgezet/{gemengd}", "merge-service")
        eis(s == 409, "een tweede keer: niets meer te doen (409)")
        os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "0"
        s, j = api("post", f"/api/beoordeling/overgezet/{inst_rel}", "merge-service")
        eis(s == 503, "kill-switch: 503")
        os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
        s, j = api("post", f"/api/beoordeling/overgezet/{inst_rel}", "assistent")
        eis(s == 403, "alleen reviewer+ (merge-service)")

    print("\nAlles groen.")


if __name__ == "__main__":
    main()
