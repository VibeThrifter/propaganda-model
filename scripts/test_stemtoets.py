#!/usr/bin/env python3
"""
End-to-end-test van de stemtoets en wat erbij hoort (eigenaarsbesluit 2026-10-08: "deze taal
moeten we niet overnemen … waak hier streng voor"; "PVV censureert AD … niet van belang"):

  * het lexicon van de eigen stem (validation.eigen_stem_treffers) en de geratchete check
    NEUTRALITEIT-EIGEN-STEM;
  * POST /api/stemtoets: alleen een ander account dan de auteur, alleen over de huidige tekst
    (tekst_hash), één oordeel per account (herzien werkt het bij);
  * de immuunpoort (A7): niets uit de praktijklaag merget zonder 'neutraal' (registerregels en
    theorie niet; kill-switch PROPAGANDA_STEMTOETS=0), ook een ondergraving niet;
  * scripts/stemtoets.py: kandidaten (voorstellen eerst, lexicon-treffers eerst in de
    veegronde, registerregels en theorie niet, een getoetste tekst niet opnieuw) en de ronde met
    een nagebootst model;
  * scripts/automatische_beoordeling.py: terugkoppelen + neutrale versie, stemrevisie van
    gemerged werk, beschrijvingen herschrijven (nooit van een mens, hooguit twee keer),
    verbanden zonder bron afwijzen (na de bronzoeker, niet als er iets loopt of een mens het
    goedkeurde, terug te draaien met heraanmelden), en de verificatie na een nieuwer
    'klopt-niet' (bronchecker v3).

Bouwt een verse database in een tijdelijke map; de live database wordt NOOIT aangeraakt. Geen
modelaanroepen: het taalmodel wordt nagebootst.

Gebruik: python3 scripts/test_stemtoets.py
Exit-code 0 = alles groen.
"""
import argparse
import importlib.util
import json
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


def test_lexicon():
    print("1. Het lexicon van de eigen stem")
    import validation as v
    fout = [
        "De PVV valt de pers publiekelijk aan en ondermijnt zo het vertrouwen in de "
        "journalistiek: PVV-leider Wilders noemde journalisten 'gewoon tuig van de richel'.",
        "PVV wil publieke omroep afschaffen. Directe bedreiging journalistieke infrastructuur.",
        "PVV valt regelmatig 'linkse' media aan, ondermijnt vertrouwen",
        "Liberale partij, onderdeel van de neoliberale consensus.",
        "Rechts-populistische partij. Wil publieke omroep afschaffen.",
        "Jarenlang kregen signalen weinig gehoor in mainstream media.",
    ]
    goed = [
        "PVV-leider Wilders noemde journalisten in juni 2021 \"tuig van de richel\".",
        "Volgens de NVJ ondermijnt de uitspraak het vertrouwen in de pers.",
        "Peter R. de Vries werd jarenlang met de dood bedreigd.",
        "Kamran Ullah vormt sinds 1 juni 2023 de hoofdredactie van De Telegraaf.",
        "Het Commissariaat noemde de uitzending 'propaganda' in zijn besluit.",
        "De PVV wil volgens haar verkiezingsprogramma de publieke omroep afschaffen.",
    ]
    eis(all(v.eigen_stem_treffers(t) for t in fout),
        "oordelen over gevolgen, etiketten en retoriek in de eigen stem worden herkend")
    eis(not any(v.eigen_stem_treffers(t) for t in goed),
        "feiten, citaten en toegeschreven oordelen niet")
    eis(v.eigen_stem_treffers("Peter R. de Vries werd bedreigd.", streng=False)
        and not v.eigen_stem_treffers("Peter R. de Vries werd bedreigd."),
        "het ruime lexicon wijst de stemtoets ook twijfelgevallen aan, het strenge niet")


def main():
    os.environ["PROPAGANDA_AUTO_MERGE"] = "1"
    os.environ["PROPAGANDA_AUTOMATISCHE_BEOORDELING"] = "1"
    os.environ["PROPAGANDA_STEMTOETS"] = "1"
    test_lexicon()
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
        import bronchecker as bc
        import bronzoeker as bz
        import smaadtoets as sm
        import stemtoets as st
        server.DB_PATH = db
        server._rate_emmers.clear()
        for module in (ab, bc, bz, sm, st):
            module.DB_PATH = db
        eis(st.tekst_hash("Een  tekst\n met witruimte ") == server.stem_hash("Een tekst met witruimte")
            and st.tekst_hash("a") != st.tekst_hash("b"),
            "het script en de server rekenen dezelfde tekst_hash (witruimte telt niet)")

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        tokens = {}
        for naam, rol, kind in (("nieuws-scout", "bijdrager", "agent"),
                                ("assistent", "bijdrager", "agent"),
                                ("bronchecker", "bijdrager", "agent"),
                                ("aanklager-agent", "bijdrager", "agent"),
                                ("merge-service", "reviewer", "agent"),
                                ("bronzoeker", "bijdrager", "agent"),
                                ("stemtoets", "bijdrager", "agent"),
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
        PVV = conn.execute("SELECT id FROM entities WHERE name = 'PVV'").fetchone()[0]
        VVD = conn.execute("SELECT id FROM entities WHERE name = 'VVD'").fetchone()[0]
        conn.close()

        client = server.app.test_client()
        kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

        def api(methode, pad, naam, body=None):
            server._rate_emmers.clear()
            r = getattr(client, methode)(pad, json=body, headers=kop[naam])
            return r.status_code, (r.get_json() or {})

        def via_client(method, pad, token, body=None):
            """De HTTP-aanroepen van de scripts gaan in de test via de test-client."""
            server._rate_emmers.clear()
            r = client.open(pad, method=method, json=body,
                            headers={"Authorization": f"Bearer {token}"})
            return r.status_code, (r.get_json() or {})

        ab.req = via_client
        bz.api_post = lambda api_url, token, pad, body: via_client("POST", pad, token, body)
        for naam, module in (("bronzoeker", bz), ("stemtoets", st)):
            pad = Path(tmp) / f"{naam}.token"
            pad.write_text(tokens[naam])
            module.DEFAULT_TOKEN = pad
        bz.POGINGEN_PATH = Path(tmp) / "bronzoeker_pogingen.json"  # de server leest hier ook
        st.LOG_PATH = Path(tmp) / "stemtoets_log.jsonl"

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

        def bron(maker="nieuws-scout"):
            teller["n"] += 1
            s, j = api("post", "/api/sources", maker,
                       {"title": f"Testbron {teller['n']}", "source_type": "website",
                        "location": {"type": "url", "value": f"https://bron.test/{teller['n']}"}})
            assert s == 201, (s, j)
            return j["id"]

        def entiteit(naam_ent, typ="persoon", maker="nieuws-scout"):
            s, j = api("post", "/api/entities", maker, {"name": naam_ent, "type": typ})
            assert s == 201, (s, j)
            return j["id"]

        def goedkeuren(tabel, rid):
            s, j = api("patch", f"/api/{tabel}/{rid}/status", "t-admin",
                       {"status": "goedgekeurd", "motivatie": "test"})
            assert s == 200, (s, j)

        def relatie(src, tgt, rtype, maker="nieuws-scout"):
            s, j = api("post", "/api/relations", maker,
                       {"source_id": src, "target_id": tgt, "relation_type": rtype,
                        "mechanism_id": MECH})
            assert s == 201, (s, j)
            return j["id"]

        def argument(rid, maker, stance="supporting", **extra):
            teller["n"] += 1
            body = {"relation_id": rid, "stance": stance, "negeer_duplicaten": True,
                    "claim": f"Bewering {teller['n']} over relatie {rid}.",
                    "citations": [{"source_id": bron(maker), "quote": f"Citaat {teller['n']}."}]}
            body.update(extra)
            s, j = api("post", "/api/arguments", maker, body)
            assert s == 201, (s, j)
            return j["id"]

        def a1(arg_id, verdict="klopt", herzien=False):
            body = {"verdict": verdict, "detail": "[bronchecker v3] test"}
            if herzien:
                body["herzien"] = True
            s, j = api("post", f"/api/arguments/{arg_id}/herverificatie", "bronchecker", body)
            assert s in (200, 201), (s, j)

        def a2(arg_id):
            s, j = api("post", f"/api/arguments/{arg_id}/tegenspraak", "aanklager-agent",
                       {"verdict": "overleefd", "detail": "test"})
            assert s == 201, (s, j)

        def tekst_van(soort, doel_id):
            tabel, kolom = {"argument": ("arguments", "claim"), "relatie": ("relations", "description"),
                            "entiteit": ("entities", "description")}[soort]
            return rij(tabel, doel_id)[kolom]

        def stem(soort, doel_id, verdict, herformulering=None, door="stemtoets", herzien=True):
            body = {"soort": soort, "doel_id": doel_id, "verdict": verdict, "reden": "test",
                    "tekst_hash": st.tekst_hash(tekst_van(soort, doel_id)), "herzien": herzien}
            if herformulering:
                body["herformulering"] = herformulering
            return api("post", "/api/stemtoets", door, body)

        def merge(arg_id):
            return api("post", f"/api/arguments/{arg_id}/auto_merge", "merge-service")

        def ronde_args(**anders):
            basis = dict(droog=False, max_stemrevisie=20, max_beschrijving=40, max_zonder_bron=20,
                         zonder_bronzoeker=False, max_zoek=8, wachttijd_dagen=14,
                         max_stem_nieuw=200, max_stem_veeg=48)
            basis.update(anders)
            return argparse.Namespace(**basis)

        stil = lambda *a, **k: None  # noqa: E731
        persoon = entiteit("Anouk Verbeek")
        partij = entiteit("Partij Voorbeeld", "partij")
        medium = entiteit("Omroep Voorbeeld", "mediaorganisatie")
        denktank = entiteit("Denktank Voorbeeld", "denktank")
        for e in (persoon, partij, medium, denktank):
            goedkeuren("entities", e)

        print("3. POST /api/stemtoets: onafhankelijk, over de huidige tekst, één oordeel per account")
        lid = relatie(partij, persoon, "lidmaatschap")
        feit = argument(lid, "nieuws-scout", claim="Anouk Verbeek is lid van Partij Voorbeeld.")
        goedkeuren("relations", lid)
        s, _ = api("post", "/api/stemtoets", "stemtoets",
                   {"soort": "argument", "doel_id": feit, "verdict": "neutraal", "reden": "x",
                    "tekst_hash": "verkeerd"})
        eis(s == 409, "een oordeel over een andere tekst (tekst_hash wijkt af) → 409")
        s, _ = stem("argument", feit, "neutraal", door="nieuws-scout")
        eis(s == 403, "de auteur toetst zijn eigen tekst niet")
        s, _ = api("post", "/api/stemtoets", "stemtoets",
                   {"soort": "fout", "doel_id": feit, "verdict": "neutraal", "reden": "x",
                    "tekst_hash": "x"})
        eis(s == 400, "onbekende soort → 400")
        s, _ = api("post", "/api/stemtoets", "stemtoets",
                   {"soort": "argument", "doel_id": 999999, "verdict": "neutraal", "reden": "x",
                    "tekst_hash": "x"})
        eis(s == 404, "onbekend doel → 404")
        s, j = stem("argument", feit, "niet_neutraal", herformulering="Feit.", herzien=False)
        eis(s == 201, f"oordeel vastgelegd ({j})")
        s, _ = stem("argument", feit, "neutraal", herzien=False)
        eis(s == 409, "zelfde tekst, zelfde account: alleen met 'herzien'")
        s, j = stem("argument", feit, "niet_neutraal", herformulering="Feit.")
        eis(s == 200 and j["herzien"], "met 'herzien' wordt het eigen oordeel bijgewerkt")

        print("4. A7: niets uit de praktijklaag merget zonder 'neutraal'")
        a1(feit)
        s, j = merge(feit)
        eis(s == 409 and j["bucket"] == "geblokkeerd-hoog-inzet"
            and any("stemtoets: niet neutraal" in r for r in j["redenen"]),
            "niet neutraal → geblokkeerd, ook een structuurfeit met A1 'klopt'")
        feit2 = argument(lid, "nieuws-scout", claim="Anouk Verbeek staat op de ledenlijst.")
        a1(feit2)
        s, j = merge(feit2)
        eis(s == 409 and any("stemtoets: nog geen oordeel" in r for r in j["redenen"]),
            "zonder stemtoets geparkeerd")
        os.environ["PROPAGANDA_STEMTOETS"] = "0"
        s, j = merge(feit2)
        os.environ["PROPAGANDA_STEMTOETS"] = "1"
        eis(s == 200 and j["merged"], "kill-switch PROPAGANDA_STEMTOETS=0: de oude poort")
        s, _ = stem("argument", feit, "neutraal")
        s, j = merge(feit)
        eis(s == 200 and j["merged"], "neutraal + A1 'klopt' → gemerged (structuurfeit)")
        invloed = relatie(denktank, medium, "beinvloeding", maker="assistent")
        claim = argument(invloed, "assistent",
                         claim="Denktank Voorbeeld levert Omroep Voorbeeld wekelijks duiding.")
        goedkeuren("relations", invloed)
        a1(claim)
        a2(claim)
        stem("argument", claim, "neutraal")
        s, j = merge(claim)
        eis(s == 200 and j["merged"], "een invloedsclaim: A1 + A2 + neutraal → gemerged")
        s, j = api("post", "/api/arguments", "bronzoeker",
                   {"parent_argument_id": claim, "stance": "contradicting",
                    "claim": "De bron draagt de bewering niet.",
                    "reasoning": "Het citaat noemt geen wekelijkse duiding."})
        assert s == 201, (s, j)
        bezwaar = j["id"]
        a1(bezwaar)
        s, j = merge(bezwaar)
        eis(s == 409 and any("stemtoets" in r for r in j["redenen"]),
            "ook een ondergraving spreekt in de eigen stem: eerst de stemtoets")
        stem("argument", bezwaar, "neutraal")
        s, j = merge(bezwaar)
        eis(s == 200 and j["merged"], "het bezwaar merget na 'neutraal'")
        c = lees()
        try:
            rol = c.execute("SELECT MIN(id) FROM roles").fetchone()[0]
            theorie = c.execute("INSERT INTO arguments (role_id, stance, claim, status, "
                                "contributed_by) VALUES (?, 'supporting', 'Herman & Chomsky "
                                "beschrijven deze rol.', 'voorgesteld', 'assistent')",
                                (rol,)).lastrowid
            register_bron = c.execute("INSERT INTO sources (title, source_type, cluster_key) "
                                      "VALUES ('Register', 'dataset', 'register:tk')").lastrowid
            reg = c.execute("INSERT INTO arguments (relation_id, stance, claim, status, "
                            "contributed_by) VALUES (?, 'supporting', 'Registerregel.', "
                            "'voorgesteld', 'nieuws-scout')", (lid,)).lastrowid
            c.execute("INSERT INTO citations (argument_id, source_id, quote, methode) VALUES "
                      "(?, ?, 'regel', 'officieel_register_scrape')", (reg, register_bron))
            c.commit()
            eis(not server._stemtoets_vereist(c, c.execute("SELECT * FROM arguments WHERE id = ?",
                                                           (theorie,)).fetchone())
                and not server._stemtoets_vereist(c, c.execute(
                    "SELECT * FROM arguments WHERE id = ?", (reg,)).fetchone()),
                "theorie-argumenten en letterlijke registerregels hebben geen stemtoets nodig")
        finally:
            c.close()

        print("5. scripts/stemtoets.py: kandidaten en een ronde (model nagebootst)")
        luid = argument(invloed, "assistent",
                        claim="Denktank Voorbeeld ondermijnt zo het vertrouwen in Omroep Voorbeeld.")
        c = lees()
        try:
            kand = st.kandidaten(c, max_nieuw=500, max_veeg=500)
            sleutels = [(k["soort"], k["doel_id"]) for k in kand]
        finally:
            c.close()
        eis(("argument", luid) in sleutels and ("argument", theorie) not in sleutels
            and ("argument", reg) not in sleutels and ("argument", feit) not in sleutels,
            "een voorstel ja; theorie, registerregels en wat ik al toetste (zelfde tekst) niet")
        eis(sleutels.index(("argument", luid)) < sleutels.index(("entiteit", PVV)),
            "voorstellen gaan voor de veegronde")
        beschrijvingen = [s_ for s_ in sleutels if s_[0] != "argument"]
        eis(beschrijvingen.index(("entiteit", PVV)) < beschrijvingen.index(("entiteit", partij))
            if ("entiteit", partij) in beschrijvingen else ("entiteit", PVV) in beschrijvingen,
            "in de veegronde eerst wat het strenge lexicon aanwijst (PVV: 'rechts-populistisch')")
        eis("Denktank Voorbeeld" in st.context_van(lees(), {"soort": "argument", "doel_id": luid,
                                                          "relation_id": invloed, "entity_id": None,
                                                          "stance": "supporting", "reply": False,
                                                          "property": None})
            and "Citaat uit de bron" in st.context_van(lees(), {
                "soort": "argument", "doel_id": luid, "relation_id": invloed, "entity_id": None,
                "stance": "supporting", "reply": False, "property": None}),
            "de context noemt het verband en de citaten (zodat een oordeel toe te schrijven is)")
        gezien = {}

        def nep_model(prompt, schema, systeem=None, model=None):
            gezien["systeem"] = systeem
            n = prompt.count("\n[")
            return {"oordelen": [
                {"nr": i, "oordeel": "niet_neutraal" if "ondermijnt" in prompt.split(f"[{i}]")[1]
                 .split("\n[")[0] else "neutraal", "reden": "test",
                 "herformulering": "Denktank Voorbeeld leverde Omroep Voorbeeld duiding."}
                for i in range(1, n + 1)]}

        st.bc.vraag_model = nep_model
        gepost = []

        def nep_post(api_url, token, item, uitkomst):
            gepost.append(item["doel_id"])
            return via_client("POST", "/api/stemtoets", token, st.toets_body(item, uitkomst))

        st.post_toets = nep_post
        tel = st.draai(token_pad=st.DEFAULT_TOKEN, ids=[("argument", luid), ("argument", feit2)],
                       meld=stil)
        eis(tel["niet_neutraal"] == 1 and tel["neutraal"] == 1 and tel["geschreven"] == 2,
            f"de ronde schrijft één oordeel per tekst ({tel})")
        eis("eigen stem" in gezien["systeem"].lower() and "toegeschreven" in gezien["systeem"],
            "de opdracht aan het model noemt de regel: eigen stem neutraal, oordelen toegeschreven")
        c = lees()
        try:
            o = st.oordeel_voor(c, "argument", luid, rij("arguments", luid)["claim"], "assistent")
        finally:
            c.close()
        eis(o["verdict"] == "niet_neutraal" and o["herformulering"].startswith("Denktank"),
            "het oordeel staat in stem_toetsen, met de neutrale herformulering")

        print("6. Terugkoppelen: verworpen met de reden, de neutrale versie komt opnieuw binnen")
        tel = ab.stap_opruimen(tokens["merge-service"], ronde_args(), stil)
        verwerping = ab.laatste_verwerping(lees(), luid)
        eis(rij("arguments", luid)["status"] == "verworpen"
            and verwerping.startswith(ab.STEM_REDEN) and "Neutraal zou zijn" in verwerping,
            "het voorstel is verworpen met de reden van de stemtoets (ook vóór A1)")
        tel = ab.stap_neutrale_versies(ronde_args(), stil)
        c = lees()
        try:
            nieuw = c.execute("SELECT * FROM arguments WHERE reasoning LIKE ?",
                              (f"Neutrale versie van #{luid}%",)).fetchall()
            cit_oud = {r[0] for r in c.execute("SELECT source_id FROM citations WHERE argument_id = ?",
                                               (luid,))}
            cit_nieuw = {r[0] for r in c.execute("SELECT source_id FROM citations WHERE "
                                                 "argument_id = ?", (nieuw[0]["id"],))} if nieuw else set()
        finally:
            c.close()
        eis(len(nieuw) == 1 and nieuw[0]["claim"].startswith("Denktank Voorbeeld leverde")
            and nieuw[0]["relation_id"] == invloed and nieuw[0]["contributed_by"] == "bronzoeker"
            and cit_nieuw == cit_oud, "de neutrale versie: zelfde doel, zelfde bronnen")
        ab.stap_neutrale_versies(ronde_args(), stil)
        c = lees()
        try:
            n = c.execute("SELECT COUNT(*) FROM arguments WHERE reasoning LIKE ?",
                          (f"Neutrale versie van #{luid}%",)).fetchone()[0]
        finally:
            c.close()
        eis(n == 1, "één keer: geen tweede neutrale versie")
        a1(luid)
        s, j = api("post", f"/api/beoordeling/heropenen/{luid}", "merge-service")
        eis(s == 409 and any("stemtoets" in r for r in j["redenen"]),
            "een teruggekoppeld voorstel wordt niet heropend (de neutrale versie gaat verder)")

        print("7. Stemrevisie: gemerged werk krijgt de neutrale bewering, zelfde bronnen")
        stem("argument", claim, "niet_neutraal",
             herformulering="Denktank Voorbeeld leverde Omroep Voorbeeld in 2025 duiding.")
        tel = ab.stap_stemrevisies(tokens["merge-service"], ronde_args(), stil)
        c = lees()
        try:
            revisie = c.execute("SELECT * FROM arguments WHERE reviseert_id = ? AND status = "
                                "'voorgesteld'", (claim,)).fetchone()
        finally:
            c.close()
        eis(tel["ingediend"] == 1 and revisie is not None
            and revisie["claim"] == "Denktank Voorbeeld leverde Omroep Voorbeeld in 2025 duiding.",
            "een revisie met de herformulering van de stemtoets")
        c = lees()
        try:
            eis(server._stemrevisie(c, revisie), "de server herkent haar als stemrevisie")
        finally:
            c.close()
        a1(revisie["id"])
        s, j = merge(revisie["id"])
        eis(s == 409 and any("stemtoets" in r for r in j["redenen"]),
            "ook de revisie moet door de stemtoets")
        stem("argument", revisie["id"], "neutraal")
        s, j = merge(revisie["id"])
        eis(s == 200 and j["merged"] and rij("arguments", claim)["vervangen"] == 1,
            "A1 'klopt' + neutraal → gemerged zonder A2; het origineel is vervangen")
        tel = ab.stap_stemrevisies(tokens["merge-service"], ronde_args(), stil)
        eis(tel["kandidaten"] == 0, "één poging per argument")
        mens_arg = argument(invloed, "t-admin",
                            claim="Denktank Voorbeeld bedreigt de onafhankelijke journalistiek.")
        stem("argument", mens_arg, "niet_neutraal", herformulering="X.")
        tel = ab.stap_stemrevisies(tokens["merge-service"], ronde_args(droog=True), stil)
        eis(tel["kandidaten"] == 0, "werk van een mens herschrijft niemand automatisch")
        leeg_arg = argument(invloed, "assistent",
                            claim="Denktank Voorbeeld valt de pers aan en ondermijnt het vertrouwen.")
        a1(leeg_arg)
        a2(leeg_arg)
        stem("argument", leeg_arg, "neutraal")
        merge(leeg_arg)
        mens_status = argument(invloed, "assistent",
                               claim="Denktank Voorbeeld bedreigt de persvrijheid van de omroep.")
        a1(mens_status)
        a2(mens_status)
        stem("argument", mens_status, "neutraal")
        merge(mens_status)
        api("patch", f"/api/arguments/{mens_status}/status", "t-admin",
            {"status": "betwist", "motivatie": "mens: herkeuren"})
        stem("argument", leeg_arg, "niet_neutraal")
        stem("argument", mens_status, "niet_neutraal")
        tel = ab.stap_stemrevisies(tokens["merge-service"], ronde_args(), stil)
        eis(tel["verworpen"] == 1 and rij("arguments", leeg_arg)["status"] == "verworpen"
            and ab.laatste_verwerping(lees(), leeg_arg).startswith(ab.STEM_REDEN),
            "geen neutraal feit over (lege herformulering): geen bewijs, verworpen met de reden")
        eis(rij("arguments", mens_status)["status"] == "betwist",
            "maar niet als een mens over de status besliste")

        print("8. Beschrijvingen: seed- en agentwerk neutraal, nooit van een mens")
        eis(any(f"entiteit #{PVV}" in x for x in validation.check_eigen_stem(lees())[0]["voorbeelden"]),
            "NEUTRALITEIT-EIGEN-STEM wijst de seed-beschrijving van de PVV aan")
        stem("entiteit", PVV, "niet_neutraal",
             herformulering="Partij, opgericht in 2006. Wil de publieke omroep afschaffen.")
        s, j = api("get", f"/api/beoordeling/beschrijving/entities/{PVV}", "merge-service")
        eis(s == 200 and j["toegestaan"], "droogloop: mag")
        oud = rij("entities", PVV)["description"]
        tel = ab.stap_beschrijvingen(tokens["merge-service"], ronde_args(), stil)
        c = lees()
        try:
            log = c.execute("SELECT old_value, new_value, reason, changed_by FROM edit_log WHERE "
                            "table_name = 'entities' AND record_id = ? ORDER BY id DESC LIMIT 1",
                            (PVV,)).fetchone()
        finally:
            c.close()
        eis(rij("entities", PVV)["description"].startswith("Partij, opgericht in 2006")
            and json.loads(log["old_value"])["description"] == oud
            and log["reason"].startswith("automatische beoordeling: stemtoets")
            and log["changed_by"] == "merge-service",
            "herschreven; de oude tekst staat in edit_log (terug te zetten)")
        eis(not any(f"entiteit #{PVV}" in x
                    for x in validation.check_eigen_stem(lees())[0]["voorbeelden"]),
            "daarna wijst de check haar niet meer aan")
        for i in (2, 3):
            stem("entiteit", PVV, "niet_neutraal", herformulering=f"Partij (versie {i}).")
            ab.stap_beschrijvingen(tokens["merge-service"], ronde_args(), stil)
        eis(rij("entities", PVV)["description"] == "Partij (versie 2).",
            "hooguit twee keer automatisch herschreven (geen lus)")
        s, j = api("post", "/api/entities", "t-admin",
                   {"name": "Stichting Mens", "type": "stichting",
                    "description": "Rechts-populistische stichting."})
        mens_ent = j["id"]
        stem("entiteit", mens_ent, "niet_neutraal", herformulering="Stichting.")
        s, j = api("post", f"/api/beoordeling/beschrijving/entities/{mens_ent}", "merge-service")
        eis(s == 409 and any("mens" in r for r in j["redenen"])
            and rij("entities", mens_ent)["description"] == "Rechts-populistische stichting.",
            "de tekst van een mens blijft staan")
        s, _ = api("post", f"/api/beoordeling/beschrijving/entities/{VVD}", "nieuws-scout")
        eis(s == 403, "alleen reviewer-tier herschrijft")
        c = lees()
        try:
            luide_rel = c.execute("INSERT INTO relations (source_id, target_id, relation_type, "
                                  "mechanism_id, status, description) VALUES (?, ?, 'flak', ?, "
                                  "'goedgekeurd', 'Valt breed media aan, ondermijnt vertrouwen')",
                                  (PVV, medium, MECH)).lastrowid
            c.commit()
        finally:
            c.close()
        stem("relatie", luide_rel, "niet_neutraal")
        ab.stap_beschrijvingen(tokens["merge-service"], ronde_args(), stil)
        eis(rij("relations", luide_rel)["description"] is None,
            "geen neutraal feit over (lege herformulering): de beschrijving van seed-werk wordt "
            "gewist (de oude tekst staat in edit_log)")

        print("9. Verbanden zonder bron eindigen, na de bronzoeker en als niets meer loopt")
        c = lees()
        try:
            def kaal(src, tgt, rtype="bron_van"):
                rid = c.execute("INSERT INTO relations (source_id, target_id, relation_type, "
                                "mechanism_id, status) VALUES (?, ?, ?, ?, 'goedgekeurd')",
                                (src, tgt, rtype, MECH)).lastrowid
                return rid
            leeg = kaal(medium, denktank)
            loopt = kaal(denktank, partij)
            inhoud = kaal(partij, medium)
            weerlegd = c.execute("INSERT INTO arguments (relation_id, stance, claim, status, "
                                 "contributed_by) VALUES (?, 'supporting', 'Algemene stelling.', "
                                 "'betwist', 'legacy')", (inhoud,)).lastrowid
            c.execute("INSERT INTO edit_log (table_name, record_id, action, changed_by, reason) "
                      "VALUES ('arguments', ?, 'disputed', 't-admin', 'Weerlegd: klopt niet')",
                      (weerlegd,))
            c.execute("INSERT INTO nieuws_doelen (sleutel, naam, soort, relation_id, status, "
                      "aangemaakt, bijgewerkt) VALUES (?, 'x', 'relatie', ?, 'open', "
                      "'2026-10-08', '2026-10-08')", (f"relatie:{loopt}", loopt))
            c.commit()
        finally:
            c.close()
        nog_niet = ab.stap_zonder_bron(tokens["merge-service"], ronde_args(), stil)
        eis(rij("relations", leeg)["status"] == "goedgekeurd" and nog_niet["wacht_op_bronzoeker"] >= 1,
            "zonder poging van de bronzoeker: eerst zoeken (blijft staan)")
        bz.POGINGEN_PATH.write_text(json.dumps({
            f"relatie:{leeg}": {"op": "2026-10-08T10:00:00", "uitkomst": "niets"},
            f"relatie:{loopt}": {"op": "2026-10-08T10:00:00", "uitkomst": "niets"}}))
        s, j = api("get", f"/api/beoordeling/zonder_bron/{lid}", "merge-service")
        eis(not j["toegestaan"] and any("gedragen door" in r for r in j["redenen"]),
            "een verband met een argument dat het draagt, blijft")
        tel = ab.stap_zonder_bron(tokens["merge-service"], ronde_args(), stil)
        eis(rij("relations", leeg)["status"] == "afgewezen"
            and rij("relations", inhoud)["status"] == "afgewezen"
            and rij("arguments", weerlegd)["status"] == "verworpen",
            "afgewezen: na 'niets gevonden', of als het enige argument om de inhoud betwist is "
            "(met de argumenten mee)")
        eis(rij("relations", loopt)["status"] == "goedgekeurd",
            "een bewijsdoel uit het nieuws loopt nog: blijft")
        c = lees()
        try:
            reden = c.execute("SELECT reason FROM edit_log WHERE table_name = 'relations' AND "
                              "record_id = ? ORDER BY id DESC LIMIT 1", (leeg,)).fetchone()[0]
        finally:
            c.close()
        eis(reden.startswith("automatische beoordeling: zonder bron")
            and "eerste opzet" in reden, f"de reden staat in edit_log ({reden[:80]}…)")
        mens_rel = relatie(medium, partij, "bron_van")
        mens_arg2 = argument(mens_rel, "nieuws-scout")
        goedkeuren("relations", mens_rel)
        api("patch", f"/api/arguments/{mens_arg2}/status", "t-admin",
            {"status": "verworpen", "motivatie": "test"})
        bz.POGINGEN_PATH.write_text(json.dumps({
            f"relatie:{mens_rel}": {"op": "2026-10-08T10:00:00", "uitkomst": "niets"}}))
        s, j = api("get", f"/api/beoordeling/zonder_bron/{mens_rel}", "merge-service")
        eis(not j["toegestaan"] and any("mens" in r for r in j["redenen"]),
            "wat een mens goedkeurde, blijft staan")
        s, j = api("post", f"/api/relations/{leeg}/heraanmelden", "t-admin", {})
        eis(s == 200 and rij("relations", leeg)["status"] == "voorgesteld",
            "terug te draaien: een maintainer meldt ook seed-werk opnieuw aan")

        print("10. Verificatie na een nieuwer 'klopt-niet' (bronchecker v3)")
        auto = argument(invloed, "assistent", claim="Omroep Voorbeeld nodigde op 3 maart 2024 "
                                                    "een analist van Denktank Voorbeeld uit.")
        a1(auto)
        a2(auto)
        stem("argument", auto, "neutraal")
        s, j = merge(auto)
        assert s == 200, (s, j)
        api("post", f"/api/beoordeling/verificatie/{auto}", "merge-service")
        eis(rij("arguments", auto)["status"] == "geverifieerd", "automatisch geverifieerd")
        c = sqlite3.connect(db)
        c.execute("UPDATE edit_log SET created_at = '2026-10-01 10:00:00' WHERE table_name = "
                  "'arguments' AND record_id = ? AND action = 'verified'", (auto,))
        c.commit()
        c.close()
        a1(auto, "klopt-niet", herzien=True)
        ab.stap_verifieren(tokens["merge-service"], ronde_args(), stil)
        eis(rij("arguments", auto)["status"] == "bronvermelding_nodig",
            "een nieuwer 'klopt-niet' (gaat niet over dit verband) → bronvermelding_nodig")
        mens_v = argument(invloed, "assistent", claim="In het jaarverslag 2023 van Omroep "
                                                      "Voorbeeld staat Denktank Voorbeeld als partner.")
        a1(mens_v)
        a2(mens_v)
        stem("argument", mens_v, "neutraal")
        s, j = merge(mens_v)
        assert s == 200, (s, j)
        api("patch", f"/api/arguments/{mens_v}/status", "t-admin",
            {"status": "geverifieerd", "motivatie": "mens"})
        c = sqlite3.connect(db)
        c.execute("UPDATE edit_log SET created_at = '2026-10-01 10:00:00' WHERE table_name = "
                  "'arguments' AND record_id = ? AND action = 'verified'", (mens_v,))
        c.commit()
        c.close()
        a1(mens_v, "klopt-niet", herzien=True)
        ab.stap_verifieren(tokens["merge-service"], ronde_args(), stil)
        eis(rij("arguments", mens_v)["status"] == "geverifieerd",
            "wat een mens verifieerde, blijft staan")

        print("\nALLE STEMTOETS-TESTS GESLAAGD")


if __name__ == "__main__":
    main()
