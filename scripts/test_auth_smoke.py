#!/usr/bin/env python3
"""
Smoke-test identiteit & poorten (verbeterplan M0.6).

Draait met Flask test_client tegen een tijdelijke KOPIE van de live database:
anonieme schrijfacties (401), sessieflow via /api/login, Bearer-flow voor agents,
rolpoorten (403), genegeerde attributie-spoofing, zelf-merge-vlag en tokenrotatie.

Gebruik: python3 scripts/test_auth_smoke.py   (exit-code 0 = alles groen)
"""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth  # noqa: E402
import server  # noqa: E402

LIVE_DB = ROOT / "data" / "propaganda_model.db"


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def main():
    tmp = Path(tempfile.mkdtemp()) / "smoke.db"
    shutil.copy2(LIVE_DB, tmp)
    server.DB_PATH = tmp

    # Testgebruikers rechtstreeks in de kopie (CLI-pad wordt apart getest)
    conn = sqlite3.connect(tmp)
    agent_token = auth.new_token()
    maintainer_token = auth.new_token()
    conn.executemany(
        "INSERT INTO users (username, kind, role, password_hash, token_hash, provenance)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [("smoke-mens", "mens", "bijdrager", auth.hash_password("wachtwoord123"), None, None),
         ("smoke-agent", "agent", "bijdrager", None, auth.hash_token(agent_token), "claude-fable-5"),
         ("smoke-baas", "mens", "maintainer", auth.hash_password("wachtwoord456"),
          auth.hash_token(maintainer_token), None)])
    conn.commit()
    conn.close()

    print("1. Anoniem")
    c = server.app.test_client()
    r = c.post("/api/arguments", json={"relation_id": 1, "stance": "contextual", "claim": "x"})
    eis(r.status_code == 401, f"anonieme POST /api/arguments -> 401 ({r.status_code})")
    r = c.delete("/api/relations/1")
    eis(r.status_code == 401, f"anonieme DELETE -> 401 ({r.status_code})")
    r = c.get("/api/me")
    eis(r.status_code == 401, f"anonieme /api/me -> 401 ({r.status_code})")
    r = c.get("/api/arguments?relation_id=1")
    eis(r.status_code == 200, f"lezen blijft open ({r.status_code})")

    print("2. Sessieflow (mens)")
    r = c.post("/api/login", json={"username": "smoke-mens", "password": "fout"})
    eis(r.status_code == 401, f"fout wachtwoord -> 401 ({r.status_code})")
    r = c.post("/api/login", json={"username": "smoke-mens", "password": "wachtwoord123"})
    eis(r.status_code == 200, f"inloggen -> 200 ({r.status_code})")
    r = c.get("/api/me")
    eis(r.status_code == 200 and r.get_json()["username"] == "smoke-mens", "/api/me na login")
    r = c.post("/api/arguments", json={"relation_id": 1, "stance": "contextual",
                                       "claim": "Sessie-test", "contributed_by": "SPOOF"})
    a = r.get_json()
    eis(r.status_code == 201 and a["contributed_by"] == "smoke-mens",
        f"attributie volgt sessie, spoof genegeerd ({a.get('contributed_by')})")
    arg_mens = a["id"]

    print("3. Rolpoorten")
    r = c.patch(f"/api/arguments/{arg_mens}/status", json={"status": "geverifieerd"})
    eis(r.status_code == 403, f"bijdrager mag status niet zetten -> 403 ({r.status_code})")
    r = c.post("/api/roles", json={"name": "x", "category": "overig", "description": "x"})
    eis(r.status_code == 403, f"bijdrager mag theorielaag niet schrijven -> 403 ({r.status_code})")
    r = c.delete("/api/relations/1")
    eis(r.status_code == 403, f"bijdrager mag niet verwijderen -> 403 ({r.status_code})")
    r = c.post("/api/logout")
    eis(r.status_code == 200, "uitloggen")
    r = c.post("/api/arguments", json={"relation_id": 1, "stance": "contextual", "claim": "x"})
    eis(r.status_code == 401, f"na uitloggen weer 401 ({r.status_code})")

    print("4. Bearer-flow (agent)")
    kop = {"Authorization": f"Bearer {agent_token}"}
    r = c.post("/api/arguments", headers=kop,
               json={"relation_id": 1, "stance": "supporting", "claim": "Agent-test zonder bron"})
    a = r.get_json()
    eis(r.status_code == 201 and a["contributed_by"] == "smoke-agent",
        "agent-POST geattribueerd aan agent-account")
    eis(a["status"] == "bronvermelding_nodig", "citatiepoort geldt ook voor agents")
    r = c.post("/api/arguments", headers={"Authorization": "Bearer pm_ongeldig"},
               json={"relation_id": 1, "stance": "contextual", "claim": "x"})
    eis(r.status_code == 401, f"ongeldig token -> 401 ({r.status_code})")

    print("5. Maintainer + zelf-merge")
    kop = {"Authorization": f"Bearer {maintainer_token}"}
    r = c.post("/api/arguments", headers=kop,
               json={"relation_id": 1, "stance": "contextual", "claim": "Eigen claim"})
    eigen_arg = r.get_json()["id"]
    r = c.patch(f"/api/arguments/{eigen_arg}/status", headers=kop,
                json={"status": "geverifieerd"})
    j = r.get_json()
    eis(r.status_code == 200 and j["self_merged"] is True,
        "eigen argument verifiëren zet de self_merged-vlag")
    r = c.patch(f"/api/arguments/{arg_mens}/status", headers=kop,
                json={"status": "geverifieerd"})
    j = r.get_json()
    eis(r.status_code == 200 and j["self_merged"] is False,
        "andermans argument verifiëren: geen vlag")
    r = c.patch(f"/api/arguments/{eigen_arg}/status", headers=kop,
                json={"status": "verworpen"})
    eis(r.status_code == 200, "status 'verworpen' wordt geaccepteerd")

    print("6. Tokenrotatie")
    r = c.post("/api/tokens", headers=kop)
    nieuw = r.get_json()["token"]
    eis(r.status_code == 201 and nieuw.startswith("pm_"), "nieuw token gegenereerd")
    r = c.get("/api/me", headers=kop)
    eis(r.status_code == 401, "oud token is ongeldig na rotatie")
    r = c.get("/api/me", headers={"Authorization": f"Bearer {nieuw}"})
    eis(r.status_code == 200, "nieuw token werkt")

    print("Smoke-test auth: alles groen.")


if __name__ == "__main__":
    main()
