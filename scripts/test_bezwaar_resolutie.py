#!/usr/bin/env python3
"""End-to-end-test: review-verdict v2 — ondergraving ('logica klopt niet') + resolutielus.

Dekt:
  - 'logica klopt niet' = een ONDERGRAVING (contradicting reply) met VERPLICHTE reden;
  - de ondergraving start in 'open' en dempt de parent pas ná merge (M2.2);
  - de resolutielus: auteur 'herzien' → bezwaarmaker 'opgelost'/'blijft', met de
    governance-keuze "blijft dempen; reviewer mag overrulen ná 'herzien'";
  - 'opgelost' heft de demping in de score op (scoring.py); 'blijft'/'open'/'herzien' niet.

Gebruik: python3 scripts/test_bezwaar_resolutie.py   (exit-code 0 = alles groen)
"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth      # noqa: E402
import server    # noqa: E402


def eis(c, m):
    if not c:
        sys.exit(f"FAAL: {m}")
    print(f"  ok — {m}")


def fixture(pad):
    conn = sqlite3.connect(pad)
    conn.executescript((ROOT / "schema.sql").read_text())
    conn.execute("INSERT INTO entities (id, name, type) VALUES (1,'H','bedrijf')")
    conn.execute("INSERT INTO entities (id, name, type) VALUES (2,'K','mediaorganisatie')")
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    mechanism_id, certainty, influence) VALUES (1,1,2,'eigendom',1,0.8,0.5)""")
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (1,'Bron','rapport','institutioneel','c')""")
    toks = {}
    for naam, rol in (("auteur", "bijdrager"), ("bezw", "bijdrager"),
                      ("derde", "bijdrager"), ("rev", "reviewer")):
        toks[naam] = auth.new_token()
        conn.execute("INSERT INTO users (username, kind, role, token_hash) VALUES (?,?,?,?)",
                     (naam, "mens", rol, auth.hash_token(toks[naam])))
    conn.commit(); conn.close()
    return toks


def main():
    tmp = Path(tempfile.mkdtemp()) / "bezwaar.db"
    toks = fixture(tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    c = server.app.test_client()
    kop = {n: {"Authorization": f"Bearer {t}"} for n, t in toks.items()}

    def sigma(aid):
        sc = c.get("/api/scores").get_json()["argument_scores"]
        return sc.get(str(aid), sc.get(aid))["sigma"]

    print("1. root-argument: indienen + mergen")
    r = c.post("/api/arguments", headers=kop["auteur"], json={
        "relation_id": 1, "stance": "supporting", "claim": "R1 blijkt uit het jaarverslag",
        "citations": [{"source_id": 1, "quote": "p.3"}]})
    root = r.get_json()["id"]
    c.post(f"/api/arguments/{root}/merge", headers=kop["rev"])
    tau = sigma(root)
    eis(tau > 0, f"gemerged root heeft kracht σ={tau:.3f}")

    print("2. ondergraving: reden verplicht")
    r = c.post("/api/arguments", headers=kop["bezw"], json={
        "parent_argument_id": root, "stance": "contradicting", "claim": "klopt niet"})
    eis(r.status_code == 400, f"contradicting reply zonder reasoning → 400 ({r.status_code})")
    r = c.post("/api/arguments", headers=kop["bezw"], json={
        "parent_argument_id": root, "stance": "contradicting", "claim": "klopt niet",
        "reasoning": "het jaarverslag noemt geen zeggenschap, alleen een belang"})
    b = r.get_json()
    eis(r.status_code == 201 and b["bezwaar_resolutie"] == "open",
        f"met reasoning → 201, resolutie 'open' ({b.get('bezwaar_resolutie')})")
    bez = b["id"]

    print("3. demping pas na merge van het bezwaar")
    eis(abs(sigma(root) - tau) < 1e-9, "voorgesteld bezwaar dempt nog niet")
    c.post(f"/api/arguments/{bez}/merge", headers=kop["rev"])
    gedempt = sigma(root)
    eis(gedempt < tau, f"gemerged bezwaar dempt de parent (σ {tau:.3f} → {gedempt:.3f})")

    print("4. resolutielus: rechten")
    r = c.patch(f"/api/arguments/{bez}/bezwaar", headers=kop["derde"], json={"actie": "opgelost"})
    eis(r.status_code == 403, f"willekeurige derde mag niet sluiten ({r.status_code})")
    r = c.patch(f"/api/arguments/{bez}/bezwaar", headers=kop["rev"], json={"actie": "opgelost"})
    eis(r.status_code == 403, f"reviewer mag niet sluiten vóór 'herzien' ({r.status_code})")
    r = c.patch(f"/api/arguments/{bez}/bezwaar", headers=kop["derde"], json={"actie": "herzien"})
    eis(r.status_code == 403, f"niet-auteur/niet-reviewer mag niet 'herzien' zetten ({r.status_code})")

    print("5. auteur herziet → reviewer overrult → demping weg")
    r = c.patch(f"/api/arguments/{bez}/bezwaar", headers=kop["auteur"], json={"actie": "herzien"})
    eis(r.status_code == 200, "auteur van het aangevochten argument zet 'herzien'")
    eis(sigma(root) < tau, "herzien dempt nog steeds (per governance-keuze)")
    r = c.patch(f"/api/arguments/{bez}/bezwaar", headers=kop["rev"], json={"actie": "opgelost"})
    j = r.get_json()
    eis(r.status_code == 200 and j["overrule"] is True, "reviewer overrult ná 'herzien' (gevlagd)")
    eis(abs(sigma(root) - tau) < 1e-9, f"opgelost heft de demping op (σ terug naar {tau:.3f})")

    print("6. bezwaarmaker mag altijd zelf sluiten/handhaven")
    r = c.patch(f"/api/arguments/{bez}/bezwaar", headers=kop["bezw"], json={"actie": "blijft"})
    eis(r.status_code == 200, "bezwaarmaker handhaaft ('blijft')")
    eis(sigma(root) < tau, "blijft dempt weer")

    # (7) De bridging-laag is bij de solo+agents-kanteling geschrapt (A3, juli 2026);
    # de test_bridging()-subtest is daarmee vervallen — een gehandhaafde ondergraving
    # dempt de parent-σ nog steeds (bewezen in stap 4/6 hierboven), maar er is geen
    # ratings-/bridging-matrix meer die de −1 leest.
    print("\nReview-verdict v2 (ondergraving + resolutielus): alles groen.")


if __name__ == "__main__":
    main()
