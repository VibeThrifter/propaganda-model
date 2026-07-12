#!/usr/bin/env python3
"""End-to-end-test: admin-reacties (juli 2026) — auto-merge + admin-veto.

Dekt:
  - een maintainer-argument merget meteen (admin hoeft geen review; self_merged gevlagd);
  - objection_type is een vrij tekstveld (de CHECK-enum verviel);
  - een admin-ondergraving ('argument klopt niet') NULT de parent volledig (σ = 0),
    niet slechts DF-QuAD-demping — de vlaggen admin_veto/geveto staan in argument_scores;
  - een VOORGESTELDE tegen-reactie op het veto verandert niets; ná merge (review!)
    is het veto opgeschort en geldt de gewone demping weer;
  - resolutie 'opgelost' heft ook de demping op (σ terug naar τ);
  - de reasoning-plicht voor ondergravingen geldt ook voor een admin;
  - GET /api/arguments draagt auteur_is_admin voor de UI-badge.

Gebruik: python3 scripts/test_admin_veto.py   (exit-code 0 = alles groen)
"""
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
                      ("rev", "reviewer"), ("admin", "maintainer")):
        toks[naam] = auth.new_token()
        conn.execute("INSERT INTO users (username, kind, role, token_hash) VALUES (?,?,?,?)",
                     (naam, "mens", rol, auth.hash_token(toks[naam])))
    conn.commit(); conn.close()
    return toks


def main():
    tmp = Path(tempfile.mkdtemp()) / "adminveto.db"
    toks = fixture(tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    c = server.app.test_client()
    kop = {n: {"Authorization": f"Bearer {t}"} for n, t in toks.items()}

    def score(aid):
        sc = c.get("/api/scores").get_json()["argument_scores"]
        return sc.get(str(aid), sc.get(aid))

    print("1. gemergede root van een bijdrager heeft kracht")
    r = c.post("/api/arguments", headers=kop["auteur"], json={
        "relation_id": 1, "stance": "supporting", "claim": "R1 blijkt uit het jaarverslag",
        "citations": [{"source_id": 1, "quote": "p.3"}]})
    root = r.get_json()["id"]
    c.post(f"/api/arguments/{root}/merge", headers=kop["rev"])
    tau = score(root)["sigma"]
    eis(tau > 0, f"gemerged root heeft kracht σ={tau:.3f}")

    print("2. admin hoeft geen review: auto-merge")
    r = c.post("/api/arguments", headers=kop["admin"], json={
        "relation_id": 1, "stance": "supporting", "claim": "Ook de KvK-registratie staaft R1",
        "citations": [{"source_id": 1, "quote": "p.9"}]})
    a = r.get_json()
    eis(r.status_code == 201 and a["status"] == "ongecontroleerd" and a["self_merged"]
        and a["merged_by"] == "admin",
        f"admin-root merget meteen ({a.get('status')}, self_merged={a.get('self_merged')})")
    r = c.post("/api/arguments", headers=kop["admin"], json={
        "relation_id": 1, "stance": "supporting", "claim": "Kale admin-claim zonder bron"})
    eis(r.status_code == 400, f"bronplicht geldt ook voor een admin-root ({r.status_code})")

    print("3. admin-ondergraving: reasoning verplicht, vrij categorie-veld, meteen actief")
    r = c.post("/api/arguments", headers=kop["admin"], json={
        "parent_argument_id": root, "stance": "contradicting", "claim": "argument klopt niet"})
    eis(r.status_code == 400, f"ook een admin-ondergraving vereist reasoning ({r.status_code})")
    r = c.post("/api/arguments", headers=kop["admin"], json={
        "parent_argument_id": root, "stance": "contradicting", "claim": "argument klopt niet",
        "reasoning": "het jaarverslag noemt geen zeggenschap",
        "objection_type": "verouderde jaarcijfers — eigen categorie"})
    v = r.get_json()
    eis(r.status_code == 201 and v["status"] == "ongecontroleerd"
        and v["bezwaar_resolutie"] == "open",
        f"admin-ondergraving merget meteen en start 'open' ({v.get('status')})")
    eis(v["objection_type"] == "verouderde jaarcijfers — eigen categorie",
        "objection_type is een vrij tekstveld (CHECK-enum verdwenen)")
    veto = v["id"]

    print("4. het veto nult de parent volledig")
    s_root, s_veto = score(root), score(veto)
    eis(s_root["sigma"] == 0, f"parent telt voor 0 (σ={s_root['sigma']})")
    eis(s_root.get("geveto") is True, "parent draagt de geveto-vlag")
    eis(s_veto.get("admin_veto") is True, "het veto draagt de admin_veto-vlag")
    arglijst = c.get("/api/arguments?relation_id=1").get_json()
    veto_row = next(x for x in arglijst if x["id"] == veto)
    eis(veto_row["auteur_is_admin"] is True, "GET /api/arguments draagt auteur_is_admin")

    print("5. tegen-reactie: voorgesteld verandert niets, gemerged schort het veto op")
    r = c.post("/api/arguments", headers=kop["bezw"], json={
        "parent_argument_id": veto, "stance": "contradicting",
        "claim": "het bezwaar leest het verslag verkeerd",
        "reasoning": "p.3 noemt expliciet 51% van de stemrechten"})
    tegen = r.get_json()["id"]
    eis(score(root)["sigma"] == 0, "voorgestelde tegen-reactie schort het veto niet op")
    c.post(f"/api/arguments/{tegen}/merge", headers=kop["rev"])
    s = score(root)
    eis(0 < s["sigma"] < tau,
        f"gemergede tegen-reactie (review) schort op → gewone demping (σ={s['sigma']:.3f})")
    eis(not score(veto).get("admin_veto") and not s.get("geveto"),
        "vlaggen weg zodra het veto is opgeschort")

    print("6. resolutie 'opgelost' heft ook de demping op")
    r = c.patch(f"/api/arguments/{veto}/bezwaar", headers=kop["admin"], json={"actie": "opgelost"})
    eis(r.status_code == 200, f"bezwaarmaker (admin) sluit het bezwaar ({r.status_code})")
    eis(abs(score(root)["sigma"] - tau) < 1e-9,
        f"opgelost → σ terug naar τ ({score(root)['sigma']:.3f})")

    print("7. heropend veto zonder tegen-reactie nult weer (blijft)")
    # Nieuw root-argument + vers admin-veto zonder weerlegging: 'blijft' houdt de nul.
    r = c.post("/api/arguments", headers=kop["auteur"], json={
        "relation_id": 1, "stance": "supporting", "claim": "R1 blijkt ook uit het depot",
        "citations": [{"source_id": 1, "quote": "p.12"}]})
    root2 = r.get_json()["id"]
    c.post(f"/api/arguments/{root2}/merge", headers=kop["rev"])
    r = c.post("/api/arguments", headers=kop["admin"], json={
        "parent_argument_id": root2, "stance": "contradicting", "claim": "argument klopt niet",
        "reasoning": "het depot toont een andere entiteit"})
    veto2 = r.get_json()["id"]
    c.patch(f"/api/arguments/{veto2}/bezwaar", headers=kop["admin"], json={"actie": "blijft"})
    eis(score(root2)["sigma"] == 0, "niet-opgelost admin-bezwaar ('blijft') houdt de parent op 0")

    print("\nAdmin-reacties (auto-merge + veto + vrij categorie-veld): alles groen.")


if __name__ == "__main__":
    main()
