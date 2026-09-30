#!/usr/bin/env python3
"""
End-to-end-test van de nieuws-autokeur (Epic 12 "Wie is dit?", story 12.4):

  * `_modereer_kern`-refactor: de bestaande moderatie-endpoints (PATCH …/status)
    gedragen zich exact als voorheen (zelfde codes + meldingen, instantiaties, edit_log,
    afwijs-cascade, eigen-werk-poort);
  * het predikaat `nieuws_autokeur_toegestaan` — élke tak (relaties én entiteiten);
  * `POST /api/nieuws/autokeur/<tabel>/<id>`: 200 / 409 / 503 (kill-switch) / 429
    (dagplafond) / 403 / 404 / 400, volgorde entiteit-vóór-relatie, eerlijk edit_log,
    argumenten NIET gemerged;
  * `POST /api/nieuws/autokeur/intrekken` (undo) incl. cascade + nooit-opnieuw;
  * `scripts/nieuws_autokeur_service.py` tegen een tijdelijke echte HTTP-server
    (droogloop default, --once --json in contractvorm, entiteiten eerst, auditlog,
    server-onbereikbaar → nette fout).

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt.

Gebruik: python3 scripts/test_nieuws_autokeur.py
Exit-code 0 = alles groen.
"""
import contextlib
import importlib.util
import io
import json
import os
import socket
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


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
    os.environ["PROPAGANDA_NIEUWS_AUTOKEUR"] = "1"
    os.environ.pop("PROPAGANDA_NIEUWS_AUTOKEUR_PLAFOND", None)

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "vers.db"
        print("1. Verse build (schema → theorie → instanties)")
        for naam, functie in (("init_db", "init_db"),
                              ("seed_theoretical_model", "seed"),
                              ("seed_from_ai_source", "seed")):
            module = laad_script(naam)
            module.DB_PATH = db
            getattr(module, functie)()

        import auth
        import server
        server.DB_PATH = db
        server.NIEUWS_AUTOKEUR_LOG_PATH = Path(tmp) / "nieuws_autokeur_log.jsonl"
        server._rate_emmers.clear()

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        tokens = {}
        for naam, rol, kind in (("nieuws-agent", "bijdrager", "agent"),
                                ("nieuws-scout", "bijdrager", "agent"),
                                ("nieuws-autokeur", "reviewer", "agent"),
                                ("t-mens", "bijdrager", "mens"),
                                ("t-reviewer", "reviewer", "mens"),
                                ("t-admin", "maintainer", "mens")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT INTO users (username, kind, role, provenance, token_hash)"
                         " VALUES (?, ?, ?, 'test', ?)",
                         (naam, kind, rol, auth.hash_token(tokens[naam])))
        conn.commit()
        MECH = conn.execute("SELECT id FROM mechanisms WHERE NOT vervangen ORDER BY id "
                            "LIMIT 1").fetchone()[0]
        ROL = conn.execute("SELECT id FROM roles ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

        client = server.app.test_client()
        kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

        def api(methode, pad, naam, body=None):
            server._rate_emmers.clear()          # test-scaffolding: geen rate limits
            r = getattr(client, methode)(pad, json=body, headers=kop[naam])
            return r.status_code, (r.get_json() or {})

        def db_conn():
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            return c

        teller = {"n": 0}

        def bron(naam="nieuws-scout", met_url=True):
            teller["n"] += 1
            body = {"title": f"Testbron {teller['n']}", "source_type": "website"}
            if met_url:
                body["location"] = {"type": "url",
                                    "value": f"https://gemeente.test/college/{teller['n']}"}
            else:
                body["source_type"] = "boek"
            st, j = api("post", "/api/sources", naam, body)
            assert st == 201, (st, j)
            return j["id"]

        def entiteit(naam_ent, maker, typ="persoon", rol=True):
            body = {"name": naam_ent, "type": typ}
            if rol:
                body["primary_role_id"] = ROL
            st, j = api("post", "/api/entities", maker, body)
            assert st == 201, (st, j)
            return j["id"]

        def relatie(src, tgt, maker, rtype="lidmaatschap", mech=True):
            body = {"source_id": src, "target_id": tgt, "relation_type": rtype}
            if mech:
                body["mechanism_id"] = MECH
            st, j = api("post", "/api/relations", maker, body)
            assert st == 201, (st, j)
            return j["id"]

        def argument(rid, maker, sid, stance="supporting", quote="Verbatim uit de bron."):
            teller["n"] += 1
            body = {"relation_id": rid, "stance": stance, "negeer_duplicaten": True,
                    "claim": f"Structuurfeit {teller['n']}: lidmaatschap volgens de bron.",
                    "citations": [{"source_id": sid, "quote": quote}]}
            if stance == "contradicting":
                body["claim"] = f"Tegenbron {teller['n']}: dit lidmaatschap klopt niet."
            st, j = api("post", "/api/arguments", maker, body)
            assert st == 201, (st, j)
            return j["id"]

        def doel(sleutel, entity_ids=(), relation_ids=(), status="klaar"):
            st, j = api("post", "/api/nieuws/doelen", "nieuws-agent",
                        {"sleutel": sleutel, "naam": sleutel, "soort": "persoon",
                         "rol_categorie": "politicus", "prioriteit": 50})
            assert st == 201, (st, j)
            did = j["doel"]["id"]
            st, j = api("patch", f"/api/nieuws/doelen/{did}", "nieuws-scout",
                        {"status": status, "verslag": "test",
                         "resultaat": {"entity_ids": list(entity_ids),
                                       "relation_ids": list(relation_ids)}})
            assert st == 200, (st, j)
            return did

        # Een goedgekeurde organisatie (maintainer → direct goedgekeurd).
        ORG = entiteit("Testpartij Noordelijk Verbond", "t-admin", typ="partij")

        def bundel(naam_p, *, rtype="lidmaatschap", mech=True, maker="nieuws-scout",
                   persoon_maker=None, arg_maker="nieuws-scout", met_url=True,
                   status="klaar", in_resultaat=True, rol=True):
            eid = entiteit(naam_p, persoon_maker or maker, rol=rol)
            rid = relatie(ORG, eid, maker, rtype=rtype, mech=mech)
            sid = bron(arg_maker, met_url=met_url)
            aid = argument(rid, arg_maker, sid)
            did = doel(f"person:{naam_p.lower().replace(' ', '-')}",
                       [eid] if in_resultaat else [], [rid] if in_resultaat else [],
                       status=status)
            return eid, rid, aid, did

        def pred(tabel, rid):
            c = db_conn()
            try:
                return server.nieuws_autokeur_toegestaan(c, tabel, rid)
            finally:
                c.close()

        # ── 2. _modereer_kern: bestaand moderatiegedrag ongewijzigd ─────────────
        print("2. Bestaande moderatie (PATCH …/status) gedraagt zich als voorheen")
        e_m = entiteit("Moderatietest Persoon Een", "t-mens")
        r_m = relatie(ORG, e_m, "t-mens")
        st, j = api("patch", f"/api/relations/{r_m}/status", "t-reviewer", {"status": "raar"})
        eis(st == 400 and j["error"] == "status moet 'goedgekeurd' of 'afgewezen' zijn",
            "ongeldige status → 400 + zelfde melding")
        st, j = api("patch", "/api/relations/999999/status", "t-reviewer", {"status": "afgewezen"})
        eis(st == 404 and j["error"] == "Niet gevonden", "onbekend → 404")
        st, j = api("patch", f"/api/relations/{r_m}/status", "t-mens", {"status": "goedgekeurd"})
        eis(st == 403 and j["error"] == "Modereren vereist reviewer of hoger",
            "bijdrager → 403 + zelfde melding")
        st, j = api("patch", f"/api/relations/{r_m}/status", "t-reviewer",
                    {"status": "goedgekeurd"})
        eis(st == 400 and j["error"].startswith("Deze relatie heeft nog geen gesourcet argument"),
            "bronplicht: relatie zonder gesourcet argument → 400")
        r_orphan = relatie(ORG, e_m, "t-mens", rtype="personeel", mech=False)
        st, j = api("patch", f"/api/relations/{r_orphan}/status", "t-reviewer",
                    {"status": "goedgekeurd"})
        eis(st == 400 and j["error"].startswith("Dit is een kandidaat-relatie zonder mechanisme"),
            "orphan-poort: relatie zonder mechanisme → 400")
        e_eigen = entiteit("Moderatietest Eigen Werk", "t-reviewer")
        st, j = api("patch", f"/api/entities/{e_eigen}/status", "t-reviewer",
                    {"status": "goedgekeurd"})
        eis(st == 403 and j["error"].startswith("Niemand keurt eigen werk goed"),
            "eigen werk → 403 + zelfde melding")
        argument(r_m, "t-mens", bron("t-mens"))
        st, j = api("patch", f"/api/relations/{r_m}/status", "t-reviewer",
                    {"status": "goedgekeurd", "motivatie": "  klopt  "})
        eis(st == 200 and j == {"id": r_m, "status": "goedgekeurd", "argumenten_mee_afgewezen": 0},
            f"goedkeuren → 200 met exact dezelfde JSON ({j})")
        c = db_conn()
        log = c.execute("SELECT * FROM edit_log WHERE table_name = 'relations' AND record_id = ? "
                        "AND action = 'updated' ORDER BY id DESC LIMIT 1", (r_m,)).fetchone()
        inst = c.execute("SELECT 1 FROM instantiations WHERE relation_id = ? AND mechanism_id = ?",
                         (r_m, MECH)).fetchone()
        c.close()
        eis(log["changed_by"] == "t-reviewer" and log["reason"] == "klopt"
            and json.loads(log["new_value"]) == {"status": "goedgekeurd"}
            and json.loads(log["old_value"]) == {"status": "voorgesteld"} and inst,
            "edit_log (changed_by, gestripte motivatie) + instantiatie zoals voorheen")
        st, j = api("patch", f"/api/relations/{r_m}/status", "t-reviewer", {"status": "afgewezen"})
        eis(st == 400 and "huidige status: goedgekeurd" in j["error"],
            "niet-voorgesteld → 400 + zelfde melding")
        # Afwijzen met cascade over de discussieboom.
        e_af = entiteit("Moderatietest Afwijzing", "t-mens")
        r_af = relatie(ORG, e_af, "t-mens")
        argument(r_af, "t-mens", bron("t-mens"))
        argument(r_af, "t-mens", bron("t-mens"))
        st, j = api("patch", f"/api/relations/{r_af}/status", "t-reviewer",
                    {"status": "afgewezen", "motivatie": "past niet"})
        eis(st == 200 and j["argumenten_mee_afgewezen"] == 2,
            f"afwijzen cascadet over de argumenten ({j})")
        st, j = api("patch", f"/api/entities/{e_af}/status", "t-reviewer",
                    {"status": "goedgekeurd"})
        eis(st == 200 and j["status"] == "goedgekeurd", "entiteit goedkeuren werkt ongewijzigd")

        # ── 3. Predikaat: het gelukkige pad ────────────────────────────────────
        print("3. Predikaat — gelukkig pad (persoon + lidmaatschap, klaar-doel)")
        E1, R1, A1, D1 = bundel("Anouk Testbeek-Verhoeven")
        eis(pred("entities", E1) == (True, []), "entiteit: toegestaan")
        eis(pred("relations", R1) == (True, []),
            "relatie: toegestaan (eindpunt in dezelfde ronde goedkeurbaar)")

        # ── 4. Predikaat — relatie-takken ──────────────────────────────────────
        print("4. Predikaat — elke relatie-tak parkeert")

        def verwacht_park(tabel, rid, stukje, label):
            ok, redenen = pred(tabel, rid)
            eis(not ok and any(stukje in r for r in redenen), f"{label} ({redenen})")

        _, r, _, _ = bundel("Tak Relatietype", rtype="financiering")
        verwacht_park("relations", r, "valt buiten de neutrale structuurtypes", "relatietype financiering")
        _, r, _, _ = bundel("Tak Zonder Mechanisme", rtype="personeel", mech=False)
        verwacht_park("relations", r, "geen mechanisme", "geen mechanism_id")
        _, r, _, _ = bundel("Tak Andere Maker", maker="t-mens", persoon_maker="nieuws-scout")
        verwacht_park("relations", r, "niet door 'nieuws-scout'", "relatie niet door nieuws-scout")
        _, r, _, _ = bundel("Tak Argument Ander", arg_maker="t-mens")
        verwacht_park("relations", r, "geen supporting root-argument", "argument niet van nieuws-scout")
        _, r, _, _ = bundel("Tak Bron Zonder Url", met_url=False)
        verwacht_park("relations", r, "URL-vindplaats", "bron zonder URL-vindplaats")
        _, r, _, _ = bundel("Tak Doel Bezig", status="bezig")
        verwacht_park("relations", r, "status 'klaar'", "doel niet klaar")
        _, r, _, _ = bundel("Tak Niet In Resultaat", in_resultaat=False)
        verwacht_park("relations", r, "status 'klaar'", "niet in resultaat")
        _, r, a, _ = bundel("Tak Smaad")
        c = db_conn(); c.execute("UPDATE arguments SET smaad_hold = 1 WHERE id = ?", (a,)); c.commit(); c.close()
        verwacht_park("relations", r, "smaad_hold", "smaad_hold op een argument")
        _, r, _, _ = bundel("Tak Tegenargument")
        argument(r, "t-mens", bron("t-mens"), stance="contradicting")
        verwacht_park("relations", r, "tegenargument", "tegenargument op de relatie")
        e, r, _, _ = bundel("Tak Eindpunt Afgewezen")
        api("patch", f"/api/entities/{e}/status", "t-reviewer", {"status": "afgewezen"})
        verwacht_park("relations", r, "heeft status 'afgewezen'", "eindpunt afgewezen")
        _, r, _, _ = bundel("Tak Eindpunt Mens", persoon_maker="t-mens")
        verwacht_park("relations", r, "niet automatisch goedkeurbaar", "eindpunt van een mens (niet goedkeurbaar)")
        _, r, _, _ = bundel("Tak Vervangen")
        c = db_conn(); c.execute("UPDATE relations SET vervangen = 1 WHERE id = ?", (r,)); c.commit(); c.close()
        verwacht_park("relations", r, "vervangen", "vervangen relatie")

        # ── 5. Predikaat — entiteit-takken ─────────────────────────────────────
        print("5. Predikaat — elke entiteit-tak parkeert")
        e, _, _, _ = bundel("Tak Zonder Rol", rol=False)
        verwacht_park("entities", e, "rol-suggestie", "geen primary_role_id")
        e, _, _, _ = bundel("Tak Entiteit Mens", persoon_maker="t-mens")
        verwacht_park("entities", e, "niet door 'nieuws-scout'", "entiteit niet door nieuws-scout")
        e = entiteit("Tak Losse Knoop", "nieuws-scout")
        doel("person:tak-losse-knoop", [e], [])
        verwacht_park("entities", e, "niet gekoppeld aan een relatie", "zonder goedkeurbare relatie")
        e_dup = entiteit("Testpartij Noordelijk Verbonden", "nieuws-scout", typ="partij")
        rr = relatie(e_dup, E1, "nieuws-scout")
        argument(rr, "nieuws-scout", bron())
        doel("org:dup", [e_dup], [rr])
        verwacht_park("entities", e_dup, "mogelijk duplicaat", "bijna-duplicaat van een goedgekeurde naam")
        e_diak = entiteit("testpartij noordelijk verbónd", "nieuws-scout", typ="partij")
        rr = relatie(e_diak, E1, "nieuws-scout")
        argument(rr, "nieuws-scout", bron())
        doel("org:diak", [e_diak], [rr])
        verwacht_park("entities", e_diak, "gelijkenis 1.00", "hoofdletter-/diakriet-gelijk = duplicaat")

        # ── 6. Endpoint ─────────────────────────────────────────────────────────
        print("6. Endpoint POST /api/nieuws/autokeur/<tabel>/<id>")
        st, j = api("post", f"/api/nieuws/autokeur/entities/{E1}", "nieuws-scout", {})
        eis(st == 403, f"bijdrager (nieuws-scout) mag niet goedkeuren ({st})")
        st, j = api("post", f"/api/nieuws/autokeur/arguments/{A1}", "nieuws-autokeur", {})
        eis(st == 400, f"tabel 'arguments' → 400 (argumenten nooit) ({st})")
        st, j = api("post", "/api/nieuws/autokeur/entities/999999", "nieuws-autokeur", {})
        eis(st == 404, f"onbekend → 404 ({st})")
        st, j = api("get", f"/api/nieuws/autokeur/relations/{R1}", "nieuws-autokeur")
        eis(st == 200 and j["toegestaan"] is True and j["status"] == "voorgesteld",
            "GET-check (droogloop) zegt: toegestaan")
        st, j = api("post", f"/api/nieuws/autokeur/relations/{R1}", "nieuws-autokeur", {})
        eis(st == 409 and any("volgorde" in r for r in j["redenen"]),
            f"volgorde: relatie vóór haar entiteit → 409 ({j.get('redenen')})")
        os.environ["PROPAGANDA_NIEUWS_AUTOKEUR"] = "0"
        st, j = api("post", f"/api/nieuws/autokeur/entities/{E1}", "nieuws-autokeur", {})
        eis(st == 503, f"kill-switch PROPAGANDA_NIEUWS_AUTOKEUR=0 → 503 ({st})")
        os.environ["PROPAGANDA_NIEUWS_AUTOKEUR"] = "1"
        st, j = api("post", f"/api/nieuws/autokeur/entities/{E1}", "nieuws-autokeur", {})
        eis(st == 200 and j["goedgekeurd"] is True, f"entiteit eerst → 200 ({j})")
        st, j = api("post", f"/api/nieuws/autokeur/relations/{R1}", "nieuws-autokeur", {})
        eis(st == 200 and j["goedgekeurd"] is True, f"daarna de relatie → 200 ({j})")
        c = db_conn()
        for tabel, rid in (("entities", E1), ("relations", R1)):
            rij = c.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
            log = c.execute("SELECT * FROM edit_log WHERE table_name = ? AND record_id = ? "
                            "AND action = 'updated' ORDER BY id DESC LIMIT 1",
                            (tabel, rid)).fetchone()
            eis(rij["status"] == "goedgekeurd" and log["changed_by"] == "nieuws-autokeur"
                and json.loads(log["new_value"]) == {"status": "goedgekeurd"}
                and log["reason"].startswith("auto-keur nieuws-pijplijn"),
                f"{tabel} #{rid}: goedgekeurd; eerlijk edit_log (nieuws-autokeur, reden)")
        arg = c.execute("SELECT status, merged_by FROM arguments WHERE id = ?", (A1,)).fetchone()
        inst = c.execute("SELECT 1 FROM instantiations WHERE relation_id = ?", (R1,)).fetchone()
        c.close()
        eis(arg["status"] == "voorgesteld" and arg["merged_by"] is None,
            "het argument is NIET gemerged (score blijft op de vloer)")
        eis(inst is not None, "instantiatie mechanisme↔relatie aanwezig")
        st, j = api("post", f"/api/nieuws/autokeur/relations/{R1}", "nieuws-autokeur", {})
        eis(st == 409 and any("goedgekeurd" in r for r in j["redenen"]),
            "tweede keer → 409 (status al goedgekeurd)")
        # Dagplafond.
        E2, R2, _, _ = bundel("Plafond Persoon Twee")
        E3, R3, _, _ = bundel("Plafond Persoon Drie")
        os.environ["PROPAGANDA_NIEUWS_AUTOKEUR_PLAFOND"] = "3"
        st, j = api("post", f"/api/nieuws/autokeur/entities/{E2}", "nieuws-autokeur", {})
        eis(st == 200, f"derde goedkeuring vandaag (plafond 3) → 200 ({st})")
        st, j = api("post", f"/api/nieuws/autokeur/relations/{R2}", "nieuws-autokeur", {})
        eis(st == 429 and j["goedgekeurd"] is False and j["plafond"] == 3,
            f"boven het dagplafond → 429 ({st}: {j.get('error')})")
        os.environ.pop("PROPAGANDA_NIEUWS_AUTOKEUR_PLAFOND")
        st, _ = api("post", f"/api/nieuws/autokeur/relations/{R2}", "nieuws-autokeur", {})
        eis(st == 200, "met het standaardplafond (60) weer 200")

        # ── 7. Intrekken ───────────────────────────────────────────────────────
        print("7. Intrekken (undo, maintainer)")
        body = {"tabel": "relations", "id": R2, "motivatie": "steekproef: verkeerde persoon"}
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-reviewer", body)
        eis(st == 403, f"reviewer mag niet intrekken ({st})")
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-admin",
                    {"tabel": "relations", "id": R2})
        eis(st == 400, "zonder motivatie → 400")
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-admin",
                    {"tabel": "relations", "id": r_m, "motivatie": "x"})
        eis(st == 409, f"door een mens goedgekeurd → 409 ({j.get('error')})")
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-admin", body)
        eis(st == 200 and j["ingetrokken"] is True, f"relatie ingetrokken ({j})")
        c = db_conn()
        rij = c.execute("SELECT status FROM relations WHERE id = ?", (R2,)).fetchone()
        log = c.execute("SELECT * FROM edit_log WHERE table_name = 'relations' AND record_id = ? "
                        "ORDER BY id DESC LIMIT 1", (R2,)).fetchone()
        c.close()
        eis(rij["status"] == "voorgesteld" and log["changed_by"] == "t-admin"
            and log["reason"].startswith("intrekken auto-keur nieuws-pijplijn: steekproef")
            and json.loads(log["new_value"]) == {"status": "voorgesteld"},
            "terug naar voorgesteld; edit_log onder de maintainer mét motivatie")
        verwacht_park("relations", R2, "eerder door een maintainer ingetrokken",
                      "een ingetrokken element keurt de autokeur nooit opnieuw goed")
        # Entiteit met een door een MENS goedgekeurde relatie → 409.
        r_mens = relatie(ORG, E2, "t-mens", rtype="personeel")
        argument(r_mens, "t-mens", bron("t-mens"))
        api("patch", f"/api/relations/{r_mens}/status", "t-reviewer", {"status": "goedgekeurd"})
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-admin",
                    {"tabel": "entities", "id": E2, "motivatie": "x"})
        eis(st == 409 and j.get("relaties") == [r_mens],
            "entiteit met een door een mens goedgekeurde relatie → 409 + lijst")
        # Entiteit + haar autokeur-relatie → cascade.
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-admin",
                    {"tabel": "entities", "id": E1, "motivatie": "naamgenoot"})
        eis(st == 200 and j["mee_ingetrokken"]["relations"] == [R1],
            f"entiteit ingetrokken, autokeur-relatie gaat mee ({j})")
        c = db_conn()
        eis(c.execute("SELECT status FROM entities WHERE id = ?", (E1,)).fetchone()[0] == "voorgesteld"
            and c.execute("SELECT status FROM relations WHERE id = ?", (R1,)).fetchone()[0]
            == "voorgesteld", "beide weer voorgesteld")
        c.close()

        # ── 8. Service tegen een tijdelijke echte HTTP-server ──────────────────
        print("8. scripts/nieuws_autokeur_service.py (tijdelijke server)")
        from werkzeug.serving import make_server
        srv = make_server("127.0.0.1", 0, server.app, threaded=True)
        basis = f"http://127.0.0.1:{srv.server_port}"
        draad = threading.Thread(target=srv.serve_forever, daemon=True)
        draad.start()
        try:
            svc = laad_script("nieuws_autokeur_service")
            svc.LOG_PATH = Path(tmp) / "service_log.jsonl"
            tokenpad = Path(tmp) / "nieuws-autokeur.token"
            tokenpad.write_text(tokens["nieuws-autokeur"])
            E4, R4, _, D4 = bundel("Service Persoon Vier")

            def draai(*extra):
                uit = io.StringIO()
                with contextlib.redirect_stdout(uit), contextlib.redirect_stderr(io.StringIO()):
                    code = svc.main(["--json", "--base-url", basis, "--token", str(tokenpad),
                                     "--pauze", "0", *extra])
                return code, json.loads(uit.getvalue())

            code, droog = draai()
            eis(code == 0 and set(droog) == {"goedgekeurd", "geparkeerd", "doelen"}
                and set(droog["goedgekeurd"]) == {"entities", "relations"},
                "droogloop (default): contractvorm")
            eis(E4 in droog["goedgekeurd"]["entities"] and R4 in droog["goedgekeurd"]["relations"]
                and D4 in droog["doelen"], "droogloop voorspelt E4 + R4 (doel D4)")
            c = db_conn()
            eis(c.execute("SELECT status FROM entities WHERE id = ?", (E4,)).fetchone()[0]
                == "voorgesteld" and not svc.LOG_PATH.exists(),
                "droogloop keurt niets goed en schrijft geen auditlog")
            c.close()
            code, echt = draai("--once")
            eis(code == 0 and E4 in echt["goedgekeurd"]["entities"]
                and R4 in echt["goedgekeurd"]["relations"],
                f"--once --json: E4 + R4 goedgekeurd ({echt['goedgekeurd']})")
            eis(all(set(p) == {"tabel", "id", "redenen"} for p in echt["geparkeerd"])
                and any(p["id"] == R2 for p in echt["geparkeerd"]),
                f"geparkeerd in contractvorm (o.a. de ingetrokken R2; {len(echt['geparkeerd'])})")
            c = db_conn()
            volgorde = [(r["table_name"], r["record_id"]) for r in c.execute(
                "SELECT table_name, record_id FROM edit_log WHERE changed_by = 'nieuws-autokeur' "
                "AND reason LIKE 'auto-keur%' ORDER BY id")]
            c.close()
            eis(volgorde.index(("entities", E4)) < volgorde.index(("relations", R4)),
                "de service keurt de entiteit vóór de relatie goed")
            regels = [json.loads(x) for x in svc.LOG_PATH.read_text().splitlines()]
            eis(any(r["tabel"] == "relations" and r["id"] == R4 and r["uitkomst"] == "goedgekeurd"
                    and r["doelen"] == [D4] for r in regels if "tabel" in r),
                "auditregel in de jsonl (met het doel-id)")
            code, nogmaals = draai("--once")
            eis(nogmaals["goedgekeurd"] == {"entities": [], "relations": []},
                "idempotent: een tweede ronde keurt niets dubbel goed")
            st, j = api("get", "/api/nieuws/autokeur/log?limit=5", "t-reviewer")
            eis(st == 200 and "vandaag" in j and "plafond" in j, "GET /api/nieuws/autokeur/log")
        finally:
            srv.shutdown()
        # Server onbereikbaar → nette fout, exit 2, JSON in contractvorm.
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        dode_poort = s.getsockname()[1]
        s.close()
        uit, fout = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(uit), contextlib.redirect_stderr(fout):
            code = svc.main(["--once", "--json", "--base-url", f"http://127.0.0.1:{dode_poort}",
                             "--token", str(tokenpad)])
        eis(code == 2 and json.loads(uit.getvalue())["goedgekeurd"] == {"entities": [],
                                                                         "relations": []}
            and "niet bereiken" in fout.getvalue(),
            "server onbereikbaar → exit 2, lege contract-JSON, duidelijke melding")

        print("\nALLE NIEUWS-AUTOKEUR-TESTS GESLAAGD")


if __name__ == "__main__":
    main()
