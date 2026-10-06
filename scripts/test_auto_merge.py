#!/usr/bin/env python3
"""
End-to-end-test van de auto-merge-poort (A7): het immuunpoort-predikaat
``auto_merge_toegestaan`` + het endpoint ``POST /api/arguments/<id>/auto_merge``
+ de kill-switch (env PROPAGANDA_AUTO_MERGE).

Bouwt een verse database in een tijdelijke map (schema → theorie → instanties),
zet ``immuun_oordelen``-rijen op met directe SQL (test-scaffolding — geen inhoud),
en toetst álle predikaat-takken. De live database wordt NOOIT aangeraakt.

Gebruik: python3 scripts/test_auto_merge.py
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
    # Kill-switch standaard aan tijdens de test (kan door de omgeving anders staan).
    os.environ["PROPAGANDA_AUTO_MERGE"] = "1"

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
        server._rate_emmers.clear()

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row

        # Accounts: auteur (bijdrager), twee gedecorreleerde verifiers, het reviewer-tier
        # systeemaccount 'merge-service' en een maintainer voor de opzet.
        tokens = {}
        for naam, rol, prov in (("t-auteur", "bijdrager", "claude-opus"),
                                ("t-verif", "bijdrager", "gpt-5.1"),
                                ("t-aanklager", "bijdrager", "gemini-3-pro"),
                                ("merge-service", "reviewer", "harness-auto-merge"),
                                ("t-admin", "maintainer", "mens")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT INTO users (username, kind, role, provenance, token_hash)"
                         " VALUES (?, 'agent', ?, ?, ?)",
                         (naam, rol, prov, auth.hash_token(tokens[naam])))
        conn.commit()

        # Doelen: een media-org, een gewone org, een natuurlijk persoon + één relatie.
        def ent(name, typ):
            cur = conn.execute("INSERT INTO entities (name, type, status) "
                               "VALUES (?, ?, 'goedgekeurd')", (name, typ))
            return cur.lastrowid
        ent_media = ent("Test Media BV", "mediaorganisatie")
        ent_org = ent("Test Belang NV", "bedrijf")
        ent_persoon = ent("Test Persoon", "persoon")
        rel = conn.execute("""INSERT INTO relations (source_id, target_id, relation_type,
                              certainty, influence, status)
                              VALUES (?, ?, 'financiering', 0.8, 0.4, 'voorgesteld')""",
                           (ent_org, ent_media)).lastrowid
        bron = conn.execute("SELECT MIN(id) FROM sources").fetchone()[0]
        rol_id = conn.execute("SELECT MIN(id) FROM roles").fetchone()[0]
        conn.commit()

        def mk_arg(stance="supporting", *, relation_id=None, entity_id=None, role_id=None,
                   parent=None, prop=None, prop_value=None, met_citaat=True,
                   auteur="t-auteur", bezwaar=None):
            cur = conn.execute("""
                INSERT INTO arguments (relation_id, entity_id, role_id, parent_argument_id,
                    property, property_value, stance, claim, status, contributed_by,
                    bezwaar_resolutie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'voorgesteld', ?, ?)""",
                (relation_id, entity_id, role_id, parent, prop, prop_value, stance,
                 "Testclaim voor de auto-merge-poort.", auteur, bezwaar))
            aid = cur.lastrowid
            if met_citaat:
                conn.execute("INSERT INTO citations (argument_id, source_id, quote) "
                             "VALUES (?, ?, ?)", (aid, bron, "Verbatim testcitaat."))
            conn.commit()
            return aid

        def immuun(aid, fase, verdict, door):
            prov = conn.execute("SELECT provenance FROM users WHERE username = ?",
                                (door,)).fetchone()[0]
            conn.execute("""INSERT INTO immuun_oordelen (argument_id, fase, verdict, door,
                            model_familie) VALUES (?, ?, ?, ?, ?)""",
                         (aid, fase, verdict, door, prov))
            conn.commit()

        def merge_reply_ondergraving(root_id, bezwaar="open"):
            """Een GEMERGEDE contradicting reply (ondergraving) onder een root."""
            cur = conn.execute("""
                INSERT INTO arguments (parent_argument_id, stance, claim, status,
                    contributed_by, bezwaar_resolutie)
                VALUES (?, 'contradicting', 'De inferentie klopt niet.', 'ongecontroleerd',
                        't-aanklager', ?)""", (root_id, bezwaar))
            conn.commit()
            return cur.lastrowid

        print("2. Predikaat-takken (auto_merge_toegestaan)")

        def check(aid, verwacht_ok, verwacht_bucket, label):
            ok, redenen, bucket = server.auto_merge_toegestaan(conn, aid)
            eis(ok == verwacht_ok and bucket == verwacht_bucket,
                f"{label}: ok={ok} bucket={bucket!r} redenen={redenen}")

        # a) Ontbrekende citatie → geparkeerd-twijfel.
        a = mk_arg("supporting", relation_id=rel, met_citaat=False)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, False, "geparkeerd-twijfel", "ontbrekende citatie")

        # b) A1 'twijfel' → geparkeerd-twijfel.
        a = mk_arg("supporting", relation_id=rel)
        immuun(a, "herverificatie", "twijfel", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, False, "geparkeerd-twijfel", "A1 twijfel")

        # c) A1 'klopt-niet' → geparkeerd-twijfel.
        a = mk_arg("supporting", relation_id=rel)
        immuun(a, "herverificatie", "klopt-niet", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, False, "geparkeerd-twijfel", "A1 klopt-niet")

        # d) Openstaande ondergraving → geparkeerd-twijfel.
        a = mk_arg("supporting", relation_id=rel)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        merge_reply_ondergraving(a, bezwaar="open")
        check(a, False, "geparkeerd-twijfel", "openstaande ondergraving")

        def smaad(aid, verdict, door="t-verif"):
            conn.execute("INSERT INTO smaad_toetsen (argument_id, verdict, reden, door) "
                         "VALUES (?, ?, 'test', ?)", (aid, verdict, door))
            conn.commit()

        # e) Persoonsclaim (eigenaarsbesluit 2026-10-06: de smaad-firewall door een agent):
        #    zonder smaadtoets geparkeerd, 'niet_feitelijk' geblokkeerd, 'feitelijk' + A1 + A2
        #    → auto-gemerged. Ongeacht stance.
        a = mk_arg("contradicting", entity_id=ent_persoon)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, False, "geparkeerd-twijfel", "persoonsclaim (entiteit) zonder smaadtoets")
        smaad(a, "niet_feitelijk")
        check(a, False, "geblokkeerd-hoog-inzet", "persoonsclaim die niet feitelijk is")

        # e2) Een SUPPORTING persoonsclaim die de smaadtoets doorstaat → auto-gemerged.
        a = mk_arg("supporting", entity_id=ent_persoon)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        smaad(a, "feitelijk")
        check(a, True, "auto-gemerged", "feitelijke persoonsclaim met A1 + A2")
        b = mk_arg("supporting", entity_id=ent_persoon, auteur="t-verif")
        immuun(b, "herverificatie", "klopt", "t-aanklager")
        immuun(b, "tegenspraak", "overleefd", "t-auteur")
        smaad(b, "feitelijk", door="t-verif")
        check(b, False, "geparkeerd-twijfel", "smaadtoets van de auteur zelf telt niet")

        # e3) Claim op een persoon↔org-RELATIE → ook via de smaadtoets.
        rel_persoon = conn.execute("""INSERT INTO relations (source_id, target_id,
                              relation_type, certainty, influence, status)
                              VALUES (?, ?, 'dienstverband', 0.8, 0.4, 'voorgesteld')""",
                           (ent_persoon, ent_org)).lastrowid
        conn.commit()
        a = mk_arg("contradicting", relation_id=rel_persoon)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, False, "geparkeerd-twijfel", "claim op persoon↔org-relatie zonder smaadtoets")
        smaad(a, "feitelijk")
        check(a, True, "auto-gemerged", "claim op persoon↔org-relatie, feitelijk bevonden")

        # e4) Org↔org-RELATIE (geen persoon betrokken) → geen smaadtoets nodig.
        #     ent_org → ent_media is org↔org/org↔media; met schone signalen auto-mergebaar.
        a = mk_arg("supporting", relation_id=rel)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, True, "auto-gemerged", "org↔org/org↔media-claim (geen persoon)")

        # f) Theorie-doel, aspect en reactie (agents doen alles, 2026-10-06): dezelfde eisen
        #    als een invloedsclaim — zonder signalen geparkeerd, met A1 + A2 gemerged.
        a = mk_arg("supporting", role_id=rol_id)
        check(a, False, "geparkeerd-twijfel", "theorie-doel (rol) zonder A1/A2")
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, True, "auto-gemerged", "theorie-doel (rol) met A1 + A2")

        # f2) Aspect-root (property='filter').
        a = mk_arg("supporting", relation_id=rel, prop="filter", prop_value="eigendom")
        check(a, False, "geparkeerd-twijfel", "aspect-root (filter) zonder A1/A2")
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, True, "auto-gemerged", "aspect-root (filter) met A1 + A2")

        # f3) Steunende reactie (parent gezet).
        root_voor_reply = mk_arg("supporting", relation_id=rel)
        a = conn.execute("""INSERT INTO arguments (parent_argument_id, stance, claim, status,
                            contributed_by) VALUES (?, 'supporting', 'Steun.', 'voorgesteld',
                            't-auteur')""", (root_voor_reply,)).lastrowid
        conn.execute("INSERT INTO citations (argument_id, source_id, quote) VALUES (?, ?, ?)",
                     (a, bron, "Verbatim testcitaat."))
        conn.commit()
        check(a, False, "geparkeerd-twijfel", "steunende reactie zonder A1/A2")
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-aanklager")
        check(a, True, "auto-gemerged", "steunende reactie met A1 + A2")

        # g) A1 én A2 door hetzelfde account → faalt op jury-onafhankelijkheid.
        a = mk_arg("supporting", relation_id=rel)
        immuun(a, "herverificatie", "klopt", "t-verif")
        immuun(a, "tegenspraak", "overleefd", "t-verif")
        ok, redenen, bucket = server.auto_merge_toegestaan(conn, a)
        eis(not ok and bucket == "geparkeerd-twijfel"
            and any("onafhankelijk" in r for r in redenen),
            f"jury-onafhankelijkheid: redenen={redenen}")

        # h) Álle signalen goed → auto-gemerged (predikaat).
        goed = mk_arg("supporting", relation_id=rel)
        immuun(goed, "herverificatie", "klopt", "t-verif")
        immuun(goed, "tegenspraak", "overleefd", "t-aanklager")
        check(goed, True, "auto-gemerged", "alle signalen goed")

        conn.close()

        print("3. Endpoint POST /api/arguments/<id>/auto_merge")
        client = server.app.test_client()
        svc = {"Authorization": f"Bearer {tokens['merge-service']}"}
        auteur_kop = {"Authorization": f"Bearer {tokens['t-auteur']}"}

        # Auteur (bijdrager) mag niet auto-mergen (reviewer+).
        r = client.post(f"/api/arguments/{goed}/auto_merge", headers=auteur_kop)
        eis(r.status_code == 403, f"bijdrager mag niet auto-mergen ({r.status_code})")

        # merge-service (reviewer) merget het schone argument → 200.
        r = client.post(f"/api/arguments/{goed}/auto_merge", headers=svc)
        j = r.get_json()
        eis(r.status_code == 200 and j["merged"] and j["bucket"] == "auto-gemerged",
            f"auto-merge van het schone argument ({r.status_code}: {j})")

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status, merged_by, self_merged FROM arguments WHERE id = ?",
                           (goed,)).fetchone()
        eis(row["status"] == "ongecontroleerd" and row["merged_by"] == "merge-service"
            and not row["self_merged"],
            f"gemerged onder merge-service, geen self_merge ({dict(row)})")
        elog = conn.execute("""SELECT reason FROM edit_log WHERE table_name = 'arguments'
                               AND record_id = ? AND action = 'merged'""", (goed,)).fetchone()
        eis(elog and elog["reason"] == "auto-merge (immuunpoort)",
            f"edit_log-reden = auto-merge (immuunpoort) ({elog['reason'] if elog else None})")

        # Tweede poging op hetzelfde (nu niet meer 'voorgesteld') → 409 mensenwerk.
        r = client.post(f"/api/arguments/{goed}/auto_merge", headers=svc)
        eis(r.status_code == 409 and r.get_json()["bucket"] == "mensenwerk",
            f"al gemerged → 409 mensenwerk ({r.status_code})")

        # Een geparkeerd item (A1 twijfel) → 409 met redenen, blijft 'voorgesteld'.
        park = conn.execute("SELECT id FROM arguments WHERE contributed_by = 't-auteur' "
                            "AND status = 'voorgesteld' AND relation_id = ? LIMIT 1",
                            (rel,)).fetchone()[0]
        conn.close()
        r = client.post(f"/api/arguments/{park}/auto_merge", headers=svc)
        eis(r.status_code == 409 and not r.get_json()["merged"] and r.get_json()["redenen"],
            f"geparkeerd item → 409 + redenen ({r.status_code})")

        print("4. Kill-switch PROPAGANDA_AUTO_MERGE=0 → 503")
        os.environ["PROPAGANDA_AUTO_MERGE"] = "0"
        # Nieuw schoon argument dat zónder kill-switch zou mergen.
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        server.DB_PATH = db
        a2id = conn.execute("""INSERT INTO arguments (relation_id, stance, claim, status,
                              contributed_by) VALUES (?, 'supporting', 'Nog een claim.',
                              'voorgesteld', 't-auteur')""", (rel,)).lastrowid
        conn.execute("INSERT INTO citations (argument_id, source_id, quote) VALUES (?, ?, ?)",
                     (a2id, bron, "Citaat."))
        for fase, verdict, door, prov in (("herverificatie", "klopt", "t-verif", "gpt-5.1"),
                                          ("tegenspraak", "overleefd", "t-aanklager", "gemini-3-pro")):
            conn.execute("""INSERT INTO immuun_oordelen (argument_id, fase, verdict, door,
                            model_familie) VALUES (?, ?, ?, ?, ?)""",
                         (a2id, fase, verdict, door, prov))
        conn.commit()
        conn.close()
        r = client.post(f"/api/arguments/{a2id}/auto_merge", headers=svc)
        eis(r.status_code == 503 and "uitgeschakeld" in r.get_json().get("error", ""),
            f"kill-switch dicht → 503 ({r.status_code})")
        os.environ["PROPAGANDA_AUTO_MERGE"] = "1"

        print("\nALLE AUTO-MERGE-TESTS GESLAAGD")


if __name__ == "__main__":
    main()
