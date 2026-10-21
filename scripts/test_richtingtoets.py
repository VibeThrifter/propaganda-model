#!/usr/bin/env python3
"""
End-to-end-test van de richting van verbanden (eigenaarsbesluit 2026-10-15: "alleen
directioneel als a ook echt invloed heeft op b en niet echt andersom, zoals a financiert b of a
is eigenaar van b … ga het hele propagandamodel af … en zorg ook dat de agents ze in de toekomst
niet meer maken"):

  * vocab.RICHTINGLOZE_TYPES: dezelfde lijst in Python en web/shared_vocab.js;
  * influence.py: een richtingloos type of een verband met bidirectional = 1 telt in beide
    richtingen, een gericht type in één;
  * POST /api/richtingtoets: nooit de auteur, alleen over het verband zoals het nu is
    (relatie_hash), geen oordeel over een richtingloos type;
  * POST /api/beoordeling/richting/<id>: 'omgekeerd' draait bron en doel om, 'richtingloos'
    zet bidirectional; één keer per verband, nooit werk van een mens, kill-switch, edit_log;
    terug te zetten met een maintainer-PATCH;
  * scripts/richtingtoets.py: kandidaten, een wijziging telt alleen als Sonnet haar bevestigt;
  * scripts/automatische_beoordeling.py stap 7b: toetsen en toepassen;
  * validation.check_richting (RICHTING-DEKKING).

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt. Geen
modelaanroepen: het taalmodel wordt nagebootst.

Gebruik: python3 scripts/test_richtingtoets.py
Exit-code 0 = alles groen.
"""
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


def test_woordenschat_en_invloed():
    print("1. Richtingloze typen en de invloedsgraaf")
    import influence
    import vocab
    eis(not vocab.verschillen(), "vocab.py en shared_vocab.js geven dezelfde richtingloze typen")
    eis(vocab.richtingloos("woordvoerder_van") and vocab.richtingloos("ambt")
        and vocab.richtingloos("dienstverband") and not vocab.richtingloos("financiering")
        and vocab.richtingloos("financiering", 1),
        "werken voor, een ambt, woordvoerder zijn: richtingloos; financiering alleen met de vlag")
    eis(set(vocab.RICHTING_PER_TYPE).isdisjoint(vocab.RICHTINGLOZE_TYPES),
        "elk gericht type heeft een betekenis van bron → doel, geen richtingloos type")
    adj = influence.build_adjacency([
        {"source_id": 1, "target_id": 2, "influence": 0.5, "relation_type": "woordvoerder_van"},
        {"source_id": 3, "target_id": 4, "influence": 0.5, "relation_type": "financiering"},
        {"source_id": 5, "target_id": 6, "influence": 0.5, "relation_type": "beinvloeding",
         "bidirectional": 1},
    ])
    eis(any(t == 1 for t, *_ in adj.get(2, [])) and any(t == 2 for t, *_ in adj.get(1, [])),
        "Frits Wester ↔ CDA (woordvoerder): invloed in beide richtingen")
    eis(not adj.get(4) and any(t == 4 for t, *_ in adj.get(3, [])),
        "financiering: alleen van financier naar ontvanger")
    eis(any(t == 5 for t, *_ in adj.get(6, [])), "bidirectional = 1: beide richtingen")


def main():
    os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
    os.environ["PROPAGANDA_RICHTINGTOETS"] = "1"
    test_woordenschat_en_invloed()
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "vers.db"
        print("2. Verse build (schema → theorie → instanties)")
        for naam, functie in (("init_db", "init_db"),
                              ("seed_theoretical_model", "seed"),
                              ("seed_from_ai_source", "seed")):
            module = laad_script(naam)
            module.DB_PATH = db
            getattr(module, functie)()

        import auth
        import server
        import validation
        import automatische_beoordeling as ab
        import richtingtoets as rt
        server.DB_PATH = db
        server._rate_emmers.clear()
        for module in (ab, rt):
            module.DB_PATH = db

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        eis(conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'richting_toetsen'").fetchone(),
            "schema.sql legt richting_toetsen aan")
        tokens = {}
        for naam, rol, kind in (("nieuws-scout", "bijdrager", "agent"),
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
        MECH = conn.execute("SELECT id FROM mechanisms WHERE NOT vervangen ORDER BY id "
                            "LIMIT 1").fetchone()[0]
        conn.close()

        client = server.app.test_client()
        kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

        def api(methode, pad, naam, body=None):
            server._rate_emmers.clear()
            r = getattr(client, methode)(pad, json=body, headers=kop[naam])
            return r.status_code, (r.get_json() or {})

        def via_client(method, pad, token, body=None):
            server._rate_emmers.clear()
            r = client.open(pad, method=method, json=body,
                            headers={"Authorization": f"Bearer {token}"})
            return r.status_code, (r.get_json() or {})

        ab.req = via_client
        rt.post_toets = lambda api_url, token, rel, uitkomst: via_client(
            "POST", "/api/richtingtoets", token, rt.toets_body(rel, uitkomst))
        pad = Path(tmp) / "richtingtoets.token"
        pad.write_text(tokens["richtingtoets"])
        rt.DEFAULT_TOKEN = pad
        rt.LOG_PATH = Path(tmp) / "richtingtoets_log.jsonl"

        def rij(rid):
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            try:
                return c.execute("SELECT * FROM relations WHERE id = ?", (rid,)).fetchone()
            finally:
                c.close()

        def entiteit(naam_ent, typ="bedrijf", maker="nieuws-scout"):
            s, j = api("post", "/api/entities", maker, {"name": naam_ent, "type": typ})
            assert s == 201, (s, j)
            return j["id"]

        def relatie(src, tgt, rtype, maker="nieuws-scout"):
            s, j = api("post", "/api/relations", maker,
                       {"source_id": src, "target_id": tgt, "relation_type": rtype,
                        "mechanism_id": MECH})
            assert s == 201, (s, j)
            return j["id"]

        def toets(rid, verdict, naam="richtingtoets", hash_=None):
            return api("post", "/api/richtingtoets", naam,
                       {"relation_id": rid, "relatie_hash": hash_ or server.richting_hash(rij(rid)),
                        "verdict": verdict, "reden": "test", "model": "haiku+sonnet"})

        print("3. Het oordeel vastleggen")
        ontvanger, financier = entiteit("Testkrant"), entiteit("Testfonds")
        fout = relatie(ontvanger, financier, "financiering")
        eis(toets(fout, "omgekeerd", naam="nieuws-scout")[0] == 403,
            "de auteur toetst zijn eigen verband niet (403)")
        eis(toets(fout, "omgekeerd", hash_="0" * 64)[0] == 409,
            "een oordeel over een ander verband dan het huidige: 409")
        persoon = entiteit("Test Woordvoerder", typ="persoon")
        band = relatie(persoon, ontvanger, "woordvoerder_van")
        eis(toets(band, "omgekeerd")[0] == 400, "een richtingloos type heeft geen richting (400)")
        eis(toets(fout, "omgekeerd")[0] == 201, "de richtingtoets legt 'omgekeerd' vast")
        eis(toets(fout, "omgekeerd")[0] == 200, "een tweede oordeel werkt het eigen oordeel bij")

        print("4. Toepassen (merge-service)")
        s, j = api("get", f"/api/beoordeling/richting/{fout}", "merge-service")
        eis(s == 200 and j["toegestaan"] and j["actie"] == "omdraaien", "droogloop: omdraaien")
        eis(api("post", f"/api/beoordeling/richting/{fout}", "nieuws-scout")[0] == 403,
            "een bijdrager past geen richting toe")
        os.environ["PROPAGANDA_RICHTINGTOETS"] = "0"
        eis(api("post", f"/api/beoordeling/richting/{fout}", "merge-service")[0] == 503,
            "kill-switch PROPAGANDA_RICHTINGTOETS=0 → 503")
        os.environ["PROPAGANDA_RICHTINGTOETS"] = "1"
        s, j = api("post", f"/api/beoordeling/richting/{fout}", "merge-service")
        r = rij(fout)
        eis(s == 200 and j["aangepast"] and r["source_id"] == financier
            and r["target_id"] == ontvanger, "bron en doel omgedraaid: Testfonds → Testkrant")
        c = sqlite3.connect(db)
        log = c.execute("SELECT old_value, reason FROM edit_log WHERE table_name = 'relations' "
                        "AND record_id = ? AND reason LIKE 'automatische beoordeling: richting%'",
                        (fout,)).fetchone()
        c.close()
        eis(log and f'"source_id": {ontvanger}' in log[0], "de oude richting staat in edit_log")
        s, j = api("post", f"/api/beoordeling/richting/{fout}", "merge-service")
        eis(s == 409, "het oude oordeel geldt niet meer voor het omgedraaide verband")
        toets(fout, "omgekeerd")
        s, j = api("post", f"/api/beoordeling/richting/{fout}", "merge-service")
        eis(s == 409 and any("al eens" in x for x in j["redenen"]),
            "één automatische aanpassing per verband — geen heen-en-weer")
        s, j = api("patch", f"/api/relations/{fout}", "t-admin", {"omdraaien": True})
        r = rij(fout)
        eis(s == 200 and r["source_id"] == ontvanger, "een maintainer draait het terug (PATCH)")
        api("patch", f"/api/relations/{fout}", "t-admin", {"omdraaien": True})

        wederzijds = relatie(entiteit("Testinstituut A"), entiteit("Testinstituut B"),
                             "beinvloeding")
        toets(wederzijds, "richtingloos")
        s, j = api("post", f"/api/beoordeling/richting/{wederzijds}", "merge-service")
        eis(s == 200 and rij(wederzijds)["bidirectional"] == 1 and j["actie"] == "richtingloos",
            "'richtingloos' zet bidirectional = 1")
        s, j = api("patch", f"/api/relations/{wederzijds}", "t-admin", {"bidirectional": False})
        eis(s == 200 and rij(wederzijds)["bidirectional"] == 0,
            "een maintainer zet de vlag terug (PATCH)")

        van_mens = relatie(entiteit("Testomroep"), entiteit("Testprogramma"), "beinvloeding",
                           maker="t-admin")
        toets(van_mens, "omgekeerd")
        s, j = api("post", f"/api/beoordeling/richting/{van_mens}", "merge-service")
        eis(s == 409 and any("mens" in x for x in j["redenen"]),
            "een verband van een mens past niemand automatisch aan")

        print("5. Het script en de ronde (nagebootst model)")
        zender, programma = entiteit("Testzender"), entiteit("Testshow")
        omgekeerd = relatie(programma, zender, "mediaplatform")
        juist = relatie(entiteit("Testadverteerder"), entiteit("Testblad"), "adverteerder")
        oneens = relatie(entiteit("Testdenktank"), entiteit("Testministerie"), "lobbyt")
        conn = rt.db()
        ids = {r["id"] for r in rt.kandidaten(conn, max_n=500)}
        eis(omgekeerd in ids and juist in ids and band not in ids and fout not in ids,
            "kandidaten: gerichte verbanden zonder huidig oordeel, geen richtingloos type")
        eis("Type: Mediaplatform — bron biedt het platform" in rt.context_van(conn, rij(omgekeerd)),
            "de vraag zegt wat bron → doel bij het type betekent")
        conn.close()
        gezien = []

        def nep_model(prompt, schema, systeem=None, model=None):
            gezien.append(model)
            oordelen = []
            for nr, blok in enumerate(prompt.split("\n[")[1:], 1):
                if "Testshow" in blok:
                    v = "omgekeerd"
                elif "Testdenktank" in blok:
                    v = "richtingloos" if model == "haiku" else "juist"
                else:
                    v = "juist"
                oordelen.append({"nr": nr, "oordeel": v, "reden": f"{model}: {v}"})
            return {"oordelen": oordelen}

        rt.bc.vraag_model = nep_model

        class Args:
            max_richting, droog, parallel = 50, False, 1

        uit = ab.stap_richting(tokens["merge-service"], Args, lambda *a: None)
        eis("haiku" in gezien and "sonnet" in gezien, "Haiku toetst, Sonnet bevestigt")
        r = rij(omgekeerd)
        eis(r["source_id"] == zender and uit["toegepast"]["omgedraaid"] >= 1,
            "Haiku en Sonnet eens: Testzender → Testshow omgedraaid")
        eis(rij(oneens)["bidirectional"] == 0, "oneens: niets veranderd")
        c = sqlite3.connect(db)
        v = c.execute("SELECT verdict, model FROM richting_toetsen WHERE relation_id = ?",
                      (oneens,)).fetchone()
        c.close()
        eis(v == ("twijfel", "haiku+sonnet"), "oneens wordt 'twijfel' (beide modellen vastgelegd)")
        conn = rt.db()
        eis(oneens not in {r["id"] for r in rt.kandidaten(conn, max_n=500)},
            "een getoetst verband komt niet opnieuw aan de beurt")
        conn.close()

        print("6. De meter")
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        c.execute("UPDATE relations SET status = 'goedgekeurd' WHERE id IN (?, ?)",
                  (juist, wederzijds))
        c.commit()
        meter = validation.check_richting(c)[0]
        c.close()
        eis(meter["code"] == "RICHTING-DEKKING" and not any(f"#{juist} " in x for x in
                                                             meter["voorbeelden"]),
            "RICHTING-DEKKING telt alleen gerichte verbanden zonder huidig oordeel")
    print("\nAlles groen.")


if __name__ == "__main__":
    main()
