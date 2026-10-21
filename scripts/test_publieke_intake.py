#!/usr/bin/env python3
"""
End-to-end test publieke intake (Fase 5, D2-kern + D2.0 + D2.1 + D2.3 + D2.4).

Draait met de Flask test_client tegen een tijdelijke KOPIE van de live database.
Bewijst de kernbelofte: een publieke inzending is een TIP/LEAD, geen claim — ze landt
in de aparte leads-baan, telt in NIETS mee, rendert nooit publiek, en de smaad-firewall
houdt negatieve persoonsclaims uit de publieke render tot de eigenaar ze vrijgeeft.

Scenario's:
  1. Welgevormde POST /api/leads → 201, rij in leads, 0 in arguments.
  2. XSS in claim/quote → ge-escaped opgeslagen (inert).
  3. Laag 0: honeypot / te snel / blocklist → gedropt/geweigerd; 50 posts/één IP → meeste 429.
  4. Sock-puppet-collapse: 50 identieke leads → 1 binnengekomen + 49 duplicaat.
  5. "Telt in niets": scoring/influence-snapshot byte-identiek met/zonder 100 leads.
  6. Smaad-firewall: negatieve persoonsclaim → smaad_hold=1, niet in graph_data; org-claim
     → geen smaad_hold; agent-poging tot opheffen → 403; opgeheven → zichtbaar.
  7. Anomalie-check (D2.4): burst over één betreft → 'waarschuwing'.

Gebruik: python3 scripts/test_publieke_intake.py   (exit-code 0 = alles groen)
"""
import json
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth        # noqa: E402
import server      # noqa: E402
import scoring     # noqa: E402
import influence   # noqa: E402
import validation  # noqa: E402

LIVE_DB = ROOT / "data" / "propaganda_model.db"
PERSOON_ID = 14   # Christian Van Thillo (type='persoon')
ORG_ID = 1        # DPG Media (type='mediaorganisatie')


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def _oud_token():
    """Een geldig, oud-genoeg lead_token (> LEAD_MIN_INVULTIJD), zodat de tijd-heuristiek
    het niet als bot dropt."""
    return server._teken_lead_token(time.time() - 10)


def _tel(db, sql):
    conn = sqlite3.connect(db)
    n = conn.execute(sql).fetchone()[0]
    conn.close()
    return n


def main():
    tmp = Path(tempfile.mkdtemp()) / "intake.db"
    shutil.copy2(LIVE_DB, tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    server._lead_emmers.clear()

    # Testaccount: een agent (leest/patcht de wachtrij, maakt de smaad-arg).
    conn = sqlite3.connect(tmp)
    agent_token = auth.new_token()
    conn.execute(
        "INSERT INTO users (username, kind, role, token_hash, provenance) VALUES (?, ?, ?, ?, ?)",
        ("intake-agent", "agent", "bijdrager", auth.hash_token(agent_token), "claude-test-1"))
    conn.commit()
    conn.close()
    kop_agent = {"Authorization": f"Bearer {agent_token}"}
    c = server.app.test_client()

    print("1. Welgevormde inzending → 201, leads-rij, 0 argumenten")
    args_voor = _tel(tmp, "SELECT COUNT(*) FROM arguments")
    r = c.get("/api/lead_token")
    eis(r.status_code == 200 and r.get_json().get("token"), "GET /api/lead_token geeft een token")
    r = c.post("/api/leads", json={"claim": "Media X negeert structureel onderwerp Y.",
                                   "soort": "tip", "lead_token": _oud_token(), "website": ""})
    j = r.get_json()
    eis(r.status_code == 201 and j.get("lead_id"), f"POST /api/leads → 201 + lead_id ({r.status_code})")
    eis("id" not in j and "status" not in j, "respons lekt geen intern id/status")
    eis(_tel(tmp, "SELECT COUNT(*) FROM leads") == 1, "precies één leads-rij")
    eis(_tel(tmp, "SELECT COUNT(*) FROM arguments") == args_voor,
        "geen enkele arguments-rij geschreven")

    print("2. XSS wordt ge-escaped opgeslagen (inert)")
    r = c.post("/api/leads", json={
        "claim": "<script>alert(1)</script> dit klopt niet",
        "quote": "<img src=x onerror=alert(2)>", "soort": "rectificatie",
        "betreft": "Media X", "lead_token": _oud_token(), "website": ""})
    eis(r.status_code == 201, f"XSS-inzending → 201 ({r.status_code})")
    conn = sqlite3.connect(tmp)
    rij = conn.execute("SELECT claim, quote FROM leads ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    eis("<script>" not in rij[0] and "&lt;script&gt;" in rij[0],
        "claim ge-escaped opgeslagen (geen ruwe <script>)")
    eis("<img" not in (rij[1] or "") and "&lt;img" in (rij[1] or ""),
        "quote ge-escaped opgeslagen (geen ruwe <img>)")

    print("3. Laag 0-poort: honeypot / tijd / blocklist / challenge / per-IP-limiet")
    n0 = _tel(tmp, "SELECT COUNT(*) FROM leads")
    # honeypot ingevuld → stille 200-drop
    r = c.post("/api/leads", json={"claim": "bot", "lead_token": _oud_token(), "website": "ingevuld"})
    eis(r.status_code == 200 and _tel(tmp, "SELECT COUNT(*) FROM leads") == n0,
        "honeypot ingevuld → stille 200-drop, 0 nieuwe rijen")
    # te snel (vers token < 2 s) → stille drop
    r = c.post("/api/leads", json={"claim": "bot", "lead_token": server._teken_lead_token(time.time()),
                                   "website": ""})
    eis(r.status_code == 200 and _tel(tmp, "SELECT COUNT(*) FROM leads") == n0,
        "render_ts < 2 s → stille drop, 0 nieuwe rijen")
    # ongeldig token → 400
    r = c.post("/api/leads", json={"claim": "x", "lead_token": "nep.token", "website": ""})
    eis(r.status_code == 400, f"ongeldig challenge-token → 400 ({r.status_code})")
    # blocklist-domein → 400
    r = c.post("/api/leads", json={"claim": "x", "bron_url": "https://bit.ly/abc",
                                   "lead_token": _oud_token(), "website": ""})
    eis(r.status_code == 400 and _tel(tmp, "SELECT COUNT(*) FROM leads") == n0,
        "blocklist-domein → 400, geen rij")
    # 50 posts vanaf één IP → meeste 429
    server._lead_emmers.clear()
    ip = {"REMOTE_ADDR": "203.0.113.7"}
    codes = []
    for i in range(50):
        r = c.post("/api/leads", json={"claim": f"floodpost variatie {i}",
                                       "lead_token": _oud_token(), "website": ""},
                   environ_overrides=ip)
        codes.append(r.status_code)
    n_429 = codes.count(429)
    n_201 = codes.count(201)
    eis(n_429 >= 40 and n_201 <= server.LEAD_RATE_LIMIET,
        f"50 posts/één IP: {n_201} door, {n_429}× 429 (limiet {server.LEAD_RATE_LIMIET})")

    print("4. Sock-puppet-collapse: 50 identieke leads → 1 binnengekomen + 49 duplicaat")
    server._lead_emmers.clear()
    uniek = "SOCKPUPPET-CLUSTER-uniek-narratief over onderwerp Z"
    for i in range(50):
        c.post("/api/leads", json={"claim": uniek, "betreft": "Media Z",
                                   "lead_token": _oud_token(), "website": ""},
               environ_overrides={"REMOTE_ADDR": f"198.51.100.{i}"})
    conn = sqlite3.connect(tmp)
    binnen = conn.execute("SELECT COUNT(*) FROM leads WHERE claim = ? AND status='binnengekomen'",
                          (server.html.escape(uniek),)).fetchone()[0]
    dup = conn.execute("SELECT COUNT(*) FROM leads WHERE claim = ? AND status='duplicaat'",
                       (server.html.escape(uniek),)).fetchone()[0]
    conn.close()
    eis(binnen == 1 and dup == 49, f"1 binnengekomen + 49 duplicaat (kreeg {binnen}/{dup})")

    print("5. 'Telt in niets': scoring/influence-snapshot byte-identiek met/zonder leads")
    conn = sqlite3.connect(tmp); conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    scores_voor = json.dumps(scoring.compute_all_scores(conn), sort_keys=True, default=str)
    infl_voor = json.dumps(influence.compute_influence(conn), sort_keys=True, default=str)
    for i in range(100):
        conn.execute("INSERT INTO leads (claim, betreft, status) VALUES (?, ?, 'binnengekomen')",
                     (f"snapshot-lead {i}", "Willekeurig"))
    conn.commit()
    scores_na = json.dumps(scoring.compute_all_scores(conn), sort_keys=True, default=str)
    infl_na = json.dumps(influence.compute_influence(conn), sort_keys=True, default=str)
    conn.close()
    eis(scores_voor == scores_na, "scoring-snapshot byte-identiek na +100 leads")
    eis(infl_voor == infl_na, "influence-snapshot byte-identiek na +100 leads")

    print("6. Smaad-firewall")
    # Bron met vindplaats zodat een supporting root de bronplicht haalt.
    r = c.post("/api/sources", headers=kop_agent, json={
        "title": "Testbron smaad-firewall", "source_type": "website",
        "location": {"type": "url", "value": "https://example.org/smaad"}})
    src_id = r.get_json()["id"]
    # (a) negatieve feitelijke claim over een PERSOON → smaad_hold=1
    r = c.post("/api/arguments", headers=kop_agent, json={
        "entity_id": PERSOON_ID, "stance": "supporting",
        "claim": "Deze persoon pleegde fraude en corruptie volgens de bron.",
        "citations": [{"source_id": src_id, "quote": "gedocumenteerde fraude"}]})
    eis(r.status_code == 201, f"persoon-claim aangemaakt ({r.status_code}: {r.get_json()})")
    persoon_arg = r.get_json()["id"]
    conn = sqlite3.connect(tmp)
    hold = conn.execute("SELECT smaad_hold FROM arguments WHERE id = ?", (persoon_arg,)).fetchone()[0]
    conn.close()
    eis(hold == 1, "negatieve persoonsclaim → smaad_hold = 1")
    server._graph_cache.clear()
    gd = c.get("/api/graph_data").get_json()
    ids = {a["id"] for a in gd["arguments"]}
    eis(persoon_arg not in ids, "smaad_hold-argument staat NIET in graph_data")
    dis = c.get(f"/api/graph_data/discussie?entity_id={PERSOON_ID}").get_json()
    eis(persoon_arg not in {a["id"] for a in dis["arguments"]},
        "smaad_hold-argument staat NIET in /api/graph_data/discussie")

    # (b) identieke lading over een ORGANISATIE → geen smaad_hold, wél in graph_data
    r = c.post("/api/arguments", headers=kop_agent, json={
        "entity_id": ORG_ID, "stance": "supporting",
        "claim": "Deze organisatie pleegde fraude en corruptie volgens de bron.",
        "citations": [{"source_id": src_id, "quote": "gedocumenteerde fraude"}]})
    org_arg = r.get_json()["id"]
    conn = sqlite3.connect(tmp)
    hold_org = conn.execute("SELECT smaad_hold FROM arguments WHERE id = ?", (org_arg,)).fetchone()[0]
    conn.close()
    eis(not hold_org, "identieke claim over organisatie → géén smaad_hold")
    server._graph_cache.clear()
    gd = c.get("/api/graph_data").get_json()
    eis(org_arg in {a["id"] for a in gd["arguments"]}, "org-claim staat wél in graph_data")

    # (c) een agent kan smaad_hold niet opheffen (403); dat doet alleen de automatische
    # beoordeling (reviewer-tier, na smaadtoets + A1, test_automatische_beoordeling.py).
    # Hier heffen we hem direct in de testkopie op en kijken of het argument verschijnt.
    r = c.post(f"/api/beoordeling/smaad_vrijgeven/{persoon_arg}", headers=kop_agent)
    eis(r.status_code == 403, f"agent mag smaad_hold niet opheffen → 403 ({r.status_code})")
    conn = sqlite3.connect(tmp)
    conn.execute("UPDATE arguments SET smaad_hold = 0 WHERE id = ?", (persoon_arg,))
    conn.commit()
    conn.close()
    server._graph_cache.clear()
    gd = c.get("/api/graph_data").get_json()
    eis(persoon_arg in {a["id"] for a in gd["arguments"]},
        "vrijgegeven argument is nu wél zichtbaar in graph_data")
    dis = c.get(f"/api/graph_data/discussie?entity_id={PERSOON_ID}").get_json()
    eis(persoon_arg in {a["id"] for a in dis["arguments"]},
        "vrijgegeven argument is nu wél zichtbaar in /api/graph_data/discussie")

    print("7. Lead-wachtrij + PATCH (agent-lane) + anomalie-check")
    r = c.get("/api/leads")  # anoniem
    eis(r.status_code == 401, f"anoniem GET /api/leads → 401 ({r.status_code})")
    r = c.get("/api/leads", headers=kop_agent)
    eis(r.status_code == 200 and "leads" in r.get_json(), "agent leest de wachtrij (200)")
    lead_id = r.get_json()["leads"][0]["id"]
    r = c.patch(f"/api/leads/{lead_id}", headers=kop_agent,
                json={"status": "gecorroboreerd", "agent_arg_id": org_arg})
    eis(r.status_code == 200 and r.get_json()["status"] == "gecorroboreerd"
        and r.get_json()["agent_arg_id"] == org_arg,
        "agent patcht lead → gecorroboreerd + agent_arg_id")
    conn = sqlite3.connect(tmp); conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    bev = [b for b in validation.check_lead_anomalie(conn) if b["code"] == "LEAD-ANOMALIE"][0]
    conn.close()
    # De sock-puppet-batch (50 over 'Media Z') overschrijdt de betreft-/duplicaat-drempel.
    eis(bev["ernst"] == "waarschuwing" and bev["aantal"] >= 1,
        f"anomalie-check vlagt de burst als waarschuwing ({bev['aantal']} treffer(s))")

    print("\nALLES GROEN — publieke intake (D2-kern/D2.0/D2.1/D2.3/D2.4).")


if __name__ == "__main__":
    main()
