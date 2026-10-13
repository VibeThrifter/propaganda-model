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
                                ("registercheck", "bijdrager", "agent"),
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
        eis(not j["toegestaan"] and any("blijft" in x and "gemerged argument" in x for x in j["redenen"]),
            "een datum met een gemerged argument wordt niet overschreven")

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
        test_reparaties(api, rij, lees, bron, entiteit, relatie, bewijs, a1, neutraal, aspect,
                        tokens, ab, server, validation, looptijd, db, tmp)
    print("test_bestaan: alles groen")


def test_reparaties(api, rij, lees, bron, entiteit, relatie, bewijs, a1, neutraal, aspect,
                    tokens, ab, server, validation, looptijd, db, tmp):
    """Ronde twee (2026-10-13, "controleer nog veel meer van dit soort dingen en maak ze goed"):
    datums corrigeren, het register, voorgangers goedkeuren, verhangen, de datumzoeker."""
    import datumzoeker as dz
    import bronzoeker as bz
    print("8. Een onbeschermde datum corrigeren; verkorten en mensdatums niet")
    omroep = entiteit("Proefomroep Nieuw", "omroep", active_from="2022")     # agent: geen bewijs
    s, j = aspect(omroep, "active_from", "2019", "Proefomroep Nieuw werd in 2019 opgericht.",
                  "De vereniging Proefomroep Nieuw is in 2019 opgericht.")
    ruimer = j["id"]
    s, j = aspect(omroep, "active_from", "2024", "Proefomroep Nieuw werd in 2024 opgericht.",
                  "Proefomroep Nieuw, opgericht in 2024.")
    korter = j["id"]
    for a in (ruimer, korter):
        a1(a)
        neutraal(a)
    s, j = api("get", f"/api/beoordeling/looptijd/{korter}", "merge-service")
    eis(not j["toegestaan"] and any("verkorten" in x for x in j["redenen"]), "verkorten blijft mensenwerk")
    s, j = api("post", f"/api/beoordeling/looptijd/{ruimer}", "merge-service")
    eis(s == 200 and j["gecorrigeerd"] == "2022" and rij("entities", omroep)["active_from"] == "2019",
        "een agentdatum zonder bewijs wijkt voor een eerdere datum uit een bron")
    s, j = aspect(omroep, "active_from", "2019", "Proefomroep Nieuw bestaat sinds 2019.",
                  "Proefomroep Nieuw bestaat sinds 2019.")
    a1(j["id"]); neutraal(j["id"])
    s, j2 = api("post", f"/api/beoordeling/looptijd/{j['id']}", "merge-service")
    eis(s == 200 and j2["bevestigd"], "dezelfde datum: het argument bevestigt (merge, niets gewijzigd)")
    s, j = api("post", "/api/entities", "t-admin", {"name": "Proefstichting Mens", "type": "stichting",
                                                     "active_from": "2010"})
    mens_ent = j["id"]
    c = lees()
    eis("mens" in (server._datum_beschermd(c, "entities", mens_ent, "active_from") or ""),
        "een datum die een mens zette is beschermd")
    eis(server._datum_beschermd(c, "entities", omroep, "active_from"), "en een datum met een gemerged argument ook")
    c.close()

    print("9. Het register geeft het bestaan van een overheidsorganisatie")
    reg = entiteit("Proefraad", "overheidsinstelling", active_from="1997")
    c = sqlite3.connect(db)
    c.execute("INSERT INTO externe_ids (entity_id, stelsel, waarde) VALUES (?, 'oo', '777')", (reg,))
    c.commit(); c.close()
    s, j = api("post", f"/api/entities/{reg}/looptijd", "assistent", {"active_from": "1919", "reden": "x"})
    eis(s == 403, "alleen de registercheck of een maintainer")
    s, j = api("post", f"/api/entities/{reg}/looptijd", "registercheck",
               {"active_from": "1919-02-21", "reden": "oo: record org:777 in uitgave 2026-10-08"})
    eis(s == 200 and j["gewijzigd"] == ["active_from"] and rij("entities", reg)["active_from"] == "1919-02-21",
        "een eerdere registerdatum vervangt een seed-/agentdatum")
    s, j = api("post", f"/api/entities/{reg}/looptijd", "registercheck",
               {"active_from": "1984-01-01", "reden": "oo: later record"})
    eis(s == 200 and not j["gewijzigd"] and "active_from" in j["blijft"],
        "een registerdatum die zelf door het register kwam, blijft (beschermd)")
    # Een registerdatum die een goedgekeurd verband buiten het bestaan zet, gaat niet door
    min_ = entiteit("Proefministerie", "overheidsinstelling")
    c = sqlite3.connect(db)
    c.execute("INSERT INTO externe_ids (entity_id, stelsel, waarde) VALUES (?, 'oo', '778')", (min_,))
    c.commit(); c.close()
    tak = entiteit("Proefdienst", "overheidsinstelling")
    zeg = relatie(min_, tak, "zeggenschap", active_from="1995")
    bewijs(zeg)
    api("patch", f"/api/relations/{zeg}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
    s, j = api("post", f"/api/entities/{min_}/looptijd", "registercheck",
               {"active_from": "2010-10-14", "reden": "oo: huidige vorm"})
    eis(s == 200 and not j["gewijzigd"] and "buiten het bestaan" in j["blijft"]["active_from"],
        "een registerdatum die een goedgekeurd verband buiten het bestaan zet, gaat niet door")
    s, j = api("post", f"/api/entities/{reg}/looptijd", "registercheck", {"wis": ["active_from"], "reden": "test"})
    eis(s == 200 and j["gewist"] == ["active_from"] and rij("entities", reg)["active_from"] is None,
        "de registercheck draait zijn eigen registerdatum terug")
    s, j = api("post", f"/api/entities/{omroep}/looptijd", "registercheck", {"wis": ["active_from"], "reden": "test"})
    eis(s in (200, 400) and not j.get("gewist") and rij("entities", omroep)["active_from"] == "2019",
        "maar niets wat het register niet zelf zette")
    s, j = api("post", f"/api/entities/{piet_id(rij, lees)}/looptijd", "registercheck",
               {"active_from": "1950", "reden": "x"})
    eis(s == 400, "geen persoon, alleen een organisatie met een externe id")

    print("10. Een voorganger komt binnen via haar fusie; verhangen")
    opvolger = entiteit("Proefomroep VARANIEUW", "omroep", active_from="2014")
    s, j = api("post", "/api/entities", "assistent", {"name": "Proefomroep VARA", "type": "omroep"})
    voor = j["id"]                                   # voorgesteld, zonder eigen verbanden
    # Wat ooit aan de opvolger hing, maar uit de tijd van de voorganger komt:
    persoon = entiteit("Mies Proef", "persoon")
    oud = relatie(persoon, opvolger, "bestuurder", active_from="1986", active_until="1995")
    s, j = api("post", "/api/arguments", "assistent",
               {"relation_id": oud, "stance": "supporting", "negeer_duplicaten": True,
                "claim": "Mies Proef was van 1986 tot 1995 voorzitter van de Proefomroep VARA.",
                "citations": [{"source_id": bron(), "quote": "Mies Proef, voorzitter van de Proefomroep VARA (1986-1995)."}]})
    api("post", f"/api/arguments/{j['id']}/merge", "t-admin")
    api("patch", f"/api/relations/{oud}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
    over = relatie(persoon, opvolger, "adviseur", active_from="2010", active_until="2020")   # over de fusie heen
    bewijs(over)
    api("patch", f"/api/relations/{over}/status", "t-admin", {"status": "goedgekeurd", "motivatie": "test"})
    s, j = api("get", f"/api/beoordeling/verhangen/{oud}", "merge-service")
    eis(not j["toegestaan"] and any("voorganger" in x for x in j["redenen"]), "zonder fusie geen verhangen")
    # De voorganger: voorgesteld, zonder eigen verbanden, lijkt op de opvolger
    s, j = aspect(voor, "active_until", "2014", "De Proefomroep VARA hield in 2014 op te bestaan.",
                  "In 2014 fuseerde de Proefomroep VARA.")
    eind_arg = j["id"]
    s, j = aspect(voor, "opgegaan_in", str(opvolger),
                  "De Proefomroep VARA ging in 2014 op in de Proefomroep VARANIEUW.",
                  "In 2014 fuseerde de Proefomroep VARA tot de Proefomroep VARANIEUW.")
    fusie_arg = j["id"]
    for a in (eind_arg, fusie_arg):
        a1(a); neutraal(a)
    c = lees()
    eis(not server.bewijs_autokeur_toegestaan(c, "entities", voor)[0], "vóór de fusie: geen goedkeuring")
    c.close()
    ab.stap_looptijd(tokens["merge-service"], argparse.Namespace(droog=False), print)
    c = lees()
    ok, redenen = server.bewijs_autokeur_toegestaan(c, "entities", voor)
    c.close()
    eis(ok, f"met de gemergede fusie is de voorganger goedkeurbaar (geen 'lijkt op' de opvolger) {redenen}")
    s, j = api("post", f"/api/beoordeling/autokeur/entities/{voor}", "merge-service")
    eis(rij("entities", voor)["status"] == "goedgekeurd", "de voorganger is goedgekeurd")
    c = lees()
    eis(oud in looptijd.verhangen_kandidaten(c), "verhangen_kandidaten vindt het verband")
    c.close()
    s, j = api("get", f"/api/beoordeling/verhangen/{over}", "merge-service")
    eis(not j["toegestaan"], "een verband over de fusie heen blijft staan")
    tel = ab.stap_verhangen(tokens["merge-service"], argparse.Namespace(droog=False, max_verhang=50), print)
    eis(tel["verhangen"] == 1 and rij("relations", oud)["target_id"] == voor,
        "stap 10d hangt het verband aan de voorganger die het bewijs noemt")
    c = lees()
    eis(c.execute("""SELECT COUNT(*) FROM edit_log WHERE table_name = 'relations' AND record_id = ?
                     AND reason LIKE 'automatische beoordeling: verhangen%'""", (oud,)).fetchone()[0] == 1,
        "met oud/nieuw en de reden in edit_log")
    eis(not any(f"#{oud}:" in v for v in validation.check_bestaan(c)[1]["voorbeelden"]),
        "en het conflict is weg")
    c.close()

    print("11. De datumzoeker zoekt het bestaan van organisaties")
    c = lees()
    kand = dz.organisatie_kandidaten(c)
    c.close()
    eis(any(e["id"] == opvolger for e in kand) is False and any(e["id"] == krant_zonder(lees) for e in kand),
        "kandidaten: organisaties met verbanden zonder oprichtingsdatum")
    dz.DB_PATH = db
    dz.ORG_STAND_PAD = Path(tmp) / "org.json"
    dz.LOG_PATH = Path(tmp) / "dz.jsonl"
    doel = krant_zonder(lees)
    naam = rij("entities", doel)["name"]
    dz.vraag = lambda prompt, schema, tools, regels=None: {
        "gevonden": True, "begin": "1975", "eind": "",
        "begin_bron": {"url": "https://bron.test/org", "titel": "Over ons", "uitgever": "Proef",
                       "datum": "", "soort": "website", "citaat": f"{naam} werd in 1975 opgericht."},
        "eind_bron": {"url": "", "titel": "", "uitgever": "", "datum": "", "soort": "website", "citaat": ""},
        "bewering": f"{naam} werd in 1975 opgericht.", "toelichting": ""}
    bz.natrekken = lambda b, partijen=None: (b, "")
    tokpad = Path(tmp) / "dz.token"
    tokpad.write_text(tokens["assistent"])
    dz.bz.api_post = lambda api_url, token, pad, body: _via(api, pad, body)
    dz.bz.registreer_bron = lambda api_url, token, b: bron()
    tel = dz.organisatie_ronde("http://x", tokens["assistent"], 1, 5, False, print, [doel])
    eis(tel["organisaties_ingediend"] == 1, f"een gevonden oprichting wordt een argument op de entiteit {tel}")
    c = lees()
    eis(c.execute("SELECT COUNT(*) FROM arguments WHERE entity_id = ? AND property = 'active_from' "
                  "AND property_value = '1975'", (doel,)).fetchone()[0] == 1, "met de datum als waarde")
    eis(any("ORGANISATIE-ZONDER-BESTAAN" == b["code"] for b in validation.check_bestaan(c)),
        "de meter ORGANISATIE-ZONDER-BESTAAN bestaat")
    c.close()


def _via(api, pad, body):
    return api("post", pad, "assistent", body)


def piet_id(rij, lees):
    c = lees()
    try:
        return c.execute("SELECT id FROM entities WHERE name = 'Piet Proef'").fetchone()[0]
    finally:
        c.close()


def krant_zonder(lees):
    """Een goedgekeurde organisatie met een goedgekeurd verband en zonder oprichtingsdatum."""
    c = lees()
    try:
        return c.execute("""SELECT e.id FROM entities e WHERE e.status = 'goedgekeurd'
            AND NOT e.vervangen AND e.type <> 'persoon' AND e.active_from IS NULL
            AND EXISTS (SELECT 1 FROM relations r WHERE (r.source_id = e.id OR r.target_id = e.id)
                        AND r.status = 'goedgekeurd' AND NOT r.vervangen)
            ORDER BY e.id LIMIT 1""").fetchone()[0]
    finally:
        c.close()


if __name__ == "__main__":
    main()
