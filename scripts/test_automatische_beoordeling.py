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
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def laad_script(naam):
    spec = importlib.util.spec_from_file_location(naam, ROOT / "scripts" / f"{naam}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mini_pdf(tekst):
    """Een minimale geldige pdf met één regel tekst (voor de pdf-lezer van de bronchecker)."""
    stroom = f"BT /F1 18 Tf 20 100 Td ({tekst}) Tj ET".encode()
    objecten = [b"<< /Type /Catalog /Pages 2 0 R >>",
                b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 144] /Contents 4 0 R "
                b"/Resources << /Font << /F1 5 0 R >> >> >>",
                b"<< /Length " + str(len(stroom)).encode() + b" >>\nstream\n" + stroom
                + b"\nendstream",
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    uit, posities = b"%PDF-1.4\n", []
    for nummer, obj in enumerate(objecten, 1):
        posities.append(len(uit))
        uit += f"{nummer} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(uit)
    uit += f"xref\n0 {len(objecten) + 1}\n0000000000 65535 f \n".encode()
    uit += b"".join(f"{pos:010d} 00000 n \n".encode() for pos in posities)
    uit += (f"trailer\n<< /Size {len(objecten) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n"
            "%%EOF\n").encode()
    return uit


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
    if bc.OSASCRIPT:
        eis(bc.pdf_naar_tekst(mini_pdf("Het PBL publiceert de KEV")) == "Het PBL publiceert de KEV"
            and bc.pdf_naar_tekst(b"geen pdf") is None, "pdf-tekst via macOS PDFKit")
    ab = laad_script("automatische_beoordeling")
    nu = datetime.datetime(2026, 10, 20, 12, 0)
    eis(round(ab.leeftijd_dagen("2026-10-06 12:00:00", nu)) == 14
        and ab.leeftijd_dagen(None, nu) == 0.0, "leeftijd in dagen (edit_log-tijden)")
    eis(ab.parse_uren("8-22") == (8, 22), "actieve uren")
    eis(ab.startmoment("2026-07-23 13:40:57", "2026-10-06 21:44:05") == "2026-10-06 21:44:05"
        and ab.startmoment("2026-07-23 13:40:57", None) == "2026-07-23 13:40:57"
        and ab.startmoment(None, None) is None,
        "een heropend argument krijgt een nieuwe wachttijd vanaf het heropenen")
    body = ab.feitelijke_versie(
        {"id": 3931, "stance": "supporting", "relation_id": 77, "entity_id": None,
         "parent_argument_id": None, "property": None, "property_value": None},
        [{"source_id": 5, "quote": "Citaat.", "methode": "verbatim_quote"}],
        "Van Mulligen gaf bij de NOS uitleg bij de inflatie van augustus 2026.",
        "'maandelijks' staat niet in de bron")
    eis(body["relation_id"] == 77 and body["stance"] == "supporting"
        and body["claim"].startswith("Van Mulligen gaf")
        and body["citations"] == [{"source_id": 5, "quote": "Citaat.", "methode": "verbatim_quote"}]
        and body["reasoning"].startswith("Feitelijke versie van #3931"),
        "teruggekoppeld: de feitelijke versie komt met dezelfde bronnen opnieuw binnen")


def test_storing_en_plafond():
    """Een storing van het model is geen oordeel (2026-10-09), en goedkeuren vraagt niets meer
    voor een soort waarvan het dagplafond vol is."""
    print("1b. Storing van het model en het dagplafond")
    bc = laad_script("bronchecker")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        token = tmp / "token"
        token.write_text("x")
        bc.POGINGEN_PATH, bc.LOG_PATH = tmp / "pogingen.json", tmp / "log.jsonl"

        class Leeg:
            def close(self):
                pass

        bc.db = Leeg
        uitkomsten, gevraagd, geschreven = {}, [], []

        def beoordeel(arg_id):
            gevraagd.append(arg_id)
            time.sleep(0.05)  # een modelvraag duurt even: de ronde kan de rest nog afzeggen
            return dict(uitkomsten[arg_id])

        bc._beoordeel_los = beoordeel
        bc.post_oordeel = (lambda api, tok, arg_id, uitkomst, herzien=False:
                           geschreven.append((arg_id, uitkomst["verdict"], herzien,
                                              uitkomst.get("detail"))) or (201, {}))
        storing = {"verdict": None, "detail": bc.MODEL_STORING, "storing": "model"}
        klopt = {"verdict": "klopt", "detail": "citaat letterlijk gevonden", "model": True}

        def ronde(ids, modus="nieuw"):
            rijen = [{"id": i} for i in ids]
            bc.MODI = {modus: (lambda conn, sel=None: rijen, modus == "storing")}
            return bc.draai(token_pad=token, parallel=1, modus=modus, meld=lambda *_: None)

        # Volledige uitval (sessielimiet): niets geschreven, niets geteld, vroeg gestopt
        for i in range(1, 21):
            uitkomsten[i] = storing
        tel = ronde(range(1, 21))
        eis(not geschreven and not json.loads(bc.POGINGEN_PATH.read_text())
            and len(gevraagd) <= bc.STORING_STOP + 2,
            f"uitval: geen oordeel, geen poging, stopt na {len(gevraagd)} vragen ({tel})")
        # Werkt het model voor de rest, dan telt een storing bij één argument als poging
        uitkomsten.update({30: klopt, 31: klopt, 32: storing})
        for n in (1, 2):
            gevraagd.clear(), geschreven.clear()
            ronde([30, 31, 32])
            eis([g[0] for g in geschreven] == [30, 31] or sorted(g[0] for g in geschreven) == [30, 31],
                f"ronde {n}: alleen de oordelen geschreven, #32 later opnieuw")
        geschreven.clear()
        ronde([30, 31, 32])
        eis((32, "twijfel", False, f"{bc.MAX_POGINGEN} keer {bc.MODEL_STORING}")
            in geschreven, "na 3 rondes met een werkend model: 'twijfel' (3 keer)")
        # --storing: herziet het eigen oordeel; een nieuwe storing verandert niets
        geschreven.clear()
        uitkomsten.update({40: klopt, 41: storing})
        ronde([40, 41], modus="storing")
        eis([(g[0], g[1], g[2]) for g in geschreven] == [(40, "klopt", True)],
            "--storing: herziet het oordeel bij een antwoord, laat een storing staan")
        # De selectie pakt de oude storing-twijfel, niet het "3 keer"-oordeel van nu
        like = sqlite3.connect(":memory:")
        eis(like.execute("SELECT ? LIKE ?", (f"[bronchecker v2] {bc.MODEL_STORING}",
                                             bc.STORING_DETAIL)).fetchone()[0] == 1
            and like.execute("SELECT ? LIKE ?", (f"{bc.VERSIE} 3 keer {bc.MODEL_STORING}",
                                                 bc.STORING_DETAIL)).fetchone()[0] == 0,
            "storing-selectie: alleen de oude storing-twijfel")
        like.close()

        # Goedkeuren: het registerplafond is vol → geen verzoeken meer voor registerfeiten
        ab = laad_script("automatische_beoordeling")
        pad = tmp / "mini.db"
        c = sqlite3.connect(pad)
        c.executescript("""
            CREATE TABLE entities (id INTEGER PRIMARY KEY, status TEXT, vervangen INTEGER DEFAULT 0);
            CREATE TABLE relations (id INTEGER PRIMARY KEY, status TEXT, vervangen INTEGER DEFAULT 0);
            CREATE TABLE externe_ids (entity_id INTEGER, stelsel TEXT, waarde TEXT);
            CREATE TABLE arguments (id INTEGER PRIMARY KEY, relation_id INTEGER,
                parent_argument_id INTEGER, stance TEXT, vervangen INTEGER DEFAULT 0, status TEXT);
            CREATE TABLE sources (id INTEGER PRIMARY KEY, cluster_key TEXT);
            CREATE TABLE citations (id INTEGER PRIMARY KEY, argument_id INTEGER, source_id INTEGER,
                methode TEXT, quote TEXT);
            INSERT INTO sources VALUES (1, 'register:tk'), (2, 'nos.nl');
            INSERT INTO entities (id, status) VALUES (1, 'voorgesteld'), (2, 'voorgesteld');
            INSERT INTO externe_ids VALUES (1, 'tk_persoon', 'x');
            INSERT INTO relations (id, status) VALUES (10, 'voorgesteld'), (11, 'voorgesteld'),
                (12, 'voorgesteld'), (13, 'voorgesteld');
            INSERT INTO arguments (id, relation_id, stance, status) VALUES
                (100, 10, 'supporting', 'ongecontroleerd'), (101, 11, 'supporting', 'ongecontroleerd'),
                (102, 12, 'supporting', 'ongecontroleerd'), (103, 13, 'supporting', 'ongecontroleerd');
            INSERT INTO citations (argument_id, source_id, methode, quote) VALUES
                (100, 1, 'officieel_register_scrape', 'regel'), (101, 2, 'verbatim_quote', 'c'),
                (102, 1, 'officieel_register_scrape', 'regel'), (103, 2, 'verbatim_quote', 'c');
        """)
        c.commit()
        c.close()

        def mini():
            conn = sqlite3.connect(pad)
            conn.row_factory = sqlite3.Row
            return conn

        verzoeken = []

        def req(methode, pad_, tok, body=None):
            tabel, rid = pad_.rsplit("/", 2)[-2:]
            verzoeken.append((tabel, int(rid)))
            if (tabel, int(rid)) in (("entities", 1), ("relations", 10), ("relations", 12)):
                return 429, {"soort": "register", "error": "dagplafond (register) bereikt"}
            return 200, {"goedgekeurd": True}

        ab.db, ab.req = mini, req
        tel = ab.stap_goedkeuren("t", type("A", (), {"droog": False})(), lambda *_: None)
        eis(verzoeken == [("entities", 1), ("entities", 2), ("relations", 11), ("relations", 13)]
            and tel["plafond_overgeslagen"] == 2 and tel["relations"] == 2,
            f"plafond vol: registerfeiten wachten zonder verzoek, de rest gaat door ({verzoeken})")


def main():
    os.environ["PROPAGANDA_AUTO_MERGE"] = "1"
    os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
    # Stap 3–22 toetsen de poorten van vóór de stemtoets; stap 23 zet haar aan
    os.environ["PROPAGANDA_STEMTOETS"] = "0"
    test_helpers()
    test_storing_en_plafond()
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
                                ("bronzoeker", "bijdrager", "agent"),
                                ("smaadtoets", "bijdrager", "agent"),
                                ("rfc-toetser", "bijdrager", "agent"),
                                ("rfc-criticus", "bijdrager", "agent"),
                                ("nieuws-agent", "bijdrager", "agent"),
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
        eis(st == 409 and j["bucket"] == "geparkeerd-twijfel"
            and any("smaadtoets" in r for r in j["redenen"]),
            "een tegen-structuurfeit over een persoon wacht op de smaadtoets")
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
        eis(st == 409 and j["bucket"] == "geparkeerd-twijfel"
            and any("smaadtoets" in r for r in j["redenen"]),
            "invloed op een persoon wacht op de smaadtoets, ook met A1 + A2")
        st, j = api("get", f"/api/beoordeling/autokeur/relations/{op_persoon}", "merge-service")
        eis(not j["toegestaan"] and any("smaadtoets" in r for r in j["redenen"]),
            "een persoonsrelatie wacht op bewijs dat de smaadtoets doorstond")
        st, _ = api("post", f"/api/arguments/{p_claim}/smaadtoets", "nieuws-bewijs",
                    {"verdict": "feitelijk", "reden": "eigen werk"})
        eis(st == 403, "de auteur toetst zijn eigen claim niet")
        st, _ = api("post", f"/api/arguments/{p_claim}/smaadtoets", "smaadtoets",
                    {"verdict": "misschien", "reden": "x"})
        eis(st == 400, "alleen 'feitelijk' of 'niet_feitelijk'")
        st, j = api("post", f"/api/arguments/{p_claim}/smaadtoets", "smaadtoets",
                    {"verdict": "feitelijk", "reden": "De bron toont het optreden; publieke rol."})
        eis(st == 201, f"smaadtoets vastgelegd ({j})")
        st, _ = api("post", f"/api/arguments/{p_claim}/smaadtoets", "smaadtoets",
                    {"verdict": "feitelijk", "reden": "nog eens"})
        eis(st == 409, "één smaadtoets per account (herzien kan expliciet)")
        st, j = merge(p_claim)
        eis(st == 200 and j["merged"], "feitelijk bevonden + A1 + A2 → gemerged")

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
        eis(st == 409 and j2["bucket"] == "geparkeerd-twijfel",
            "een steunende reactie vergt een bron, A1 en A2 (agents doen alles)")

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
        eis(st == 200 and status("relations", op_persoon) == "goedgekeurd",
            f"een persoonsrelatie met feitelijk bevonden bewijs gaat de graaf in ({j})")
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

        def kale_claim(rid, claim, status_oud="betwist"):
            """Een oud argument zonder bron, zoals de corpus-import ze naliet (de API eist
            sinds M0.3 een bron, dus rechtstreeks in de testdatabase)."""
            c = sqlite3.connect(db)
            try:
                cur = c.execute("INSERT INTO arguments (relation_id, stance, claim, status, "
                                "contributed_by) VALUES (?, 'supporting', ?, ?, 'assistent')",
                                (rid, claim, status_oud))
                c.commit()
                return cur.lastrowid
            finally:
                c.close()

        def revisie(arg_id, maker="bronzoeker", **extra):
            body = {"citations": [{"source_id": bron(maker), "quote": "Een letterlijk citaat.",
                                   "methode": "verbatim_quote"}]}
            body.update(extra)
            st, j = api("post", f"/api/arguments/{arg_id}/revisie", maker, body)
            assert st == 201, (st, j)
            return j["id"]

        def rij(arg_id):
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            try:
                return dict(c.execute("SELECT * FROM arguments WHERE id = ?",
                                      (arg_id,)).fetchone())
            finally:
                c.close()

        print("8. Bronrevisie: dezelfde bewering met een betere bron merget op A1 alleen")
        oud = kale_claim(invloed, "De denktank levert de omroep vaste duiding bij klimaatnieuws.")
        nieuw = revisie(oud)
        st, j = merge(nieuw)
        eis(st == 409 and any("A1" in r for r in j["redenen"])
            and not any("A6" in r for r in j["redenen"]),
            "zonder A1 geparkeerd; het origineel telt niet als duplicaat (A6)")
        a1(nieuw)
        st, j = merge(nieuw)
        eis(st == 200 and j["merged"], f"A1 'klopt' volstaat: geen aanklager nodig ({j})")
        eis(rij(oud)["vervangen"] == 1 and status("arguments", oud) == "verouderd",
            "de revisie vervangt het origineel (verouderd + vervangen)")
        ander = kale_claim(invloed, "Medewerkers van de denktank schrijven opiniestukken voor de omroep.")
        anders = revisie(ander, claim="De omroep publiceerde in 2024 drie opiniestukken van de denktank.")
        a1(anders)
        st, j = merge(anders)
        eis(st == 409 and any("A2" in r for r in j["redenen"]),
            "een nieuwe formulering is een nieuwe bewering: ook de aanklager (A2)")
        p_oud = kale_claim(op_persoon, "Anouk Verbeek schuift geregeld aan als deskundige bij de omroep.")
        p_nieuw = revisie(p_oud)
        a1(p_nieuw)
        st, j = merge(p_nieuw)
        eis(st == 409 and any("smaadtoets" in r for r in j["redenen"]),
            "ook een bronrevisie over een persoon gaat langs de smaadtoets")
        api("post", f"/api/arguments/{p_nieuw}/smaadtoets", "smaadtoets",
            {"verdict": "feitelijk", "reden": "De bron noemt haar optredens."})
        st, j = merge(p_nieuw)
        eis(st == 200 and j["merged"], "feitelijk bevonden: de bronrevisie merget op A1 alleen")
        n_oud = kale_claim(op_persoon, "Anouk Verbeek kreeg betaald voor optredens bij de omroep.")
        n_nieuw = revisie(n_oud, claim="Anouk Verbeek kreeg betaald voor optredens bij de omroep, "
                                       "een vorm van omkoping.")
        a1(n_nieuw)
        a2(n_nieuw)
        api("post", f"/api/arguments/{n_nieuw}/smaadtoets", "smaadtoets",
            {"verdict": "niet_feitelijk", "reden": "'Omkoping' is een conclusie die de bron niet trekt.",
             "herformulering": "Anouk Verbeek kreeg betaald voor optredens bij de omroep."})
        st, j = merge(n_nieuw)
        eis(st == 409 and j["bucket"] == "geblokkeerd-hoog-inzet",
            "niet feitelijk bevonden: geblokkeerd (de opruimstap koppelt het terug)")

        print("9. Verificatie: het onafhankelijke A1-oordeel zet de status van gemerged werk")
        geverifieerd = argument(invloed, "assistent")
        st, j = api("post", f"/api/arguments/{geverifieerd}/merge", "t-admin")
        assert st == 200, (st, j)
        eis(status("arguments", geverifieerd) == "ongecontroleerd", "gemerged, nooit gecontroleerd")
        st, j = api("post", f"/api/beoordeling/verificatie/{geverifieerd}", "merge-service")
        eis(st == 409 and any("A1" in r for r in j["redenen"]), "zonder A1 geen besluit")
        a1(geverifieerd)
        st, j = api("get", f"/api/beoordeling/verificatie/{geverifieerd}", "merge-service")
        eis(j["nieuwe_status"] == "geverifieerd" and status("arguments", geverifieerd)
            == "ongecontroleerd", "droogloop (GET) zegt wat er zou gebeuren en schrijft niets")
        st, j = api("post", f"/api/beoordeling/verificatie/{geverifieerd}", "merge-service")
        eis(st == 200 and status("arguments", geverifieerd) == "geverifieerd",
            "A1 'klopt' → 'geverifieerd'")
        c = sqlite3.connect(db)
        log = c.execute("SELECT action, changed_by, reason FROM edit_log WHERE table_name = "
                        "'arguments' AND record_id = ? ORDER BY id DESC LIMIT 1",
                        (geverifieerd,)).fetchone()
        c.close()
        eis(log[0] == "verified" and log[1] == "merge-service"
            and log[2].startswith("automatische beoordeling: verificatie"), "eerlijk edit_log")
        draagt_niet = argument(invloed, "assistent")
        api("post", f"/api/arguments/{draagt_niet}/merge", "t-admin")
        a1(draagt_niet, "klopt-niet")
        st, j = api("post", f"/api/beoordeling/verificatie/{draagt_niet}", "merge-service")
        eis(st == 200 and status("arguments", draagt_niet) == "bronvermelding_nodig",
            "A1 'klopt-niet' → 'bronvermelding_nodig' (de bronzoeker zoekt een betere bron)")
        eigen = argument(invloed, "bronchecker")
        api("post", f"/api/arguments/{eigen}/merge", "t-admin")
        a1(eigen, door="aanklager-agent")
        st, _ = api("post", f"/api/beoordeling/verificatie/{eigen}", "merge-service")
        eis(st == 200, "een ander account dan de auteur mag het oordeel geven")
        mens = argument(invloed, "assistent")
        api("post", f"/api/arguments/{mens}/merge", "t-admin")
        api("patch", f"/api/arguments/{mens}/status", "t-admin",
            {"status": "bronvermelding_nodig", "motivatie": "mens kijkt hiernaar"})
        a1(mens)
        st, j = api("post", f"/api/beoordeling/verificatie/{mens}", "merge-service")
        eis(st == 409 and any("mens" in r for r in j["redenen"]),
            "een statusbesluit van een mens blijft staan (zo draait een maintainer iets terug)")
        st, _ = api("post", f"/api/beoordeling/verificatie/{geverifieerd}", "assistent")
        eis(st == 403, "alleen reviewer-tier verifieert")
        os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "0"
        st, _ = api("post", f"/api/beoordeling/verificatie/{draagt_niet}", "merge-service")
        os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
        eis(st == 503, "kill-switch → 503")

        print("10. Heropenen: alleen eigen afwijzingen, en alleen na een nieuw 'klopt'")
        afgewezen = argument(invloed, "assistent")
        a1(afgewezen, "twijfel")
        api("patch", f"/api/arguments/{afgewezen}/status", "merge-service",
            {"status": "verworpen", "motivatie": "automatische beoordeling: test v1 te streng"})
        st, j = api("post", f"/api/beoordeling/heropenen/{afgewezen}", "merge-service")
        eis(st == 409 and any("A1" in r for r in j["redenen"]), "zonder bevestiging niet")
        c = sqlite3.connect(db)
        c.execute("UPDATE edit_log SET created_at = datetime('now', '-1 minute') "
                  "WHERE table_name = 'arguments' AND record_id = ?", (afgewezen,))
        c.commit()
        c.close()
        st, j = api("post", f"/api/arguments/{afgewezen}/herverificatie", "bronchecker",
                    {"verdict": "klopt", "herzien": True, "detail": "[bronchecker v2] draagt"})
        assert st == 200, (st, j)
        st, j = api("post", f"/api/beoordeling/heropenen/{afgewezen}", "merge-service")
        eis(st == 200 and status("arguments", afgewezen) == "voorgesteld",
            "eigen afwijzing + later onafhankelijk 'klopt' → terug naar 'voorgesteld'")
        door_mens = argument(invloed, "assistent")
        api("patch", f"/api/arguments/{door_mens}/status", "t-admin",
            {"status": "verworpen", "motivatie": "mens: klopt niet"})
        a1(door_mens)
        st, j = api("post", f"/api/beoordeling/heropenen/{door_mens}", "merge-service")
        eis(st == 409 and any("automatische beoordeling" in r for r in j["redenen"]),
            "een afwijzing door een mens heropent de automaat nooit")

        print("11. Voorrang uit het nieuws en de volgorde van de controle")
        st, j = api("post", "/api/nieuws/voorrang", "nieuws-agent",
                    {"relation_ids": [invloed, 999999]})
        eis(st == 200 and j["bijgewerkt"] == 1, "bestaande relaties krijgen voorrang, rest genegeerd")
        st, _ = api("post", "/api/nieuws/voorrang", "assistent", {"relation_ids": [invloed]})
        eis(st == 403, "alleen nieuws-agent (of een maintainer) meldt voorrang")
        st, _ = api("post", "/api/nieuws/voorrang", "nieuws-agent", {"relation_ids": ["x"]})
        eis(st == 400, "alleen gehele getallen")
        bc = laad_script("bronchecker")
        bc.DB_PATH = db
        ander_doel = relatie(partij, denktank, "beinvloeding")
        later = argument(ander_doel, "assistent")
        api("post", f"/api/arguments/{later}/merge", "t-admin")
        goedkeuren("relations", ander_doel)  # bronplicht: eerst een gesourcet argument
        eerder = argument(invloed, "assistent")
        api("post", f"/api/arguments/{eerder}/merge", "t-admin")
        goedkeuren("relations", invloed)
        conn = bc.db()
        try:
            volgorde = [r["id"] for r in bc.controle_kandidaten(conn)]
        finally:
            conn.close()
        eis(eerder in volgorde and later in volgorde
            and volgorde.index(eerder) < volgorde.index(later),
            "wat het nieuws toont gaat voor bij de controle (ook als het ouder is)")
        eis(geverifieerd not in volgorde, "al geverifieerd werk komt niet terug")

        print("12. Bronzoeker-helpers")
        bz = laad_script("bronzoeker")
        eis(bz.datum_van("gepubliceerd 2021-03-04") == "2021-03-04"
            and bz.datum_van("maart 2021") == "2021" and bz.datum_van("onbekend") is None,
            "publicatiedatum uit wat het model gaf")
        eis(bz.verboden("https://nl.wikipedia.org/wiki/RIVM") and bz.verboden("https://x.com/a")
            and not bz.verboden("https://linux.com/x") and not bz.verboden("https://nos.nl/a"),
            "Wikipedia en sociale media nooit als bron, gewone sites wel")
        eis(bz.probleem({"n_echt": 0, "status": "betwist", "a1": None,
                         "betwist_reden": "Onvoldoende te sourcen (workflow-onderzoek): AD.nl "
                                          "is paywalled"}) == "geen_bron"
            and bz.probleem({"n_echt": 0, "status": "betwist", "a1": None,
                             "betwist_reden": "Verifieerbaar (bron beschikbaar) maar PERIFEER "
                                              "voor nieuwsbias"}) is None
            and bz.probleem({"n_echt": 0, "status": "betwist", "a1": None,
                             "betwist_reden": "Weerlegd: RTL onthulde de affaire juist"}) is None
            and bz.probleem({"n_echt": 1, "status": "betwist", "a1": "klopt-niet",
                             "betwist_reden": None}) is None
            and bz.probleem({"n_echt": 0, "status": "ongecontroleerd", "a1": None,
                             "betwist_reden": None}) == "geen_bron"
            and bz.probleem({"n_echt": 1, "status": "ongecontroleerd", "a1": "klopt-niet",
                             "betwist_reden": None}) == "draagt_niet"
            and bz.probleem({"n_echt": 1, "status": "ongecontroleerd", "a1": "klopt",
                             "betwist_reden": None}) is None,
            "wie een (betere) bron nodig heeft; betwist om de inhoud nooit")
        nu = datetime.datetime(2026, 10, 6, 12, 0)
        eis(bz.mag_weer(None, nu) and not bz.mag_weer({"op": "2026-09-20T12:00:00",
                                                       "uitkomst": "niets"}, nu)
            and bz.mag_weer({"op": "2026-10-05T12:00:00", "uitkomst": "fout"}, nu),
            "niets gevonden: pas na 30 dagen opnieuw; een fout de volgende dag")
        pagina = ("Tijdens de coronacrisis was het RIVM de belangrijkste bron voor de "
                  "berichtgeving van de landelijke dagbladen. " * 30)
        bz.bc.haal_bron = lambda bron, citaat=None: (pagina, "ok", bron["url"])
        goed, _ = bz.natrekken({"url": "https://nos.nl/a", "citaat": "was het RIVM de "
                                "belangrijkste bron voor de berichtgeving", "datum": "2021"})
        eis(goed is not None and goed["letterlijk"], "een citaat dat in de bron staat houdt stand")
        fout, reden = bz.natrekken({"url": "https://nos.nl/a", "citaat": "het RIVM bepaalde "
                                    "zelf wat de kranten schreven over corona"})
        eis(fout is None and "niet teruggevonden" in reden, "een verzonnen citaat valt af")
        fout, reden = bz.natrekken({"url": "https://nl.wikipedia.org/wiki/RIVM",
                                    "citaat": "was het RIVM de belangrijkste bron"})
        eis(fout is None and "toegestane" in reden, "Wikipedia valt af")
        eis(bz.noemt("De Volkskrant verspreidde berichten via Facebook", "Meta (Facebook/Instagram)")
            and bz.noemt("De Volkskrant verspreidde berichten via Facebook", "de Volkskrant")
            and bz.noemt("Het AD nam RIVM-cijfers over", "AD (Algemeen Dagblad)")
            and bz.noemt("Volgens DPG zelf", "DPG Media")
            and not bz.noemt("Nederlandse nieuwssites hangen van Google af", "De Telegraaf")
            and not bz.noemt("Een adviesbureau", "AD (Algemeen Dagblad)"),
            "een herformulering moet de partijen zelf noemen (als heel woord)")
        algemeen = {"bewering": "Nederlandse nieuwssites zijn steeds afhankelijker van Google.",
                    "bronnen": [{"url": "https://nos.nl/a", "titel": "x", "uitgever": "NOS",
                                 "datum": "2025", "soort": "nieuwsartikel",
                                 "citaat": "was het RIVM de belangrijkste bron voor de berichtgeving"}],
                    "gevonden": True, "toelichting": ""}
        bz.vraag_zoeker = lambda prompt: algemeen
        uit = bz.zoek({"id": 1, "claim": "Telegraaf afhankelijk van Google", "relation_id": 9,
                       "bron_naam": "Google", "doel_naam": "De Telegraaf", "entiteit_naam": None,
                       "stance": "supporting", "mechanisme": None, "relation_type": "x",
                       "probleem": "geen_bron", "bronnen": [], "status": "betwist"})
        eis(uit["uitkomst"] == "niets" and "De Telegraaf" in uit["afgevallen"][-1]["reden"],
            "een algemene herformulering zonder de partij zelf wordt geen revisie")

        print("13. Smaadtoets: smaad_hold eraf als het feitelijk is, en eigen afwijzingen terug")
        gehouden = argument(op_persoon, "nieuws-bewijs",
                            claim="Anouk Verbeek werd veroordeeld wegens fraude met omroepgeld.")
        eis(rij(gehouden)["smaad_hold"] == 1, "negatieve persoonsclaim landt onder smaad_hold")
        st, j = api("post", f"/api/beoordeling/smaad_vrijgeven/{gehouden}", "merge-service")
        eis(st == 409 and any("smaadtoets" in r for r in j["redenen"]), "zonder smaadtoets niet vrij")
        a1(gehouden)
        api("post", f"/api/arguments/{gehouden}/smaadtoets", "smaadtoets",
            {"verdict": "feitelijk", "reden": "De uitspraak van de rechtbank staat in de bron."})
        st, _ = api("post", f"/api/beoordeling/smaad_vrijgeven/{gehouden}", "nieuws-scout")
        eis(st == 403, "alleen reviewer-tier geeft vrij")
        st, j = api("post", f"/api/beoordeling/smaad_vrijgeven/{gehouden}", "merge-service")
        eis(st == 200 and rij(gehouden)["smaad_hold"] == 0,
            "feitelijk bevonden en de bron draagt het → smaad_hold eraf")
        vast = argument(op_persoon, "nieuws-bewijs",
                        claim="Anouk Verbeek presenteerde in 2025 een omroepdebat over media.")
        a1(vast)
        api("patch", f"/api/arguments/{vast}/status", "merge-service",
            {"status": "verworpen", "motivatie": "automatische beoordeling: na 14 dagen niet te "
             "bevestigen — het komt (nog) niet door de immuunpoort; opgeschoond"})
        c = sqlite3.connect(db)
        c.execute("UPDATE edit_log SET created_at = datetime('now', '-1 minute') "
                  "WHERE table_name = 'arguments' AND record_id = ?", (vast,))
        c.execute("UPDATE immuun_oordelen SET created_at = datetime('now', '-2 minutes') "
                  "WHERE argument_id = ?", (vast,))
        c.commit()
        c.close()
        st, j = api("post", f"/api/beoordeling/heropenen/{vast}", "merge-service")
        eis(st == 409, "zonder nieuw oordeel blijft de afwijzing staan")
        api("post", f"/api/arguments/{vast}/smaadtoets", "smaadtoets",
            {"verdict": "feitelijk", "reden": "Een publiek optreden, zo in de bron."})
        st, j = api("post", f"/api/beoordeling/heropenen/{vast}", "merge-service")
        eis(st == 200 and status("arguments", vast) == "voorgesteld",
            "een persoonsclaim die op de oude firewall strandde, komt terug na 'feitelijk'")

        print("14. Mechanisme-toewijzer: kandidaat-verbanden krijgen een mechanisme")
        st, j = api("post", "/api/relations", "nieuws-scout",
                    {"source_id": partij, "target_id": denktank, "relation_type": "financiering"})
        assert st == 201, (st, j)
        kandidaat = j["id"]
        st, _ = api("post", f"/api/beoordeling/mechanisme/{kandidaat}", "nieuws-scout",
                    {"mechanism_id": MECH, "motivatie": "x"})
        eis(st == 403, "alleen reviewer-tier zet een mechanisme")
        st, _ = api("post", f"/api/beoordeling/mechanisme/{kandidaat}", "merge-service",
                    {"mechanism_id": 999999, "motivatie": "x"})
        eis(st == 400, "een onbekend mechanisme wordt geweigerd")
        st, j = api("post", f"/api/beoordeling/mechanisme/{kandidaat}", "merge-service",
                    {"mechanism_id": MECH, "motivatie": "past het best"})
        c = sqlite3.connect(db)
        gezet = c.execute("SELECT mechanism_id FROM relations WHERE id = ?", (kandidaat,)).fetchone()[0]
        reden = c.execute("SELECT reason FROM edit_log WHERE table_name = 'relations' AND "
                          "record_id = ? ORDER BY id DESC LIMIT 1", (kandidaat,)).fetchone()[0]
        c.close()
        eis(st == 200 and gezet == MECH
            and reden.startswith("automatische beoordeling: mechanisme"),
            "mechanisme gezet, met reden in edit_log (de opruimklok begint dan opnieuw)")
        st, _ = api("post", f"/api/beoordeling/mechanisme/{kandidaat}", "merge-service",
                    {"mechanism_id": MECH, "motivatie": "nog eens"})
        eis(st == 409, "een relatie met een mechanisme is geen kandidaat meer")

        print("15. RfC's door agents: twee akkoorden nemen aan, één afwijzing wijst af")
        st, j = api("post", "/api/voorstellen", "assistent",
                    {"soort": "hernoemen", "titel": "Hernoem de denktank",
                     "payload": {"element_type": "entiteit", "element_id": denktank,
                                 "nieuwe_naam": "Denktank Herdoopt", "motivatie": "nieuwe naam"}})
        assert st == 201, (st, j)
        rfc = j["id"]
        st, _ = api("post", f"/api/beoordeling/rfc/{rfc}", "merge-service")
        eis(st == 409, "zonder reviews geen besluit")
        for wie in ("rfc-toetser", "assistent"):
            api("post", f"/api/voorstellen/{rfc}/reviews", wie,
                {"oordeel": "akkoord", "motivatie": "klopt"})
        st, j = api("post", f"/api/beoordeling/rfc/{rfc}", "merge-service")
        eis(st == 409, "één agent-akkoord (plus de indiener zelf) is niet genoeg")
        api("post", f"/api/voorstellen/{rfc}/reviews", "rfc-criticus",
            {"oordeel": "akkoord", "motivatie": "geen bezwaar gevonden"})
        st, j = api("post", f"/api/beoordeling/rfc/{rfc}", "merge-service")
        c = sqlite3.connect(db)
        naam = c.execute("SELECT name FROM entities WHERE id = ?", (denktank,)).fetchone()[0]
        c.close()
        eis(st == 200 and j["besluit"] == "geaccepteerd" and naam == "Denktank Herdoopt",
            "twee onafhankelijke agent-akkoorden → aangenomen en uitgevoerd")
        st, j = api("post", "/api/voorstellen", "assistent",
                    {"soort": "hernoemen", "titel": "Hernoem de omroep",
                     "payload": {"element_type": "entiteit", "element_id": medium,
                                 "nieuwe_naam": "Omroep Herdoopt", "motivatie": "nieuwe naam"}})
        rfc2 = j["id"]
        api("post", f"/api/voorstellen/{rfc2}/reviews", "rfc-toetser",
            {"oordeel": "akkoord", "motivatie": "klopt"})
        api("post", f"/api/voorstellen/{rfc2}/reviews", "rfc-criticus",
            {"oordeel": "afwijzen", "motivatie": "Geen bron voor de naamswijziging gevonden."})
        st, j = api("post", f"/api/beoordeling/rfc/{rfc2}", "merge-service")
        c = sqlite3.connect(db)
        stand = c.execute("SELECT status FROM voorstellen WHERE id = ?", (rfc2,)).fetchone()[0]
        c.close()
        eis(st == 200 and j["besluit"] == "afgewezen" and stand == "afgewezen",
            "één agent-afwijzing met reden → afgewezen (de indiener kan herzien)")

        print("16. Wachtrijen: aanklager en smaadtoets")
        ab = laad_script("automatische_beoordeling")
        sm = laad_script("smaadtoets")
        aspect = argument(invloed, "nieuws-bewijs", property="active_from",
                          property_value="2020")
        a1(aspect)
        p_wacht = argument(op_persoon, "nieuws-bewijs",
                           claim="Anouk Verbeek gaf in 2024 een lezing op het omroepcongres.")
        a1(p_wacht)
        structuurfeit = argument(lid, "nieuws-scout",
                                 claim="Anouk Verbeek staat sinds 2019 op de ledenlijst.")
        a1(structuurfeit)
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        wachtrij = {r["id"] for r in ab.a2_wachtrij(c)}
        toetsbaar = {r["id"] for r in sm.kandidaten(c)}
        c.close()
        eis(aspect in wachtrij, "ook een aspect (sinds wanneer) wacht op de aanklager")
        eis(p_wacht not in wachtrij and p_wacht in toetsbaar,
            "een persoonsclaim gaat eerst langs de smaadtoets, pas daarna naar de aanklager")
        eis(structuurfeit not in toetsbaar and structuurfeit not in wachtrij,
            "een neutraal structuurfeit heeft geen smaadtoets en geen aanklager nodig")
        api("post", f"/api/arguments/{p_wacht}/smaadtoets", "smaadtoets",
            {"verdict": "feitelijk", "reden": "Publiek optreden."})
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        wachtrij = {r["id"] for r in ab.a2_wachtrij(c)}
        toetsbaar = {r["id"] for r in sm.kandidaten(c)}
        c.close()
        eis(p_wacht in wachtrij and p_wacht not in toetsbaar,
            "feitelijk bevonden → naar de aanklager, en geen tweede smaadtoets")

        print("17. Verificatie voor elk soort argument (ook theorie)")
        literatuur = bron("assistent")  # eerst de bron (de API schrijft zelf)
        c = sqlite3.connect(db)
        rol_id = c.execute("SELECT MIN(id) FROM roles").fetchone()[0]
        theorie = c.execute("INSERT INTO arguments (role_id, stance, claim, status, contributed_by) "
                            "VALUES (?, 'supporting', 'Herman & Chomsky beschrijven deze rol.', "
                            "'ongecontroleerd', 'assistent')", (rol_id,)).lastrowid
        c.execute("INSERT INTO citations (argument_id, source_id, quote) VALUES (?, ?, ?)",
                  (theorie, literatuur, "Een letterlijke passage."))
        c.commit()
        c.close()
        a1(theorie)
        st, j = api("post", f"/api/beoordeling/verificatie/{theorie}", "merge-service")
        eis(st == 200 and status("arguments", theorie) == "geverifieerd",
            "een theorie-argument waarvan de bron het draagt → geverifieerd")
        eis(status("arguments", bezwaar) == "ongecontroleerd", "het bezwaar uit stap 5 is gemerged")
        st, j = api("post", f"/api/beoordeling/verificatie/{bezwaar}", "merge-service")
        eis(st == 200 and status("arguments", bezwaar) == "geverifieerd",
            "een bevestigd bezwaar leunt op de bron van het aangevochten argument → geverifieerd")

        def lees():
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            return c

        print("18. Bronzoeker: voorstellen met twijfel en verbanden zonder argument")
        twijfel = argument(invloed, "nieuws-bewijs",
                           claim="De denktank levert de omroep elke week duiding bij nieuws.")
        a1(twijfel, "twijfel")
        eigen_vervanger = argument(invloed, "bronzoeker",
                                   claim="De denktank levert de omroep duiding bij nieuws.")
        a1(eigen_vervanger, "twijfel")
        kaal_verband = relatie(medium, denktank, "bron_van")
        c = sqlite3.connect(db)
        c.execute("UPDATE relations SET status = 'goedgekeurd' WHERE id = ?", (kaal_verband,))
        c.commit()
        c.close()
        c = lees()
        try:
            alle = bz.kandidaten(c)
            voorstellen = {a["id"]: a for a in alle if a["soort"] == "voorstel"}
            verbanden = {a["relation_id"]: a for a in alle if a["soort"] == "verband"}
            wacht_leeg = bz.wacht_op_zoeker(c, {})
            wacht_na = bz.wacht_op_zoeker(c, {str(twijfel): {"uitkomst": "niets"}})
            wacht_fout = bz.wacht_op_zoeker(c, {str(twijfel): {"uitkomst": "fout"}})
        finally:
            c.close()
        eis(twijfel in voorstellen and voorstellen[twijfel]["probleem"] == "twijfel",
            "een voorstel met 'twijfel' gaat naar de bronzoeker")
        eis(eigen_vervanger not in voorstellen,
            "wat de bronzoeker zelf indiende, krijgt geen tweede reparatie")
        eis(kaal_verband in verbanden and verbanden[kaal_verband]["probleem"] == "geen_argument",
            "een goedgekeurd verband zonder enig steunend argument gaat naar de bronzoeker")
        eis(twijfel in wacht_leeg and twijfel not in wacht_na and twijfel in wacht_fout,
            "de opruimstap wacht op een poging (een technische fout telt niet als poging)")
        eis([a["soort"] for a in alle].index("voorstel") < [a["soort"] for a in alle].index(
            "gemerged") if any(a["soort"] == "gemerged" for a in alle) else True,
            "een voorstel (dat op een besluit wacht) gaat voor gemerged werk")
        citaties = [{"source_id": bron("bronzoeker"), "quote": "De denktank levert de omroep "
                     "duiding.", "methode": "verbatim_quote"}]
        pad, body = bz.indiening(voorstellen[twijfel], {"bewering": "De denktank levert de "
                                 "omroep duiding bij nieuws.", "toelichting": "NOS 2025"},
                                 citaties)
        eis(pad == "/api/arguments" and body["relation_id"] == invloed
            and body["stance"] == "supporting"
            and body["reasoning"].startswith(f"Betere bron voor #{twijfel}"),
            "een vervangend voorstel: zelfde doel en stance, merkteken in de reasoning")
        st, j = api("post", pad, "bronzoeker", body)
        eis(st == 201, f"de server neemt het vervangende voorstel aan ({st})")
        pad, body = bz.indiening(verbanden[kaal_verband], {"bewering": "Omroep Voorbeeld citeert "
                                 "Denktank Herdoopt.", "toelichting": ""}, citaties)
        eis(pad == "/api/arguments" and body["relation_id"] == kaal_verband
            and body["reasoning"].startswith(f"Bron voor verband #{kaal_verband}"),
            "een nieuw steunend argument voor het verband zonder argument")
        st, j = api("post", pad, "bronzoeker", body)
        eis(st == 201, f"de server neemt het nieuwe argument aan ({st})")
        c = lees()
        try:
            verbanden = {a["relation_id"] for a in bz.verbanden_zonder_argument(c)}
        finally:
            c.close()
        eis(kaal_verband not in verbanden, "met een (voorgesteld) argument is het verband in "
            "behandeling: geen tweede zoektocht")
        pad, _ = bz.indiening({**voorstellen[twijfel], "soort": "gemerged"},
                              {"bewering": voorstellen[twijfel]["claim"]}, citaties)
        eis(pad.endswith("/revisie"), "gemerged werk krijgt een revisie")
        gevonden = {"bewering": "", "bronnen": [{"url": "https://nos.nl/a", "titel": "x",
                                                 "uitgever": "NOS", "datum": "2025",
                                                 "soort": "nieuwsartikel",
                                                 "citaat": "was het RIVM de belangrijkste bron "
                                                           "voor de berichtgeving"}],
                    "gevonden": True, "toelichting": ""}
        verband = {
            "id": None, "soort": "verband", "claim": "", "relation_id": 77,
            "bron_naam": "RIVM", "doel_naam": "De Telegraaf", "entiteit_naam": None,
            "stance": "supporting", "mechanisme": "x", "relation_type": "bron_van",
            "probleem": "geen_argument", "bronnen": [], "status": "goedgekeurd"}
        bz.vraag_zoeker = lambda prompt: gevonden
        eis(bz.zoek(verband)["uitkomst"] == "niets", "geen bewering geformuleerd → niets")
        gevonden["bewering"] = "Het RIVM was de belangrijkste bron voor De Telegraaf."
        uit = bz.zoek(verband)
        eis(uit["uitkomst"] == "niets"
            and any("noemt De Telegraaf niet" in a["reden"] for a in uit["afgevallen"]),
            "v3: een bron die De Telegraaf niet noemt, draagt het verband niet (alleen 'de "
            "landelijke dagbladen')")
        telegraaf = ("Tijdens de coronacrisis was het RIVM de belangrijkste bron voor de "
                     "berichtgeving van De Telegraaf. " * 30)
        bz.bc.haal_bron = lambda bron, citaat=None: (telegraaf, "ok", bron["url"])
        eis(bz.zoek(verband)["uitkomst"] == "gevonden",
            "een bewering met beide partijen, een bron die beide noemt en een citaat dat in de "
            "bron staat → gevonden")
        gevonden["bewering"] = "Het RIVM was de belangrijkste bron voor de kranten."
        eis(bz.zoek(verband)["uitkomst"] == "niets",
            "een bewering zonder de tweede partij → niets (geen algemene uitspraak)")

        print("19. Opruimen: eerst repareren, dan beslissen")
        nu = datetime.datetime(2026, 10, 7, 12, 0)
        basis = {"id": 1, "a1": "twijfel", "a1_detail": "[bronchecker] de bron noemt geen datum",
                 "smaad": None, "smaad_reden": None, "smaad_herformulering": None,
                 "parent_argument_id": None, "created_at": "2026-10-07 10:00:00",
                 "heropend_op": None, "a1_op": "2026-10-07 11:00:00", "a2": None}

        def besluit(a, wacht_zoeker=(), pogingen=None, wacht_a2=()):
            return ab.motivatie_voor(a, wacht_a2=set(wacht_a2), wacht_zoeker=set(wacht_zoeker),
                                     pogingen=pogingen or {}, wachttijd=14, nu=nu)

        eis(besluit(basis, wacht_zoeker={1}) == (None, "bronzoeker"),
            "twijfel: eerst de bronzoeker")
        m, _ = besluit(basis, pogingen={"1": {"uitkomst": "gevonden", "nieuw_id": 99}})
        eis(m.startswith("automatische beoordeling: vervangen door #99"),
            "gevonden: verworpen met de vervanger erbij")
        m, _ = besluit(basis, pogingen={"1": {"uitkomst": "niets"}})
        eis("bevestigt het niet volledig" in m and "geen betere bron" in m
            and "noemt geen datum" in m, "niets gevonden: meteen verworpen, met de reden")
        m, _ = besluit(basis)
        eis(m is not None and "bevestigt het niet volledig" in m,
            "niet te repareren (bv. van de bronzoeker zelf): meteen verworpen, geen 14 dagen")
        m, _ = besluit({**basis, "a1": "klopt-niet", "parent_argument_id": 5})
        eis("het bezwaar houdt geen stand" in m, "een bezwaar dat geen stand houdt")
        eis(besluit({**basis, "a1": "klopt"}, wacht_a2={1}) == (None, "aanklager"),
            "wacht op de aanklager binnen de wachttijd")
        m, _ = besluit({**basis, "a1": "klopt", "a1_op": "2026-09-20 10:00:00"}, wacht_a2={1})
        eis("tegenspraak-certificaat" in m, "na de wachttijd zonder aanklager opgeschoond")
        m, _ = besluit({**basis, "smaad": "niet_feitelijk", "smaad_reden": "een mening als feit",
                        "smaad_herformulering": "X zei Y."})
        eis(m.startswith("automatische beoordeling: teruggekoppeld door de smaadtoets")
            and "Feitelijk zou zijn: X zei Y." in m, "de smaadtoets koppelt terug")
        eis(besluit({**basis, "a1": "klopt"}) == (None, None), "jong en 'klopt': niets te doen")

        print("20. Mechanisme-toewijzer: buiten het model wordt afgewezen, anders incuberen")
        mt = laad_script("mechanisme_toewijzer")
        mt.DB_PATH = db
        st, j = api("post", "/api/relations", "nieuws-scout",
                    {"source_id": partij, "target_id": medium, "relation_type": "alliantie"})
        assert st == 201, (st, j)
        buiten = j["id"]
        mt.bc.vraag_model = lambda *a, **k: {"mechanism_id": 0, "buiten_model": True,
                                             "reden": "Een partijfusie, geen invloed op media."}
        eis(mt.kies(buiten)["uitkomst"] == "buiten_model", "het model zegt: buiten het model")
        mt.bc.vraag_model = lambda *a, **k: {"mechanism_id": 0, "buiten_model": False,
                                             "reden": "Een patroon zonder mechanisme."}
        eis(mt.kies(buiten)["uitkomst"] == "geen", "een invloedspatroon zonder huis: incuberen")
        st, j = api("patch", f"/api/relations/{buiten}/status", "merge-service",
                    {"status": "afgewezen", "motivatie": "automatische beoordeling: buiten het "
                     "model — geen mechanisme past (test)"})
        eis(st == 200 and status("relations", buiten) == "afgewezen",
            "merge-service wijst een kandidaat zonder mechanisme af (met reden)")
        nu = datetime.datetime(2026, 10, 7, 12, 0)
        eis(not mt.mag_weer({"op": "2026-10-01T12:00:00", "uitkomst": "geen", "mech_max": 200},
                            nu, 200)
            and mt.mag_weer({"op": "2026-10-01T12:00:00", "uitkomst": "geen", "mech_max": 200},
                            nu, 201)
            and mt.mag_weer({"op": "2026-09-01T12:00:00", "uitkomst": "geen"}, nu, 200),
            "een incuberende kandidaat komt terug na 30 dagen, of zodra er een mechanisme bij kwam")

        print("21. Bronklassen: twee oordelen, bij verschil de voorzichtigste")
        bk = laad_script("bronklasse")

        def o(rel, ond="nl_systeem", wie="x"):
            return {"wie": wie, "reliability": rel, "onderwerp": ond, "reden": ""}

        nieuws = {"source_type": "nieuwsartikel", "heeft_loc": 1}
        eis(bk.beslis(nieuws, [o("regulier"), o("regulier")])[:3]
            == ("regulier", "nl_systeem", "eens"), "eens: dat geldt")
        eis(bk.beslis(nieuws, [o("kwaliteitsjournalistiek"), o("regulier", "algemeen")])[:3]
            == ("regulier", "algemeen", "oneens"),
            "oneens: de laagste klasse en het minst stellige onderwerp")
        eis(bk.beslis(nieuws, [o("primair"), o("primair")])[:3]
            == ("kwaliteitsjournalistiek", "nl_systeem", "lager"),
            "'primair' past niet bij een nieuwsartikel: de eerstvolgende lagere klasse")
        eis(bk.beslis({"source_type": "boek", "heeft_loc": 0},
                      [o("academisch"), o("academisch")])[0] == "kwaliteitsjournalistiek",
            "een hoge klasse zonder vindplaats haalt de poort niet")
        eis(bk.beslis({"source_type": "overig", "heeft_loc": 1},
                      [o("eigen_synthese"), o("grijs")])[0] == "eigen_synthese",
            "projectmateriaal blijft projectmateriaal")
        eis(bk.beslis(nieuws, [o("grijs"), o("opinie")])[0] == "grijs"
            and "eigen_synthese" not in [bk.beslis(nieuws, [o("grijs"), o("grijs")])[0]],
            "nooit vanzelf naar projectmateriaal")
        st, j = api("post", "/api/sources", "nieuws-scout",
                    {"title": "Nieuwsbericht over de omroep", "source_type": "nieuwsartikel",
                     "location": {"type": "url", "value": "https://bron.test/klasse"},
                     "reliability_voorgesteld": "kwaliteitsjournalistiek",
                     "onderwerp_voorgesteld": "nl_systeem"})
        assert st == 201, (st, j)
        klasse_bron = j["id"]
        c = lees()
        try:
            rijen = {r["id"]: r for r in bk.kandidaten(c)}
        finally:
            c.close()
        eis(klasse_bron in rijen and bk.voorstel_van(rijen[klasse_bron])["wie"] == "nieuws-scout",
            "een bron met een voorstel wacht op een besluit (het voorstel is het eerste oordeel)")
        rel_k, ond_k, uitkomst, uitleg = bk.beslis(
            rijen[klasse_bron], [bk.voorstel_van(rijen[klasse_bron]), o("regulier", wie="sonnet")])
        st, j = api("patch", f"/api/sources/{klasse_bron}/classificatie", "merge-service",
                    {"reliability": rel_k, "onderwerp": ond_k,
                     "motivatie": bk.motivatie(rijen[klasse_bron], [], rel_k, ond_k, uitleg)})
        c = lees()
        try:
            na = c.execute("SELECT reliability, reliability_voorgesteld FROM sources WHERE id = ?",
                           (klasse_bron,)).fetchone()
            nog = {r["id"] for r in bk.kandidaten(c)}
        finally:
            c.close()
        eis(st == 200 and tuple(na) == ("regulier", None) and klasse_bron not in nog,
            "het besluit (de voorzichtigste) staat, het voorstel is verwerkt")
        bk.LOG_PATH = Path(tmp) / "bronklasse_log.jsonl"
        bk.LOG_PATH.write_text(json.dumps({
            "source_id": klasse_bron, "http": 200,
            "oordelen": [bk.voorstel_van(rijen[klasse_bron]), o("regulier", wie="sonnet")]}),
            encoding="utf-8")
        c = lees()
        try:
            herzien = {r["id"]: r for r in bk.herzien_kandidaten(c)}
        finally:
            c.close()
        eis(klasse_bron in herzien
            and bk.voorstel_van(herzien[klasse_bron])["reliability"] == "kwaliteitsjournalistiek",
            "--herzien: een eigen besluit opnieuw, met het voorstel van toen uit het logboek")
        api("patch", f"/api/sources/{klasse_bron}/classificatie", "t-admin",
            {"reliability": "regulier", "onderwerp": "nl_systeem", "motivatie": "mens"})
        c = lees()
        try:
            herzien = {r["id"] for r in bk.herzien_kandidaten(c)}
        finally:
            c.close()
        eis(klasse_bron not in herzien, "wat een mens daarna zette, herziet de agent niet")

        print("22. Archiveren: wat een run al behandelde, houdt de rest niet tegen")
        ar = laad_script("archiveer_bronnen")
        log = Path(tmp) / "archiveer_log.jsonl"
        log.write_text("\n".join([
            '{"datum": "2026-10-06T12:00:00", "source_ids": [1, 2]}',
            '{"datum": "2026-09-01T12:00:00", "source_ids": [3]}', "kapot"]), encoding="utf-8")
        eis(ar.recent_behandeld(7, datetime.datetime(2026, 10, 7, 12, 0), pad=log) == {1, 2},
            "alleen de laatste 7 dagen tellen (kapotte regels worden overgeslagen)")
        eis(ab.ARCHIEF_KLAAR.search("Klaar: 3 bestaande snapshot(s) geregistreerd, 2 vers "
                                    "aangevraagd, 0 zonder snapshot, 1 door fout/rate-limit "
                                    "open.").groups() == ("3", "2", "0", "1"),
            "de ronde leest de uitkomst van het archiefscript")

        print("23. Bronchecker v3: gaat het bewijs over dít verband?")
        bc.DB_PATH = db
        pagina_alg = ("Op een bijeenkomst zei de partijleider dat journalisten gewoon tuig van "
                      "de richel zijn, en dat herhaalde hij later. " * 20)
        algemeen_arg = argument(invloed, "assistent",
                                claim="Denktank Voorbeeld viel Omroep Voorbeeld publiekelijk aan.",
                                citations=[{"source_id": bron("assistent"),
                                            "quote": "journalisten gewoon tuig van de richel zijn"}])
        gevraagd = {}

        def nep_model(prompt, schema, systeem=None, model=None):
            gevraagd["prompt"], gevraagd["schema"] = prompt, schema
            return dict(gevraagd["antwoord"])

        bc.haal_bron = lambda bron_, citaat=None: (pagina_alg, "ok", bron_.get("url"))
        bc.vraag_model = nep_model
        gevraagd["antwoord"] = {"oordeel": "draagt", "over_dit_verband": "nee",
                                "ontbreekt": "Omroep Voorbeeld",
                                "reden": "de bron gaat over journalisten in het algemeen"}
        c = lees()
        try:
            arg_rij = c.execute("SELECT * FROM arguments WHERE id = ?", (algemeen_arg,)).fetchone()
            eis(bc.verband_van(c, arg_rij)["doel"] == "Omroep Voorbeeld",
                "het verband van een root op een relatie")
            uit = bc.beoordeel_argument(c, arg_rij)
        finally:
            c.close()
        eis(gevraagd["schema"] is bc.SCHEMA_VERBAND and "Denktank Voorbeeld" in gevraagd["prompt"]
            and "Omroep Voorbeeld" in gevraagd["prompt"] and "'de pers'" in gevraagd["prompt"],
            "de vraag noemt beide partijen en de regel over groepen in het algemeen")
        eis(uit["verdict"] == "klopt-niet" and "gaat niet over Omroep Voorbeeld" in uit["detail"]
            and "citaat letterlijk gevonden" in uit["detail"],
            "een bron over 'journalisten' draagt het verband met één medium niet → klopt-niet")
        gevraagd["antwoord"] = {"oordeel": "draagt", "over_dit_verband": "ja", "ontbreekt": "",
                                "reden": "de bron noemt beide"}
        c = lees()
        try:
            uit = bc.beoordeel_argument(c, c.execute("SELECT * FROM arguments WHERE id = ?",
                                                     (algemeen_arg,)).fetchone())
        finally:
            c.close()
        eis(uit["verdict"] == "klopt", "over dít verband en gedragen → klopt")
        ent_bron = bron("assistent")  # eerst de bron (de API schrijft zelf)
        c = lees()
        try:
            ent_arg = c.execute("INSERT INTO arguments (entity_id, stance, claim, status, "
                                "contributed_by) VALUES (?, 'supporting', 'Anouk Verbeek is "
                                "journalist.', 'voorgesteld', 'assistent')", (persoon,)).lastrowid
            c.execute("INSERT INTO citations (argument_id, source_id, quote) VALUES (?, ?, ?)",
                      (ent_arg, ent_bron, "journalisten gewoon tuig van de richel zijn"))
            c.commit()
            gevraagd["antwoord"] = {"oordeel": "draagt", "reden": "x"}
            bc.beoordeel_argument(c, c.execute("SELECT * FROM arguments WHERE id = ?",
                                               (ent_arg,)).fetchone())
        finally:
            c.close()
        eis(gevraagd["schema"] is bc.SCHEMA_ARGUMENT,
            "een argument over één entiteit krijgt de gewone vraag (geen verband)")
        oud_v2 = argument(invloed, "assistent", claim="Denktank Voorbeeld leverde Omroep "
                                                      "Voorbeeld in 2022 een rapport aan.")
        api("post", f"/api/arguments/{oud_v2}/merge", "t-admin")
        api("post", f"/api/arguments/{oud_v2}/herverificatie", "bronchecker",
            {"verdict": "klopt", "detail": "[bronchecker v2] citaat letterlijk gevonden"})
        al_v3 = argument(invloed, "assistent", claim="Omroep Voorbeeld citeerde Denktank "
                                                     "Voorbeeld op 4 april 2025.")
        api("post", f"/api/arguments/{al_v3}/merge", "t-admin")
        api("post", f"/api/arguments/{al_v3}/herverificatie", "bronchecker",
            {"verdict": "klopt", "detail": "[bronchecker v3] citaat letterlijk gevonden"})
        buiten = argument(ander_doel, "assistent", claim="Partij Voorbeeld vroeg Denktank "
                                                         "Voorbeeld in 2021 om advies.")
        api("post", f"/api/arguments/{buiten}/merge", "t-admin")
        api("post", f"/api/arguments/{buiten}/herverificatie", "bronchecker",
            {"verdict": "klopt", "detail": "[bronchecker v2] citaat letterlijk gevonden"})
        c = lees()
        try:
            herbekijk = {r["id"] for r in bc.specifiek_kandidaten(c)}
        finally:
            c.close()
        eis(oud_v2 in herbekijk and al_v3 not in herbekijk and buiten not in herbekijk,
            "--specifiek: alleen verbanden uit het nieuws, alleen een 'klopt' van een eerdere "
            "versie (geen massale herbeoordeling)")
        eis(bc.zonder_versie("[bronchecker v2] citaat x") == "citaat x"
            and bc.zonder_versie("[bronchecker] y") == "y", "het versiemerk gaat eraf")

        print("24. Bronzoeker: één feit per bewering, een bron noemt beide partijen")
        bz.DB_PATH = db

        def via_client(api_url, token, pad, body):
            server._rate_emmers.clear()
            r = client.post(pad, json=body, headers={"Authorization": f"Bearer {token}"})
            return r.status_code, (r.get_json() or {})

        bz.api_post = via_client
        twee = ("Denktank Voorbeeld leverde in 2025 duiding aan Omroep Voorbeeld. Een analist "
                "van Denktank Voorbeeld trad op 3 maart op bij Omroep Voorbeeld. ") * 20
        bz.bc.haal_bron = lambda bron_, citaat=None: (twee, "ok", bron_["url"])
        bijbron = lambda citaat: {"url": "https://nos.nl/x", "titel": "x", "uitgever": "NOS",  # noqa: E731
                                  "datum": "2025-03-03", "soort": "nieuwsartikel", "citaat": citaat}
        bz.vraag_zoeker = lambda prompt: {
            "gevonden": True, "toelichting": "",
            "bewering": "Denktank Voorbeeld leverde in 2025 duiding aan Omroep Voorbeeld.",
            "bronnen": [bijbron("Denktank Voorbeeld leverde in 2025 duiding aan Omroep Voorbeeld")],
            "extra": [{"bewering": "Een analist van Denktank Voorbeeld trad op 3 maart 2025 op "
                                   "bij Omroep Voorbeeld.",
                       "bronnen": [bijbron("Een analist van Denktank Voorbeeld trad op 3 maart "
                                           "op bij Omroep Voorbeeld")]},
                      {"bewering": "De Haya van Someren Stichting is het opleidingsinstituut van "
                                   "de VVD.",
                       "bronnen": [bijbron("Denktank Voorbeeld leverde in 2025 duiding")]}]}
        splits = {"id": None, "soort": "verband", "claim": "", "relation_id": invloed,
                  "bron_naam": "Denktank Voorbeeld", "doel_naam": "Omroep Voorbeeld",
                  "entiteit_naam": None, "entity_id": None, "stance": "supporting",
                  "mechanisme": "x", "relation_type": "beinvloeding", "property": None,
                  "probleem": "geen_argument", "bronnen": [], "status": "goedgekeurd"}
        uit = bz.zoek(splits)
        eis(uit["uitkomst"] == "gevonden" and len(uit["extra"]) == 1
            and any("afgesplitst feit valt af" in a["reden"] for a in uit["afgevallen"]),
            "een tweede feit over dezelfde partijen blijft (eigen bron); een feit over een ander "
            "verband valt af")
        nieuw_id, fout = bz.dien_in("", tokens["bronzoeker"], splits, uit)
        c = lees()
        try:
            afgesplitst_rij = c.execute("SELECT * FROM arguments WHERE reasoning LIKE ?",
                                        (f"Afgesplitst van #{nieuw_id}%",)).fetchone()
        finally:
            c.close()
        eis(nieuw_id and fout is None and afgesplitst_rij is not None
            and afgesplitst_rij["relation_id"] == invloed
            and afgesplitst_rij["claim"].startswith("Een analist"),
            "elk feit een eigen argument op hetzelfde verband ('Afgesplitst van #…')")
        eenzijdig = "Een analist trad op 3 maart op bij Omroep Voorbeeld. " * 30
        bz.bc.haal_bron = lambda bron_, citaat=None: (eenzijdig, "ok", bron_["url"])
        goed, reden = bz.natrekken(bijbron("Een analist trad op 3 maart op bij Omroep Voorbeeld"),
                                   ["Denktank Voorbeeld", "Omroep Voorbeeld"])
        eis(goed is None and "noemt Denktank Voorbeeld niet" in reden,
            "een bron die één partij niet noemt, telt niet")
        eis(bz.noemt("trainer bij de Haya van Somerenstichting", "Haya van Someren Stichting")
            and not bz.noemt("trainer bij de VVD", "Haya van Someren Stichting"),
            "een naam van meerdere woorden telt ook aaneengeschreven")
        eis("Eén feit per bewering" in bz.OPDRACHT and "neutrale eigen woorden" in bz.OPDRACHT
            and "BEIDE partijen" in bz.OPDRACHT, "de opdracht noemt de drie regels")

        print("25. Opschonen: dubbele bronnen en verbanden, registerrollen, samenvoegen")
        import opschonen
        import voorstellen as vs
        import viz_data
        # Dezelfde pagina onder een andere titel is dezelfde bron
        st, j1 = api("post", "/api/sources", "nieuws-scout",
                     {"title": "Pagina A", "source_type": "website",
                      "location": {"type": "url", "value": "https://www.dubbel.test/stuk/?utm_source=x"}})
        st2, j2 = api("post", "/api/sources", "nieuws-scout",
                      {"title": "Pagina A (andere titel)", "source_type": "website",
                       "location": {"type": "url", "value": "http://dubbel.test/stuk"}})
        eis(st == 201 and st2 == 200 and j2.get("hergebruikt") and j2["id"] == j1["id"],
            "POST /api/sources hergebruikt een bron met dezelfde url")
        # Twee bronnen die al dubbel staan (van vóór die regel): de jongste gaat op in de oudste
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        oud_bron, jong_bron = j1["id"], c.execute(
            "INSERT INTO sources (title, source_type, cluster_key) VALUES ('Pagina A kopie', "
            "'website', 'ander-cluster')").lastrowid
        c.execute("INSERT INTO source_locations (source_id, location_type, location) VALUES "
                  "(?, 'url', 'https://dubbel.test/stuk/')", (jong_bron,))
        c.commit()
        c.close()
        dubbel_rel = relatie(partij, persoon, "lidmaatschap")
        arg_jong = argument(dubbel_rel, "nieuws-scout", citations=[
            {"source_id": jong_bron, "quote": "Anouk Verbeek is lid."}])
        st, j = api("get", f"/api/beoordeling/bron_dubbel/{jong_bron}", "merge-service")
        eis(j.get("toegestaan") and j.get("blijft") == oud_bron, "droogloop: de jongste bron is dubbel")
        st, j = api("post", f"/api/beoordeling/bron_dubbel/{jong_bron}", "merge-service")
        c = sqlite3.connect(db)
        eis(st == 200 and j["citaties"] == 1
            and c.execute("SELECT source_id FROM citations WHERE argument_id = ?",
                          (arg_jong,)).fetchone()[0] == oud_bron
            and c.execute("SELECT 1 FROM sources WHERE id = ?", (jong_bron,)).fetchone() is None
            and c.execute("SELECT 1 FROM edit_log WHERE table_name = 'sources' AND record_id = ? "
                          "AND action = 'deleted'", (jong_bron,)).fetchone(),
            "de citatie verhuist, de dubbele bron verdwijnt (oude rij in edit_log)")
        c.close()
        st, j = api("post", f"/api/beoordeling/bron_dubbel/{oud_bron}", "merge-service")
        eis(st == 409, "de oudste bron blijft")

        # Dubbele verbanden: twee keer hetzelfde feit
        def gedragen_verband(src, tgt, rtype, **velden):
            rid = relatie(src, tgt, rtype)
            arg = argument(rid, "nieuws-scout")
            a1(arg)
            merge(arg)
            c = sqlite3.connect(db)
            # gemerged, ook als A7 voor dit type ook A2 vraagt (dat toetsen stap 3–5)
            c.execute("UPDATE arguments SET status = 'ongecontroleerd' WHERE id = ? AND status = "
                      "'voorgesteld'", (arg,))
            c.execute("UPDATE relations SET status = 'goedgekeurd'"
                      + "".join(f", {k} = ?" for k in velden) + " WHERE id = ?",
                      (*velden.values(), rid))
            c.commit()
            c.close()
            return rid

        eerste = gedragen_verband(denktank, medium, "alliantie")
        tweede = gedragen_verband(denktank, medium, "alliantie", active_from="2020-01-01")
        st, j = api("get", f"/api/beoordeling/dubbel/{eerste}", "merge-service")
        eis(not j["toegestaan"], "het oudste van twee gelijke verbanden blijft")
        st, j = api("post", f"/api/beoordeling/dubbel/{tweede}", "merge-service")
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        eis(st == 200 and j["blijft"] == eerste and status("relations", tweede) == "afgewezen"
            and c.execute("SELECT active_from FROM relations WHERE id = ?",
                          (eerste,)).fetchone()[0] == "2020-01-01"
            and c.execute("SELECT COUNT(*) FROM arguments WHERE relation_id = ? AND status <> "
                          "'verworpen'", (tweede,)).fetchone()[0] == 0,
            "het jongste wordt afgewezen (boom mee), de begindatum gaat naar het blijvende")
        c.close()
        # In beide richtingen dezelfde tweezijdige band: één blijft
        heen = gedragen_verband(persoon, denktank, "adviseur")
        terug = gedragen_verband(denktank, persoon, "adviseur")
        oordelen = [api("get", f"/api/beoordeling/dubbel/{r}", "merge-service")[1]["toegestaan"]
                    for r in (heen, terug)]
        eis(sorted(oordelen) == [False, True], "beide richtingen: precies één is dubbel")
        # Een ambt naast een band met een ánder mechanisme is een ander feit
        ander_mech = sqlite3.connect(db).execute(
            "SELECT id FROM mechanisms WHERE NOT vervangen AND id <> ? ORDER BY id LIMIT 1",
            (MECH,)).fetchone()[0]
        ambt = gedragen_verband(persoon, medium, "ambt")
        band = gedragen_verband(persoon, medium, "bestuurder", mechanism_id=ander_mech)
        eis(not api("get", f"/api/beoordeling/dubbel/{band}", "merge-service")[1]["toegestaan"],
            "een band met een ander mechanisme naast een ambt blijft")
        c = sqlite3.connect(db)
        c.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?", (MECH, band))
        c.commit()
        c.close()
        eis(api("get", f"/api/beoordeling/dubbel/{band}", "merge-service")[1]["toegestaan"]
            and not api("get", f"/api/beoordeling/dubbel/{ambt}", "merge-service")[1]["toegestaan"],
            "met hetzelfde mechanisme wint het ambt")
        # Wat alleen een mens goedkeurde, blijft staan
        door_mens = relatie(medium, partij, "alliantie")
        arg = argument(door_mens, "nieuws-scout")
        a1(arg)
        merge(arg)
        c = sqlite3.connect(db)
        c.execute("UPDATE arguments SET status = 'ongecontroleerd' WHERE id = ?", (arg,))
        c.commit()
        c.close()
        goedkeuren("relations", door_mens)
        kopie = gedragen_verband(medium, partij, "alliantie")
        eis(not api("get", f"/api/beoordeling/dubbel/{door_mens}", "merge-service")[1]["toegestaan"]
            and api("get", f"/api/beoordeling/dubbel/{kopie}", "merge-service")[1]["toegestaan"],
            "een besluit van een mens blijft; de kopie zonder mens gaat")

        # Registerrollen: een gekoppelde organisatie krijgt de rol die het register geeft
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        tokens["register-import"] = auth.new_token()
        c.execute("INSERT OR IGNORE INTO users (username, kind, role, provenance, token_hash) "
                  "VALUES ('register-import', 'agent', 'bijdrager', 'test', ?)",
                  (auth.hash_token(tokens["register-import"]),))
        c.execute("UPDATE users SET token_hash = ? WHERE username = 'register-import'",
                  (auth.hash_token(tokens["register-import"]),))
        rol = c.execute("SELECT name FROM roles WHERE NOT vervangen ORDER BY id LIMIT 1").fetchone()[0]
        c.commit()
        c.close()
        kop["register-import"] = {"Authorization": f"Bearer {tokens['register-import']}"}
        ministerie = entiteit("Ministerie van Voorbeeldzaken", "overheidsinstelling")
        st, j = api("post", f"/api/entities/{ministerie}/register", "register-import",
                    {"rollen": [rol], "externe_ids": [{"stelsel": "oo", "waarde": "123"}]})
        st2, j2 = api("post", f"/api/entities/{ministerie}/register", "register-import",
                      {"rollen": [rol]})
        st3, _ = api("post", f"/api/entities/{ministerie}/register", "register-import",
                     {"rollen": ["bestaat_niet"]})
        c = sqlite3.connect(db)
        eis(st == 200 and j["gewijzigd"].get("primaire_rol") == rol and not j2["gewijzigd"]
            and st3 == 400
            and c.execute("SELECT 1 FROM instantiations WHERE entity_id = ? AND role_id IS NOT "
                          "NULL", (ministerie,)).fetchone(),
            "registerrol: aanvullen, nooit overschrijven, onbekende rol geweigerd")
        c.close()

        # Samenvoegen van entiteiten neemt externe id's en rollen mee
        dubbel_min = entiteit("Ministerie van Voorbeeldzaken (register)", "overheidsinstelling")
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        c.execute("UPDATE externe_ids SET entity_id = ? WHERE entity_id = ?", (dubbel_min, ministerie))
        vid = c.execute("INSERT INTO voorstellen (soort, titel, payload, ingediend_door) VALUES "
                        "('samenvoegen', 't', '{}', 'assistent')").lastrowid
        uit = vs.voer_uit(c, "samenvoegen", {"element_type": "entiteit", "oud_ids": [dubbel_min],
                                             "doel": {"bestaand_id": ministerie},
                                             "herbevestigd": {}, "motivatie": "test"}, vid)
        eis(uit["verplaatst"]["externe_ids"] == 1
            and c.execute("SELECT entity_id FROM externe_ids WHERE stelsel = 'oo' AND waarde = '123'"
                          ).fetchone()[0] == ministerie,
            "samenvoegen: de externe id gaat naar de opvolger")
        c.rollback()
        c.close()

        # De viz: een verband met een verstreken einddatum is niet meer actief
        c = sqlite3.connect(db)
        c.execute("UPDATE relations SET active_until = '2001-01-01' WHERE id = ?", (eerste,))
        c.commit()
        rel = next(r for r in viz_data.export_data(c)["relations"] if r["id"] == eerste)
        c.close()
        eis(not rel["active"], "viz: een afgelopen verband is niet actief")
        eis(opschonen.url_sleutel("https://WWW.Voorbeeld.nl/a/?b=1&utm_medium=x#z")
            == "voorbeeld.nl/a?b=1", "url-sleutel: host, www, slash, tracking en fragment")

        print("\nALLE TESTS VAN DE AUTOMATISCHE BEOORDELING GESLAAGD")


if __name__ == "__main__":
    main()
