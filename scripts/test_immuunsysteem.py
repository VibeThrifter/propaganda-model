#!/usr/bin/env python3
"""End-to-end test voor de backend-kern van het immuunsysteem (Fase 2, stories A1/A2/A5).

Twee lagen, beide tegen een verse DB uit schema.sql (geen live-DB-afhankelijkheid):
1. Endpoints (Flask test_client): herverificatie (A1) + tegenspraak (A2) — zelf-oordeel
   → 403, geldig oordeel van een ander account → rij + edit_log geschreven, en het
   oordeel verschuift GEEN enkele score (GET /api/scores identiek vóór en na).
2. Scoring (A5): de provenance-methode-tier weegt in de bronfactor; twee identieke
   citaties met verschillende `methode` geven verschillende τ, en methode=NULL = factor 1,0.

Gebruik: python3 scripts/test_immuunsysteem.py   (exit-code 0 = alles groen)
"""
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth      # noqa: E402
import scoring   # noqa: E402
import server    # noqa: E402

SCHEMA = (ROOT / "schema.sql").read_text()


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


# ── Deel 1: endpoints (A1/A2) ────────────────────────────────

def _seed_endpoint_db(pad):
    conn = sqlite3.connect(pad)
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO entities (id, name, type) VALUES (1, 'Holding', 'bedrijf')")
    conn.execute("INSERT INTO entities (id, name, type) VALUES (2, 'Krant', 'mediaorganisatie')")
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    certainty, influence) VALUES (1, 1, 2, 'eigendom', 0.9, 0.6)""")
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability)
                    VALUES (1, 'Bron A', 'website', 'regulier')""")
    conn.execute("""INSERT INTO source_locations (source_id, location_type, location)
                    VALUES (1, 'url', 'https://example.org/a')""")
    tok = {}
    for naam, kind, rol, prov in [
            ("imm-agent-a", "agent", "bijdrager", "familie-a"),
            ("imm-agent-b", "agent", "bijdrager", "familie-b"),
            ("imm-rev", "mens", "reviewer", None)]:
        t = auth.new_token()
        tok[naam] = t
        conn.execute("INSERT INTO users (username, kind, role, token_hash, provenance) "
                     "VALUES (?, ?, ?, ?, ?)", (naam, kind, rol, auth.hash_token(t), prov))
    conn.commit()
    conn.close()
    return tok


def test_endpoints():
    tmp = Path(tempfile.mkdtemp()) / "immuun.db"
    tok = _seed_endpoint_db(tmp)
    server.DB_PATH = tmp
    c = server.app.test_client()

    def kop(naam):
        return {"Authorization": f"Bearer {tok[naam]}"}

    print("1. Argument + merge (telt in de score mee)")
    r = c.post("/api/arguments", headers=kop("imm-agent-a"),
               json={"relation_id": 1, "stance": "supporting", "claim": "Holding bezit de Krant.",
                     "citations": [{"source_id": 1, "quote": "de holding bezit de krant"}]})
    eis(r.status_code == 201, f"agent-a plaatst root ({r.status_code})")
    arg_id = r.get_json()["id"]
    r = c.post(f"/api/arguments/{arg_id}/merge", headers=kop("imm-rev"))
    eis(r.status_code == 200, f"reviewer merget de root ({r.status_code})")

    scores_voor = c.get("/api/scores").get_json()

    print("2. Herverificatie (A1)")
    r = c.post(f"/api/arguments/{arg_id}/herverificatie", headers=kop("imm-agent-a"),
               json={"verdict": "klopt"})
    eis(r.status_code == 403, f"zelf-verificatie → 403 ({r.status_code})")
    r = c.post(f"/api/arguments/{arg_id}/herverificatie", headers=kop("imm-agent-b"),
               json={"verdict": "klopt", "verbatim_span": "De holding bezit de krant, blijkt.",
                     "bron_id": 1})
    eis(r.status_code == 201 and r.get_json()["verdict"] == "klopt",
        f"ander account, verbatim-match → verdict 'klopt' ({r.status_code})")
    r = c.post(f"/api/arguments/{arg_id}/herverificatie", headers=kop("imm-agent-b"),
               json={"verdict": "klopt"})
    eis(r.status_code == 409, f"tweede oordeel zelfde account/fase → 409 ({r.status_code})")
    r = c.post(f"/api/arguments/{arg_id}/herverificatie", headers=kop("imm-agent-b"),
               json={"verdict": "onzin"})
    eis(r.status_code == 400, f"ongeldig verdict → 400 ({r.status_code})")

    print("3. Tegenspraak (A2)")
    r = c.post(f"/api/arguments/{arg_id}/tegenspraak", headers=kop("imm-agent-a"),
               json={"verdict": "overleefd"})
    eis(r.status_code == 403, f"zelf-certificering → 403 ({r.status_code})")
    r = c.post(f"/api/arguments/{arg_id}/tegenspraak", headers=kop("imm-agent-b"),
               json={"verdict": "overleefd", "detail": "geen tegenbron gevonden"})
    eis(r.status_code == 201, f"ander account certificeert 'overleefd' ({r.status_code})")

    # Score-invariantie tight meten: alléén immuun-oordelen zijn sinds scores_voor
    # toegevoegd (nog geen nieuwe argumenten). Zo bewijst de gelijkheid dat de oordelen
    # nergens in de score tellen.
    scores_na = c.get("/api/scores").get_json()
    eis(json.dumps(scores_voor, sort_keys=True) == json.dumps(scores_na, sort_keys=True),
        "GET /api/scores identiek vóór en na de immuun-oordelen (telt nergens mee)")

    print("4. Verbatim-voorcheck forceert 'twijfel'")
    r = c.post("/api/arguments", headers=kop("imm-agent-a"),
               json={"relation_id": 1, "stance": "supporting", "claim": "Iets heel anders geldt hier.",
                     "citations": [{"source_id": 1, "quote": "de kat zat op de mat"}]})
    arg2 = r.get_json()["id"]
    c.post(f"/api/arguments/{arg2}/merge", headers=kop("imm-rev"))
    r = c.post(f"/api/arguments/{arg2}/herverificatie", headers=kop("imm-agent-b"),
               json={"verdict": "klopt", "verbatim_span": "compleet ongerelateerde passage"})
    eis(r.status_code == 201 and r.get_json()["verdict"] == "twijfel",
        f"verbatim_span zonder quote-match → verdict verlaagd naar 'twijfel' ({r.status_code})")

    print("5. Rijen + edit_log geschreven, model_familie uit provenance")
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    rijen = conn.execute("SELECT * FROM immuun_oordelen WHERE argument_id = ? ORDER BY id",
                         (arg_id,)).fetchall()
    eis(len(rijen) == 2, f"twee immuun_oordelen-rijen voor arg #{arg_id} ({len(rijen)})")
    eis({r["fase"] for r in rijen} == {"herverificatie", "tegenspraak"},
        "beide fasen aanwezig")
    eis(all(r["door"] == "imm-agent-b" and r["model_familie"] == "familie-b" for r in rijen),
        "door + model_familie (uit users.provenance) correct opgeslagen")
    n_log = conn.execute(
        "SELECT COUNT(*) FROM edit_log WHERE table_name = 'immuun_oordelen' AND action = 'created'"
    ).fetchone()[0]
    eis(n_log == 3, f"drie edit_log-regels (2 arg1 + 1 arg2) ({n_log})")
    conn.close()

    print("6. Review-queue toont het nieuwste verdict")
    r = c.post("/api/arguments", headers=kop("imm-agent-a"),
               json={"relation_id": 1, "stance": "supporting", "claim": "Nog een aparte claim erbij.",
                     "citations": [{"source_id": 1, "quote": "nog een quote"}]})
    arg3 = r.get_json()["id"]
    c.post(f"/api/arguments/{arg3}/herverificatie", headers=kop("imm-agent-b"),
           json={"verdict": "twijfel"})
    q = c.get("/api/review_queue", headers=kop("imm-rev")).get_json()
    kaart = next((a for a in q["argumenten"] if a["id"] == arg3), None)
    eis(kaart is not None and kaart.get("herverificatie", {}).get("verdict") == "twijfel",
        "review_queue verrijkt de kaart met het herverificatie-verdict")


# ── Deel 2: provenance-methode-tier (A5) ─────────────────────

def test_methode_scoring():
    print("8. A5 — methode weegt in de bronfactor")
    verbatim = scoring.source_factor([("academisch", "algemeen", "verbatim_quote")])
    nul = scoring.source_factor([("academisch", "algemeen", None)])
    llm = scoring.source_factor([("academisch", "algemeen", "llm_samenvatting_van_pagina")])
    register = scoring.source_factor([("academisch", "algemeen", "officieel_register_scrape")])
    eis(verbatim == nul, f"methode=NULL == verbatim (beide factor 1,0) ({nul} == {verbatim})")
    eis(llm < register < verbatim,
        f"llm ({llm:.4f}) < register ({register:.4f}) < verbatim ({verbatim:.4f})")

    # Terugwaartse compat: 2-tuple en kale string blijven werken.
    eis(scoring.source_factor([("academisch", "algemeen")]) == verbatim,
        "2-tuple (reliability, onderwerp) = neutrale methode")
    eis(scoring.source_factor(["academisch"]) > scoring.NO_CITATION_FACTOR,
        "kale reliability-string blijft geldig")

    print("9. A5 — identieke citaties, verschillende methode → verschillende τ")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO entities (id, name, type) VALUES (1, 'H', 'bedrijf')")
    conn.execute("INSERT INTO entities (id, name, type) VALUES (2, 'K', 'mediaorganisatie')")
    for rid in (1, 2, 3):
        conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                        certainty, influence) VALUES (?, 1, 2, 'eigendom', 0.9, 0.6)""", (rid,))
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (1, 'B', 'website', 'regulier', 'c1')""")
    # Drie identieke supporting-roots, elk één citatie uit dezelfde bron, andere methode.
    for aid, rid, meth in [(1, 1, "verbatim_quote"), (2, 2, "llm_samenvatting_van_pagina"),
                           (3, 3, None)]:
        conn.execute("""INSERT INTO arguments (id, relation_id, stance, claim, status)
                        VALUES (?, ?, 'supporting', ?, 'geverifieerd')""",
                     (aid, rid, f"claim {aid}"))
        conn.execute("INSERT INTO citations (argument_id, source_id, quote, methode) "
                     "VALUES (?, 1, 'quote', ?)", (aid, meth))
    conn.commit()
    scores = scoring.compute_all_scores(conn)
    tau = {aid: scores["argument_scores"][aid]["tau"] for aid in (1, 2, 3)}
    eis(tau[1] > tau[2], f"verbatim-τ ({tau[1]}) > llm-τ ({tau[2]})")
    eis(tau[1] == tau[3], f"verbatim-τ == NULL-τ ({tau[1]} == {tau[3]})")
    conn.close()


def main():
    test_endpoints()
    test_methode_scoring()
    print("\nTest immuunsysteem: alles groen.")


if __name__ == "__main__":
    main()
