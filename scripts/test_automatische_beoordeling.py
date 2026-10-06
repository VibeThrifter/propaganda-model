#!/usr/bin/env python3
"""
End-to-end-test van de automatische beoordeling (eigenaarsbesluit 2026-10-06):

  * A7 — de twee nieuwe routes: een neutraal structuurfeit merget op een onafhankelijke A1
    alleen (ook als het een persoon raakt), een ondergraving merget als een onafhankelijk
    A1-oordeel zegt dat het bezwaar standhoudt; de oude regels blijven (invloedsclaim vergt
    A1 én A2, een persoon-rakende invloedsclaim en een tegen-structuurfeit nooit
    automatisch, A1 van de auteur telt niet);
  * `bewijs_autokeur_toegestaan` + `POST /api/beoordeling/autokeur/<tabel>/<id>`:
    entiteit-vóór-relatie, bewijs moet gemerged zijn, invloed op een persoon nooit,
    kill-switch (503), eerlijk edit_log, en intrekken door een maintainer;
  * de pure helpers van scripts/bronchecker.py (normaliseren, HTML → tekst, citaat
    terugvinden) en scripts/automatische_beoordeling.py.

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt.

Gebruik: python3 scripts/test_automatische_beoordeling.py
Exit-code 0 = alles groen.
"""
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


def test_helpers():
    print("1. Bronchecker- en orkestratie-helpers")
    bc = laad_script("bronchecker")
    eis(bc.normaliseer("“Het  PBL” — zegt dit…") == '"het pbl" - zegt dit...',
        "normaliseren: typografische tekens, witruimte, kleine letters")
    html = ("<html><head><style>p{}</style><script>var x=1;</script></head><body>"
            "<h1>Kop</h1><p>Eerste alinea met &amp; teken.</p><div>Tweede</div></body></html>")
    eis(bc.html_naar_tekst(html) == "Kop\nEerste alinea met & teken.\nTweede",
        "HTML → leesbare tekst (scripts/stijlen weg, blokken als regels)")
    tekst = ("Het Planbureau voor de Leefomgeving (PBL) concludeert dat het heel erg "
             "onwaarschijnlijk is dat Nederland het klimaatdoel haalt. " * 3)
    eis(bc.zoek_citaat("heel erg onwaarschijnlijk is dat Nederland het klimaatdoel haalt",
                       tekst)[:2] == (True, True), "citaat letterlijk teruggevonden")
    eis(bc.zoek_citaat("heel erg onwaarschijnlijk is dat Nederland het klimaatdoel haalde",
                       tekst)[:2] == (True, False), "bijna letterlijk (één woord anders)")
    eis(bc.zoek_citaat("Het kabinet haalt alle doelen ruim op tijd en zonder extra beleid",
                       tekst)[0] is False, "verzonnen citaat niet gevonden")
    eis(bc.zoek_citaat("kort", tekst)[0] is False, "te kort citaat telt niet")
    eis(bc.host_van("https://www.pbl.nl/x") == "www.pbl.nl", "host van een url")
    ab = laad_script("automatische_beoordeling")
    nu = datetime.datetime(2026, 10, 20, 12, 0)
    eis(round(ab.leeftijd_dagen("2026-10-06 12:00:00", nu)) == 14
        and ab.leeftijd_dagen(None, nu) == 0.0, "leeftijd in dagen (edit_log-tijden)")
    eis(ab.parse_uren("8-22") == (8, 22), "actieve uren")


def main():
    os.environ["PROPAGANDA_AUTO_MERGE"] = "1"
    os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
    test_helpers()
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
        server.DB_PATH = db
        server._rate_emmers.clear()
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        tokens = {}
        for naam, rol, kind in (("nieuws-scout", "bijdrager", "agent"),
                                ("nieuws-bewijs", "bijdrager", "agent"),
                                ("assistent", "bijdrager", "agent"),
                                ("bronchecker", "bijdrager", "agent"),
                                ("aanklager-agent", "bijdrager", "agent"),
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

        teller = {"n": 0}

        def bron(maker="nieuws-scout"):
            teller["n"] += 1
            st, j = api("post", "/api/sources", maker,
                        {"title": f"Testbron {teller['n']}", "source_type": "website",
                         "location": {"type": "url",
                                      "value": f"https://bron.test/{teller['n']}"}})
            assert st == 201, (st, j)
            return j["id"]

        def entiteit(naam_ent, typ="persoon", maker="nieuws-scout"):
            st, j = api("post", "/api/entities", maker, {"name": naam_ent, "type": typ})
            assert st == 201, (st, j)
            return j["id"]

        def goedkeuren(tabel, rid):
            st, j = api("patch", f"/api/{tabel}/{rid}/status", "t-admin",
                        {"status": "goedgekeurd", "motivatie": "test"})
            assert st == 200, (st, j)

        def relatie(src, tgt, rtype, maker="nieuws-scout"):
            st, j = api("post", "/api/relations", maker,
                        {"source_id": src, "target_id": tgt, "relation_type": rtype,
                         "mechanism_id": MECH})
            assert st == 201, (st, j)
            return j["id"]

        def argument(rid, maker, stance="supporting", **extra):
            teller["n"] += 1
            body = {"relation_id": rid, "stance": stance, "negeer_duplicaten": True,
                    "claim": f"Bewering {teller['n']} over relatie {rid}.",
                    "citations": [{"source_id": bron(maker), "quote": f"Citaat {teller['n']}."}]}
            body.update(extra)
            st, j = api("post", "/api/arguments", maker, body)
            assert st == 201, (st, j)
            return j["id"]

        def a1(arg_id, verdict="klopt", door="bronchecker"):
            st, j = api("post", f"/api/arguments/{arg_id}/herverificatie", door,
                        {"verdict": verdict, "detail": "test"})
            assert st == 201, (st, j)

        def a2(arg_id, verdict="overleefd", door="aanklager-agent"):
            st, j = api("post", f"/api/arguments/{arg_id}/tegenspraak", door,
                        {"verdict": verdict, "detail": "test"})
            assert st == 201, (st, j)

        def merge(arg_id):
            return api("post", f"/api/arguments/{arg_id}/auto_merge", "merge-service")

        def status(tabel, rid):
            c = sqlite3.connect(db)
            try:
                return c.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()[0]
            finally:
                c.close()

        # Knopen: een persoon, een partij, een medium, een denktank (alle goedgekeurd)
        persoon = entiteit("Anouk Verbeek")
        partij = entiteit("Partij Voorbeeld", "partij")
        medium = entiteit("Omroep Voorbeeld", "mediaorganisatie")
        denktank = entiteit("Denktank Voorbeeld", "denktank")
        for e in (persoon, partij, medium, denktank):
            goedkeuren("entities", e)

        print("3. A7 — neutraal structuurfeit: A1 alleen, ook over een persoon")
        lid = relatie(partij, persoon, "lidmaatschap")
        feit = argument(lid, "nieuws-scout")
        goedkeuren("relations", lid)  # bronplicht: eerst een gesourcet argument
        st, j = merge(feit)
        eis(st == 409 and j["bucket"] == "geparkeerd-twijfel"
            and any("A1" in r for r in j["redenen"]), f"zonder A1 geparkeerd ({j})")
        a1(feit)
        st, j = merge(feit)
        eis(st == 200 and j["merged"] and status("arguments", feit) == "ongecontroleerd",
            "met onafhankelijke A1 'klopt' gemerged — geen A2 nodig, persoon geen blokkade")
        tegen = argument(lid, "assistent", stance="contradicting")
        a1(tegen)
        st, j = merge(tegen)
        eis(st == 409 and j["bucket"] == "geblokkeerd-hoog-inzet",
            "een tegen-structuurfeit over een persoon blijft geblokkeerd (smaad-firewall)")
        eigen = argument(lid, "bronchecker")
        a1(eigen, door="aanklager-agent")
        st, j = api("post", f"/api/arguments/{eigen}/herverificatie", "bronchecker",
                    {"verdict": "klopt"})
        eis(st == 403, "de bronchecker controleert nooit zijn eigen argument")

        print("3b. Een eigen A1-oordeel herzien (bronchecker v2), nooit een tweede stem")
        tweede = argument(lid, "nieuws-scout",
                          claim="Volgens het jaarverslag 2025 staat Anouk Verbeek op de ledenlijst.")
        a1(tweede, "twijfel")
        st, j = merge(tweede)
        eis(st == 409 and any("twijfel" in r for r in j["redenen"]), "twijfel blokkeert de merge")
        st, j = api("post", f"/api/arguments/{tweede}/herverificatie", "bronchecker",
                    {"verdict": "klopt"})
        eis(st == 409, "zonder 'herzien' geen tweede oordeel van hetzelfde account")
        st, j = api("post", f"/api/arguments/{tweede}/herverificatie", "bronchecker",
                    {"verdict": "klopt", "herzien": True, "detail": "v2"})
        eis(st == 200 and j.get("herzien") is True, "met 'herzien' wordt het eigen oordeel bijgewerkt")
        c = sqlite3.connect(db)
        n = c.execute("SELECT COUNT(*) FROM immuun_oordelen WHERE argument_id = ? AND door = "
                      "'bronchecker'", (tweede,)).fetchone()[0]
        c.close()
        eis(n == 1, "nog steeds één oordeel per account (geen extra stem)")
        st, j = merge(tweede)
        eis(st == 200 and j["merged"], f"het herziene oordeel telt: gemerged ({j})")

        print("4. A7 — invloedsclaim: A1 én A2, en nooit over een persoon")
        invloed = relatie(denktank, medium, "beinvloeding", maker="nieuws-bewijs")
        claim = argument(invloed, "nieuws-bewijs")
        a1(claim)
        st, j = merge(claim)
        eis(st == 409 and any("A2" in r for r in j["redenen"]),
            "A1 alleen is niet genoeg voor een invloedsclaim")
        a2(claim)
        st, j = merge(claim)
        eis(st == 200 and j["merged"], "A1 'klopt' + A2 'overleefd' (andere accounts) → gemerged")
        op_persoon = relatie(persoon, medium, "beinvloeding", maker="nieuws-bewijs")
        p_claim = argument(op_persoon, "nieuws-bewijs")
        a1(p_claim)
        a2(p_claim)
        st, j = merge(p_claim)
        eis(st == 409 and j["bucket"] == "geblokkeerd-hoog-inzet",
            "invloed van/op een persoon nooit automatisch, ook met A1 + A2")

        print("5. A7 — ondergraving: merget als een onafhankelijke A1 het bezwaar bevestigt")
        bezwaar_body = {"parent_argument_id": claim, "stance": "contradicting",
                        "claim": "De bron draagt de claim niet.",
                        "reasoning": "Het persbericht zegt wat de denktank zegt, niet wat "
                                     "de omroep ermee deed."}
        st, j = api("post", "/api/arguments", "assistent", bezwaar_body)
        assert st == 201, (st, j)
        bezwaar = j["id"]
        st, j = merge(bezwaar)
        eis(st == 409 and any("A1" in r for r in j["redenen"]), "zonder oordeel geparkeerd")
        a1(bezwaar, door="nieuws-bewijs")  # de auteur van de parent telt niet
        st, j = merge(bezwaar)
        eis(st == 409 and any("auteur" in r for r in j["redenen"]),
            "A1 door de auteur van de parent telt niet")
        a1(bezwaar, "klopt")
        st, j = merge(bezwaar)
        eis(st == 200 and j["merged"], "onafhankelijke A1 'klopt' op het bezwaar → gemerged")
        st, j = api("post", "/api/arguments", "assistent",
                    {"parent_argument_id": feit, "stance": "supporting",
                     "claim": "Klopt, zie ook het jaarverslag."})
        assert st == 201, (st, j)
        st, j2 = merge(j["id"])
        eis(st == 409 and j2["bucket"] == "mensenwerk", "een steunende reactie blijft mensenwerk")

        print("6. Relaties en entiteiten met gecontroleerd bewijs")
        nieuw_persoon = entiteit("Pieter Nieuw")
        nieuw_lid = relatie(partij, nieuw_persoon, "lidmaatschap")
        st, j = api("get", f"/api/beoordeling/autokeur/relations/{nieuw_lid}", "merge-service")
        eis(not j["toegestaan"] and any("gemerged" in r for r in j["redenen"]),
            "zonder gemerged bewijs niet goedkeurbaar")
        bewijs = argument(nieuw_lid, "nieuws-scout")
        a1(bewijs)
        merge(bewijs)
        st, j = api("post", f"/api/beoordeling/autokeur/relations/{nieuw_lid}", "merge-service")
        eis(st == 409 and any("eindpunt" in r for r in j["redenen"]),
            "strikt: de relatie wacht op haar entiteit (entiteit eerst)")
        st, j = api("post", f"/api/beoordeling/autokeur/entities/{nieuw_persoon}",
                    "merge-service")
        eis(st == 200 and status("entities", nieuw_persoon) == "goedgekeurd",
            "de entiteit gaat mee met haar goedkeurbare relatie")
        st, j = api("post", f"/api/beoordeling/autokeur/relations/{nieuw_lid}", "merge-service")
        eis(st == 200 and status("relations", nieuw_lid) == "goedgekeurd",
            "daarna de relatie: bewijs onafhankelijk gecontroleerd")
        c = sqlite3.connect(db)
        reden = c.execute("SELECT reason, changed_by FROM edit_log WHERE table_name = 'relations' "
                          "AND record_id = ? ORDER BY id DESC LIMIT 1", (nieuw_lid,)).fetchone()
        c.close()
        eis(reden[0].startswith("automatische beoordeling") and reden[1] == "merge-service",
            "eerlijk edit_log (account en reden)")
        st, j = api("post", "/api/beoordeling/autokeur/relations/" + str(op_persoon),
                    "merge-service")
        eis(st == 409 and any("persoon" in r for r in j["redenen"]),
            "een invloedsrelatie op een persoon nooit automatisch")
        st, j = api("post", f"/api/beoordeling/autokeur/relations/{nieuw_lid}", "nieuws-scout")
        eis(st == 403, "alleen reviewer-tier mag automatisch goedkeuren")
        os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "0"
        st, _ = api("post", f"/api/beoordeling/autokeur/relations/{op_persoon}", "merge-service")
        os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
        eis(st == 503, "kill-switch PROPAGANDA_AUTOMATISCHE_BEOORDELING=0 → 503")
        st, j = api("post", "/api/nieuws/autokeur/intrekken", "t-admin",
                    {"tabel": "relations", "id": nieuw_lid, "motivatie": "test terug"})
        eis(st == 200 and status("relations", nieuw_lid) == "voorgesteld",
            "een maintainer trekt een automatische goedkeuring in")
        st, j = api("get", f"/api/beoordeling/autokeur/relations/{nieuw_lid}", "merge-service")
        eis(not j["toegestaan"] and any("ingetrokken" in r for r in j["redenen"]),
            "ingetrokken = nooit opnieuw automatisch")

        print("7. Opruimen gebruikt de gewone poorten")
        weg = argument(invloed, "assistent")
        st, j = api("patch", f"/api/arguments/{weg}/status", "merge-service",
                    {"status": "verworpen", "motivatie": "automatische beoordeling: test"})
        eis(st == 200 and status("arguments", weg) == "verworpen",
            "merge-service verwerpt met motivatie (reviewer-tier)")
        st, j = api("patch", f"/api/arguments/{feit}/status", "merge-service",
                    {"status": "verworpen"})
        eis(st == 400, "zonder motivatie geen afwijzing")

        print("\nALLE TESTS VAN DE AUTOMATISCHE BEOORDELING GESLAAGD")


if __name__ == "__main__":
    main()
