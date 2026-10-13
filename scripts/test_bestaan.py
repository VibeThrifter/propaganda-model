#!/usr/bin/env python3
"""
End-to-end-test van de bestaansregel en fusies (eigenaarsbesluit 2026-10-13: "PvdA en GroenLinks
samenvoegen met PRO en goed op tijdlijn zetten en kijken of en hoe je bepaalde banden van het
verleden samenvoegt met fusies … zorg goed dat alle tijdsintervallen worden gehandhaafd"):

  * looptijd.py: vergelijken op de gemeenschappelijke precisie, effectieve looptijd (een open
    band eindigt met zijn partij), conflicten, stamboom zonder kring;
  * de vorm van een looptijd bij aanmaken (JJJJ[-MM[-DD]], geen begin na het einde);
  * de aspect-property 'opgegaan_in': bron verplicht, een bestaande organisatie, niet zichzelf,
    geen persoon;
  * stap 10c (/api/beoordeling/looptijd): de einddatum van een organisatie en een fusie, pas na
    A1 'klopt' en de stemtoets; nooit overschrijven; een persoon draagt geen looptijd;
  * de goedkeurpoort (bestaan_reden): een verband dat begint nadat de partij ophield, wacht, met
    de opvolger in de reden; kill-switch PROPAGANDA_LOOPTIJD_POORT=0;
  * de controles LOOPTIJD-BUITEN-BESTAAN, OPVOLGING-ZONDER-EINDE en PERSOON-LOOPTIJD;
  * viz_data (active_until_eff, opgegaan_in/voortgekomen_uit) en partijen.py (de stamboom).

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt. Geen
modelaanroepen.

Gebruik: python3 scripts/test_bestaan.py
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


def test_looptijd_module():
    import looptijd as lt
    print("1. looptijd.py")
    eis(lt.voor("1945", "1946-02-09") and not lt.voor("1946", "1946-02-09")
        and not lt.voor(None, "2000"), "vergelijken op de gemeenschappelijke precisie")
    pvda = {"id": 1, "name": "PvdA", "type": "partij", "active_from": "1946", "active_until": "2026-07-01"}
    piet = {"id": 2, "name": "Piet", "type": "persoon", "active_from": "2020", "active_until": None}
    band = {"active_from": "1990", "active_until": None}
    eis(lt.effectief(band, piet, pvda) == ("1990", "2026-07-01", 1),
        "een open band eindigt met zijn partij (persoon begrenst niet)")
    eis(lt.afgelopen(band, piet, pvda, peil="2026-10-13") and not lt.afgelopen(band, piet, pvda, peil="2026"),
        "afgelopen op de dag; op jaarbasis loopt hij in 2026 nog")
    c = lt.conflicten({"active_from": "2027"}, piet, pvda, {1: [3]}, {3: "PRO"})
    eis(len(c) == 1 and "ging op in PRO" in c[0], "een band na de opheffing wijst naar de opvolger")
    eis(lt.conflicten({"active_from": "1940"}, piet, pvda) and not lt.conflicten({"active_from": "1946-05"}, piet, pvda),
        "vóór de oprichting is een conflict, in het oprichtingsjaar niet")
    eis(lt.conflicten({"active_from": "2010", "active_until": "2005"}, piet, None), "begin na einde")
    opv = {10: [{"opvolger": 20, "argument_id": 1}], 20: [{"opvolger": 30, "argument_id": 2}],
           11: [{"opvolger": 20, "argument_id": 3}]}
    hoofd, vg = lt.stamboom(opv)
    eis(hoofd == {10: 30, 20: 30, 11: 30} and vg[30] == {10, 20, 11} and vg[20] == {10, 11},
        "stamboom: transitieve voorgangers en het hoofd van de keten")
    eis(lt.kring(opv, 30, 10) and not lt.kring(opv, 40, 10), "kringdetectie")
    hoofd, _ = lt.stamboom({1: [{"opvolger": 2, "argument_id": 1}], 2: [{"opvolger": 1, "argument_id": 2}]})
    eis(hoofd == {}, "een kring levert geen stamboom")


def main():
    test_looptijd_module()
    os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
    os.environ["PROPAGANDA_STEMTOETS"] = "1"
    os.environ["PROPAGANDA_LOOPTIJD_POORT"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "vers.db"
        print("2. Verse build (schema → theorie → instanties)")
        for naam, functie in (("init_db", "init_db"), ("seed_theoretical_model", "seed"),
                              ("seed_from_ai_source", "seed")):
            module = laad_script(naam)
            module.DB_PATH = db
            getattr(module, functie)()

        import auth
        import server
        import validation
        import viz_data
        import partijen
        import looptijd
        import automatische_beoordeling as ab
        import stemtoets as st
        server.DB_PATH = db
        server._rate_emmers.clear()
        ab.DB_PATH = db
        st.DB_PATH = db

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        eis("'opgegaan_in'" in conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'arguments'").fetchone()[0],
            "schema.sql kent de property 'opgegaan_in'")
        tokens = {}
        for naam, rol, kind in (("assistent", "bijdrager", "agent"),
                                ("bronchecker", "bijdrager", "agent"),
                                ("merge-service", "reviewer", "agent"),
                                ("stemtoets", "bijdrager", "agent"),
                                ("t-admin", "maintainer", "mens")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT OR IGNORE INTO users (username, kind, role, provenance, "
                         "token_hash) VALUES (?, ?, ?, 'test', ?)",
                         (naam, kind, rol, auth.hash_token(tokens[naam])))
            conn.execute("UPDATE users SET role = ?, kind = ?, token_hash = ? WHERE username = ?",
                         (rol, kind, auth.hash_token(tokens[naam]), naam))
        conn.commit()
        mech = conn.execute("SELECT id FROM mechanisms WHERE NOT vervangen ORDER BY id LIMIT 1").fetchone()[0]
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

        def entiteit(naam_ent, typ="partij", **extra):
            s, j = api("post", "/api/entities", "assistent", {"name": naam_ent, "type": typ, **extra})
            assert s == 201, (s, j)
            api("patch", f"/api/entities/{j['id']}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
            return j["id"]

        def relatie(src, tgt, rtype="lidmaatschap", **extra):
            s, j = api("post", "/api/relations", "assistent",
                       {"source_id": src, "target_id": tgt, "relation_type": rtype, "mechanism_id": mech, **extra})
            assert s == 201, (s, j)
            return j["id"]

        def bewijs(rid):
            s, j = api("post", "/api/arguments", "assistent",
                       {"relation_id": rid, "stance": "supporting", "negeer_duplicaten": True,
                        "claim": f"Proef-verband {rid} bestaat.",
                        "citations": [{"source_id": bron(), "quote": f"Verband {rid} staat hier."}]})
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

        def aspect(eid, prop, waarde, claim, quote, bronnen=True):
            body = {"entity_id": eid, "property": prop, "property_value": waarde, "stance": "supporting",
                    "claim": claim, "negeer_duplicaten": True}
            if bronnen:
                body["citations"] = [{"source_id": bron(), "quote": quote}]
            return api("post", "/api/arguments", "assistent", body)

        print("3. De vorm van een looptijd bij aanmaken")
        pvda = entiteit("Proefpartij Rood", active_from="1946")
        gl = entiteit("Proefpartij Groen", active_from="1990-11-24")
        pro = entiteit("Proefpartij Samen (PS)", active_from="2023")
        piet = entiteit("Piet Proef", "persoon")
        kees = entiteit("Kees Proef", "persoon", active_from="2020-03-01")   # functieperiode als looptijd
        krant = entiteit("Proefkrant", "mediaorganisatie", active_from="1950")
        s, j = api("post", "/api/relations", "assistent", {"source_id": piet, "target_id": pvda,
                   "relation_type": "lidmaatschap", "mechanism_id": mech, "active_from": "ca. 1990"})
        eis(s == 400 and "JJJJ" in j["error"], "een verband met 'ca. 1990' als begin wordt geweigerd")
        s, j = api("post", "/api/relations", "assistent", {"source_id": piet, "target_id": pvda,
                   "relation_type": "lidmaatschap", "mechanism_id": mech, "active_from": "2010", "active_until": "2005"})
        eis(s == 400 and "na het einde" in j["error"], "een begin na het einde wordt geweigerd")
        s, j = api("post", "/api/entities", "assistent", {"name": "Proef X", "type": "partij", "active_from": "1990/91"})
        eis(s == 400, "ook bij een entiteit")

        print("4. 'opgegaan_in': de fusie als aspect-argument")
        s, j = aspect(pvda, "opgegaan_in", str(pro), "Proefpartij Rood ging in 2026 op in Proefpartij Samen.", "", bronnen=False)
        eis(s == 400 and "bron" in j["error"].lower(), "bron verplicht")
        s, j = aspect(pvda, "opgegaan_in", str(pvda), "Rood ging in Rood op.", "Rood ging in Rood op.")
        eis(s == 400, "niet in zichzelf")
        s, j = aspect(pvda, "opgegaan_in", str(piet), "Rood ging op in Piet Proef.", "Rood ging op in Piet.")
        eis(s == 400 and "persoon" in j["error"], "niet in een persoon")
        s, j = aspect(pvda, "opgegaan_in", "Proefpartij Samen", "Rood ging op in Samen.", "Rood ging op in Samen.")
        eis(s == 400 and "id" in j["error"], "de opvolger als id (rename-vast)")

        print("5. Stap 10c: einddatum en fusie toepassen")
        band = relatie(piet, pvda, active_from="1990")          # open band
        bewijs(band)
        api("patch", f"/api/relations/{band}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
        s, j = aspect(pvda, "active_until", "2026-07-01",
                      "Proefpartij Rood hield op 1 juli 2026 op te bestaan; zij ging op in Proefpartij Samen.",
                      "Per 1 juli 2026 zijn Rood en Groen opgegaan in Samen.")
        assert s == 201, (s, j)
        einde = j["id"]
        s, j = aspect(pvda, "opgegaan_in", str(pro),
                      "Proefpartij Rood ging per 1 juli 2026 op in Proefpartij Samen (PS).",
                      "Per 1 juli 2026 zijn Rood en Groen opgegaan in Samen.")
        assert s == 201, (s, j)
        fusie = j["id"]
        s, j = aspect(gl, "opgegaan_in", str(pro), "Proefpartij Groen ging per 1 juli 2026 op in een nieuwe partij.",
                      "Per 1 juli 2026 zijn Rood en Groen opgegaan in Samen.")
        assert s == 201, (s, j)
        zonder_naam = j["id"]
        s, j = aspect(kees, "active_from", "1962", "Kees Proef werd geboren in 1962.", "Kees Proef (1962) …")
        assert s == 201, (s, j)
        persoon_arg = j["id"]
        for a in (einde, fusie, zonder_naam, persoon_arg):
            s, j = api("get", f"/api/beoordeling/looptijd/{a}", "merge-service")
            assert any("A1" in x for x in j["redenen"]), j
        for a in (einde, fusie, zonder_naam, persoon_arg):
            a1(a)
            neutraal(a)
        c = lees()
        wacht = {a["id"] for a in ab.a2_wachtrij(c)}
        c.close()
        eis(einde not in wacht and fusie not in wacht, "einddatum en fusie wachten niet op de aanklager")
        s, j = api("get", f"/api/beoordeling/looptijd/{zonder_naam}", "merge-service")
        eis(not j["toegestaan"] and any("noemt de opvolger" in x for x in j["redenen"]),
            "de bewering moet de opvolger noemen")
        s, j = api("get", f"/api/beoordeling/looptijd/{persoon_arg}", "merge-service")
        eis(not j["toegestaan"] and any("persoon" in x for x in j["redenen"]), "een persoon draagt geen looptijd")
        tel = ab.stap_looptijd(tokens["merge-service"], argparse.Namespace(droog=False), print)
        eis(tel["gezet"] == 2, "stap 10c past de einddatum en de fusie toe")
        eis(rij("entities", pvda)["active_until"] == "2026-07-01", "de partij heeft haar einddatum")
        eis(rij("arguments", fusie)["status"] in ("ongecontroleerd", "geverifieerd"), "de fusie is gemerged")
        c = lees()
        eis(looptijd.opvolgingen(c) == {pvda: [{"opvolger": pro, "argument_id": fusie}]},
            "looptijd.opvolgingen leest de gemergede fusie")
        eis(c.execute("""SELECT COUNT(*) FROM edit_log WHERE table_name = 'entities' AND record_id = ?
                         AND reason LIKE 'automatische beoordeling: looptijd%'""", (pvda,)).fetchone()[0] == 2,
            "beide met de reden in edit_log")
        c.close()
        s, j = aspect(pvda, "active_until", "2025", "Proefpartij Rood hield in 2025 op.", "Rood stopte in 2025.")
        a1(j["id"])
        neutraal(j["id"])
        s, j = api("get", f"/api/beoordeling/looptijd/{j['id']}", "merge-service")
        eis(not j["toegestaan"] and any("nooit overschrijven" in x for x in j["redenen"]), "nooit overschrijven")

        print("6. De goedkeurpoort en de controles")
        laat = relatie(kees, pvda, "bestuurder", active_from="2026-09")   # na de opheffing
        bewijs(laat)
        c = lees()
        ok, redenen = server.bewijs_autokeur_toegestaan(c, "relations", laat)
        eis(not ok and any("buiten het bestaan" in x and "Proefpartij Samen" in x for x in redenen),
            "een band die begint na de opheffing wacht, met de opvolger in de reden")
        os.environ["PROPAGANDA_LOOPTIJD_POORT"] = "0"
        eis(not any("buiten het bestaan" in x for x in server.bewijs_autokeur_toegestaan(c, "relations", laat)[1]),
            "kill-switch PROPAGANDA_LOOPTIJD_POORT=0")
        os.environ["PROPAGANDA_LOOPTIJD_POORT"] = "1"
        basis = {b["code"]: b["aantal"] for b in validation.check_bestaan(c)}
        c.close()
        api("patch", f"/api/relations/{laat}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
        oud = relatie(kees, krant, "personeel", active_from="2001", active_until="2005")
        bewijs(oud)
        api("patch", f"/api/relations/{oud}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
        c = lees()
        nu = {b["code"]: b for b in validation.check_bestaan(c)}
        eis(nu["LOOPTIJD-BUITEN-BESTAAN"]["aantal"] == basis["LOOPTIJD-BUITEN-BESTAAN"] + 1,
            "LOOPTIJD-BUITEN-BESTAAN telt de goedgekeurde band na de opheffing")
        eis(nu["PERSOON-LOOPTIJD"]["aantal"] == basis["PERSOON-LOOPTIJD"] + 1,
            "PERSOON-LOOPTIJD wijst een functieperiode als looptijd aan")
        eis(nu["OPVOLGING-ZONDER-EINDE"]["aantal"] == 0 and nu["OPVOLGING-ONGELDIG"]["aantal"] == 0,
            "de fusie zelf is in orde")
        c.close()

        print("7. Wat de viz en het partijnetwerk ervan maken")
        c = lees()
        data = viz_data.export_data(c)
        c.close()
        r = next(x for x in data["relations"] if x["id"] == band)
        eis(r.get("active_until_eff") == "2026-07-01" and r["einde_door"] == pvda and r["active"] == 0,
            "viz_data: de open band eindigt met de partij en is afgelopen")
        e = {x["id"]: x for x in data["entities"]}
        eis(e[pvda].get("opgegaan_in") == [pro] and e[pro].get("voortgekomen_uit") == [pvda],
            "viz_data: opgegaan_in en voortgekomen_uit")
        c = lees()
        kol = {p["id"]: p for p in partijen.compute_overzicht(c)["partijen"]}
        eis(pvda not in kol and kol[pro]["voorgangers"][0]["id"] == pvda,
            "partijen: de voorganger zit in de kolom van de opvolger")
        d = partijen.compute_partij(c, pro)
        piet_rij = next(p for p in d["personen"] if p["id"] == piet)
        eis(piet_rij["band_afgelopen"] and piet_rij["band"][0]["partij"]["id"] == pvda,
            "partijen: Piet telt mee bij Samen, met zijn eigen partij en een afgelopen band")
        c.close()
    print("test_bestaan: alles groen")


if __name__ == "__main__":
    main()
