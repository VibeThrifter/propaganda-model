#!/usr/bin/env python3
"""
Verse-buildtest (verbeterplan M0.2): bewijst dat een schone build werkt.

Bouwt het model from scratch in een tijdelijke map (schema.sql → theorie-seed →
instantie-seed, exact de volgorde uit CLAUDE.md) en draait daarna alle
schrijf-endpoints van server.py tegen die verse database via Flask test_client.
De live database wordt niet aangeraakt.

Gebruik: python3 scripts/test_fresh_build.py
Exit-code 0 = alles groen.
"""
import importlib.util
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
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "vers.db"

        print("1. Verse build (schema → theorie → instanties)")
        for naam, functie in (("init_db", "init_db"),
                              ("seed_theoretical_model", "seed"),
                              ("seed_from_ai_source", "seed")):
            module = laad_script(naam)
            module.DB_PATH = db
            getattr(module, functie)()

        conn = sqlite3.connect(db)
        rollen, mechanismen, entiteiten, relaties = (
            conn.execute("SELECT (SELECT COUNT(*) FROM roles), (SELECT COUNT(*) FROM mechanisms),"
                         " (SELECT COUNT(*) FROM entities), (SELECT COUNT(*) FROM relations)").fetchone())
        conn.close()
        eis(rollen and mechanismen and entiteiten and relaties,
            f"verse DB gevuld ({rollen} rollen, {mechanismen} mechanismen, "
            f"{entiteiten} entiteiten, {relaties} relaties)")

        print("2. Schrijf-endpoints op de verse DB (maintainer + 2 reviewers, via Bearer)")
        import auth
        import server
        server.DB_PATH = db
        server._rate_emmers.clear()

        tokens = {}
        conn = sqlite3.connect(db)
        for naam, rol in (("verse-buildtest", "maintainer"),
                          ("verse-reviewer-1", "reviewer"), ("verse-reviewer-2", "reviewer")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT INTO users (username, kind, role, token_hash)"
                         " VALUES (?, 'mens', ?, ?)", (naam, rol, auth.hash_token(tokens[naam])))
        conn.commit()
        conn.close()
        kop = {"Authorization": f"Bearer {tokens['verse-buildtest']}"}
        kop_r1 = {"Authorization": f"Bearer {tokens['verse-reviewer-1']}"}
        kop_r2 = {"Authorization": f"Bearer {tokens['verse-reviewer-2']}"}
        client = server.app.test_client()

        r = client.post("/api/entities", json={"name": "Verse-build Testentiteit",
                                               "type": "bedrijf", "active_from": "2020"})
        eis(r.status_code == 401, f"zonder token weigert de poort ({r.status_code})")

        r = client.post("/api/entities", headers=kop, json={
            "name": "Verse-build Testentiteit", "type": "bedrijf", "active_from": "2020"})
        eis(r.status_code == 201, f"POST /api/entities ({r.status_code}: {r.get_json()})")
        ent_a = r.get_json()["id"]

        r = client.post("/api/entities", headers=kop, json={
            "name": "Verse-build Testmedium", "type": "mediaorganisatie"})
        eis(r.status_code == 201, f"POST /api/entities 2e ({r.status_code})")
        ent_b = r.get_json()["id"]

        # Theorielaag: niet-maintainers kunnen niet direct creëren (alleen via RfC) ...
        r = client.post("/api/roles", headers=kop_r1, json={
            "name": "x_directe_rol", "category": "tegenmacht", "description": "x"})
        eis(r.status_code == 403,
            f"directe POST /api/roles dicht voor niet-maintainers ({r.status_code})")
        # ... maar een maintainer mag in de opbouwfase wél direct (gevlagd); ruim 'm op.
        r = client.post("/api/roles", headers=kop, json={
            "naam": "verse_directe_rol", "categorie": "tegenmacht", "definitie": "Direct."})
        eis(r.status_code == 201 and r.get_json().get("direct_toegevoegd"),
            f"maintainer mag een rol direct toevoegen ({r.status_code})")
        client.delete(f"/api/roles/{r.get_json()['id']}", headers=kop)

        def rfc(titel, payload):
            r = client.post("/api/voorstellen", headers=kop, json={
                "soort": "nieuw_theorie_element", "titel": titel, "payload": payload})
            eis(r.status_code == 201, f"RfC '{titel}' ingediend ({r.status_code}: {r.get_json()})")
            vid = r.get_json()["id"]
            client.post(f"/api/voorstellen/{vid}/reviews", headers=kop_r1,
                        json={"oordeel": "akkoord"})
            r = client.post(f"/api/voorstellen/{vid}/reviews", headers=kop_r2,
                            json={"oordeel": "akkoord"})
            j = r.get_json()
            eis(j.get("besluit") == "geaccepteerd",
                f"RfC '{titel}' geaccepteerd na 2 menselijke akkoorden ({j.get('besluit')})")
            return j["resultaat"]["id"]

        rol_id = rfc("Rol: verse_build_testrol", {
            "element_type": "rol", "naam": "verse_build_testrol", "categorie": "tegenmacht",
            "definitie": "Testrol voor de verse-buildtest.",
            "afgrenzing": "Bestaat alleen in deze test.",
            "falsificatiecriterium": "De test faalt.",
            "instantiaties": ["Verse-build Testentiteit"], "bronnen": ["testbron"]})
        mech_id = rfc("Mechanisme: verse_build_testmechanisme", {
            "element_type": "mechanisme", "naam": "verse_build_testmechanisme",
            "filter": "tegenmacht", "definitie": "Testmechanisme.", "effect": "Geen.",
            "aard": "direct", "freeze_test": "n.v.t. (direct kanaal)",
            "afgrenzing": "Bestaat alleen in deze test.",
            "falsificatiecriterium": "De test faalt.",
            "instantiaties": ["testrelatie"], "bronnen": ["testbron"],
            "source_role_id": rol_id, "target_role_id": rol_id})

        r = client.post("/api/relations", headers=kop, json={
            "source_id": ent_a, "target_id": ent_b, "relation_type": "financiering",
            "mechanism_id": mech_id, "certainty": 0.8, "influence": 0.4,
            "active_from": "2021"})
        eis(r.status_code == 201, f"POST /api/relations ({r.status_code}: {r.get_json()})")
        rel_id = r.get_json()["id"]

        # De relatie materialiseert haar mechanisme-instantiatie zelf al (create_relation),
        # dus een expliciete POST van hetzelfde paar is nu idempotent: 200 + hergebruikt.
        r = client.post("/api/instantiations", headers=kop, json={
            "mechanism_id": mech_id, "relation_id": rel_id, "exemplarity": 0.9})
        eis(r.status_code in (200, 201), f"POST /api/instantiations mech↔relatie ({r.status_code})")
        eis(r.get_json().get("hergebruikt") is True or r.status_code == 201,
            "instantiatie mech↔relatie bestaat al (auto-gematerialiseerd) of nieuw aangemaakt")
        r = client.post("/api/instantiations", headers=kop, json={
            "role_id": rol_id, "entity_id": ent_a})
        eis(r.status_code == 201, f"POST /api/instantiations rol↔entiteit ({r.status_code})")
        inst_id = r.get_json()["id"]

        # Harde citatiepoort (sinds 6af4f97): een supporting/contradicting root
        # zónder echte citatie komt er bij creatie al niet meer in.
        r = client.post("/api/arguments", headers=kop, json={
            "relation_id": rel_id, "stance": "supporting",
            "claim": "Testclaim zonder bron."})
        eis(r.status_code == 400,
            f"POST /api/arguments zonder citatie botst op de bronplicht ({r.status_code})")

        # Admin hoeft geen review (juli 2026): een maintainer-argument merget meteen.
        bron_id = sqlite3.connect(db).execute("SELECT MIN(id) FROM sources").fetchone()[0]
        r = client.post("/api/arguments", headers=kop, json={
            "relation_id": rel_id, "stance": "supporting",
            "claim": "Admin-testclaim voor de verse build.",
            "citations": [{"source_id": bron_id, "quote": "Testcitaat."}]})
        a = r.get_json()
        eis(r.status_code == 201 and a["status"] == "ongecontroleerd" and a["self_merged"],
            f"maintainer-argument merget meteen (auto-merge, self_merged) ({a.get('status')})")

        # Niet-maintainers volgen de gewone voorstel-workflow (M2.2).
        r = client.post("/api/arguments", headers=kop_r1, json={
            "relation_id": rel_id, "stance": "supporting",
            "claim": "Onafhankelijke tweede bevestiging uit het handelsregister.",
            "citations": [{"source_id": bron_id, "quote": "Testcitaat 2."}]})
        a = r.get_json()
        eis(r.status_code == 201 and a["status"] == "voorgesteld",
            f"POST /api/arguments (mét citatie) landt als voorstel (M2.2) ({a.get('status')})")
        arg_id = a["id"]

        r = client.post(f"/api/arguments/{arg_id}/merge", headers=kop_r2)
        eis(r.status_code == 200 and r.get_json()["status"] == "ongecontroleerd",
            f"merge van een gesourcete root → ongecontroleerd ({r.get_json().get('status')})")

        # De mergetijd-citatiepoort blijft de vangrail voor legacy on-gesourcete roots;
        # zo'n rij kan alleen nog als DB-fixture bestaan (de API weigert 'm hierboven).
        conn = sqlite3.connect(db)
        legacy_id = conn.execute(
            "INSERT INTO arguments (relation_id, stance, claim, status, contributed_by)"
            " VALUES (?, 'supporting', 'Legacy-claim zonder bron.', 'voorgesteld', ?)",
            (rel_id, "verse-buildtest")).lastrowid
        conn.commit()
        conn.close()
        r = client.post(f"/api/arguments/{legacy_id}/merge", headers=kop_r1)
        eis(r.status_code == 200 and r.get_json()["status"] == "bronvermelding_nodig",
            f"merge past de citatiepoort toe op een legacy-root ({r.get_json().get('status')})")

        r = client.post("/api/citations", headers=kop, json={
            "argument_id": legacy_id, "source_id": bron_id, "quote": "Testcitaat."})
        eis(r.status_code == 201 and r.get_json()["argument_status"] == "ongecontroleerd",
            f"POST /api/citations promoveert het argument ({r.status_code})")

        r = client.patch(f"/api/arguments/{legacy_id}/status", headers=kop_r1,
                         json={"status": "geverifieerd"})
        eis(r.status_code == 200, f"PATCH status door niet-auteur ({r.status_code})")

        r = client.get("/api/scores")
        eis(r.status_code == 200, f"GET /api/scores ({r.status_code})")
        r = client.get("/api/health")
        eis(r.status_code == 200, f"GET /api/health ({r.status_code})")
        r = client.get("/api/review_queue", headers=kop_r1)
        eis(r.status_code == 200, f"GET /api/review_queue (reviewer) ({r.status_code})")
        r = client.get("/")
        eis(r.status_code == 200 and b'id="appScript"' in r.data and b'"%%DATA%%"' in r.data,
            f"GET / serveert de dunne pagina (template + boot-loader, W5.1) ({r.status_code})")
        r = client.get("/api/graph_data")
        j = r.get_json()
        eis(r.status_code == 200 and j.get("entities") and j.get("relations"),
            f"GET /api/graph_data levert de graafdata ({r.status_code})")
        r = client.get(f"/api/arguments/{arg_id}/score_diff?status=verworpen")
        eis(r.status_code == 200, f"GET score_diff ({r.status_code})")

        r = client.delete(f"/api/instantiations/{inst_id}", headers=kop)
        eis(r.status_code == 200, f"DELETE /api/instantiations ({r.status_code})")
        r = client.delete(f"/api/relations/{rel_id}", headers=kop)
        eis(r.status_code == 200, f"DELETE /api/relations ({r.status_code})")
        r = client.delete(f"/api/entities/{ent_a}", headers=kop)
        eis(r.status_code == 200, f"DELETE /api/entities ({r.status_code})")
        r = client.delete(f"/api/mechanisms/{mech_id}", headers=kop)
        eis(r.status_code == 200, f"DELETE /api/mechanisms ({r.status_code})")
        r = client.delete(f"/api/roles/{rol_id}", headers=kop)
        eis(r.status_code == 200, f"DELETE /api/roles ({r.status_code})")

        print("Verse build: alles groen.")


if __name__ == "__main__":
    main()
