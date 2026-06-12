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

        print("2. Schrijf-endpoints op de verse DB (als maintainer, via Bearer-token)")
        import auth
        import server
        server.DB_PATH = db

        token = auth.new_token()
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO users (username, kind, role, token_hash)"
                     " VALUES ('verse-buildtest', 'mens', 'maintainer', ?)",
                     (auth.hash_token(token),))
        conn.commit()
        conn.close()
        kop = {"Authorization": f"Bearer {token}"}
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

        r = client.post("/api/roles", headers=kop, json={
            "name": "verse_build_testrol", "category": "tegenmacht",
            "description": "Testrol voor de verse-buildtest."})
        eis(r.status_code == 201, f"POST /api/roles incl. categorie 'tegenmacht' ({r.status_code})")
        rol_id = r.get_json()["id"]

        r = client.post("/api/mechanisms", headers=kop, json={
            "name": "verse_build_testmechanisme", "filter": "tegenmacht",
            "description": "Testmechanisme.", "effect": "Geen.",
            "source_role_id": rol_id, "target_role_id": rol_id})
        eis(r.status_code == 201, f"POST /api/mechanisms incl. filter 'tegenmacht' ({r.status_code})")
        mech_id = r.get_json()["id"]

        r = client.post("/api/relations", headers=kop, json={
            "source_id": ent_a, "target_id": ent_b, "relation_type": "financiering",
            "mechanism_id": mech_id, "certainty": 0.8, "influence": 0.4,
            "active_from": "2021"})
        eis(r.status_code == 201, f"POST /api/relations ({r.status_code}: {r.get_json()})")
        rel_id = r.get_json()["id"]

        r = client.post("/api/instantiations", headers=kop, json={
            "mechanism_id": mech_id, "relation_id": rel_id, "exemplarity": 0.9})
        eis(r.status_code == 201, f"POST /api/instantiations mech↔relatie ({r.status_code})")
        r = client.post("/api/instantiations", headers=kop, json={
            "role_id": rol_id, "entity_id": ent_a})
        eis(r.status_code == 201, f"POST /api/instantiations rol↔entiteit ({r.status_code})")
        inst_id = r.get_json()["id"]

        r = client.post("/api/arguments", headers=kop, json={
            "relation_id": rel_id, "stance": "supporting",
            "claim": "Testclaim voor de verse build."})
        a = r.get_json()
        eis(r.status_code == 201 and a["status"] == "bronvermelding_nodig",
            f"POST /api/arguments; citatiepoort actief ({a.get('status')})")
        arg_id = a["id"]

        bron_id = sqlite3.connect(db).execute("SELECT MIN(id) FROM sources").fetchone()[0]
        r = client.post("/api/citations", headers=kop, json={
            "argument_id": arg_id, "source_id": bron_id, "quote": "Testcitaat."})
        eis(r.status_code == 201 and r.get_json()["argument_status"] == "ongecontroleerd",
            f"POST /api/citations promoveert het argument ({r.status_code})")

        r = client.patch(f"/api/arguments/{arg_id}/status", headers=kop,
                         json={"status": "geverifieerd"})
        eis(r.status_code == 200, f"PATCH /api/arguments/{arg_id}/status ({r.status_code})")

        r = client.get("/api/scores")
        eis(r.status_code == 200, f"GET /api/scores ({r.status_code})")
        r = client.get("/api/health")
        eis(r.status_code == 200, f"GET /api/health ({r.status_code})")

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
