#!/usr/bin/env python3
"""
Onderzoeksagenda (verbeterplan M3.2): ranglijst belang × bewijsarmoede.

Het systeem vertelt zelf waar het zwak is: theorie-elementen die veel dragen
(hoge geloofwaardigheid/sterkte) maar dun onderbouwd zijn (weinig bronclusters,
weinig argumenten, geen tegenspraak, geen compositieclaim) staan bovenaan —
daar levert één nieuwe goede bron de grootste verschuiving op (Value of
Information). De lijst stuurt de eerstvolgende scout-missie (M1.9) en is de
voordeur voor nieuwkomers (§6.5).

Daarnaast de red-team-doelwitten (M3.3): de top-20 invloedrijkste edges van het
praktijkmodel (afgeleide invloed × afgeleide zekerheid, scoring/M1.7 — dezelfde
gewichten als de invloedsgraaf in influence.py), met hun stance-balans. Dát zijn
de claims waarvoor georganiseerde tegenspraak het meest oplevert.

Beide ranglijsten BESLISSEN niets; ze prioriteren bijdrage-werk.

Uitvoer: leesbaar rapport + data/onderzoeksagenda.json (→ /api/health → viz).
Gebruik: python3 scripts/onderzoeksagenda.py
"""
import datetime
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import scoring  # noqa: E402  (repo-root module met de scoringsketen)

DB_PATH = ROOT / "data" / "propaganda_model.db"
OUT_PATH = ROOT / "data" / "onderzoeksagenda.json"

TOP_AGENDA = 25
TOP_REDTEAM = 20


def bewijsarmoede(s, is_veld=False):
    """0..1: hoe dun is de onderbouwing? Gemiddelde van concrete tekorten.

    - brontekort:      1/(1+n onafhankelijke steunclusters) — M1.2;
    - volumetekort:    1/(1+n argumenten + n instanties);
    - tegenspraaktekort: 1,0 zolang het element 'onweersproken' is (M1.4);
    - velden bovendien: compositietekort (M1.5) — zonder compositieclaim is
      juist de meest verstrekkende claim ongetoetst.
    """
    n_clusters = s.get("n_steun_clusters", 0)
    volume = s.get("n_bronnen", 0) + s.get("n_instanties", 0) + s.get("n_compositie", 0)
    tekorten = [1.0 / (1.0 + n_clusters),
                1.0 / (1.0 + volume),
                1.0 if s.get("onweersproken") else 0.0]
    if is_veld:
        tekorten.append(1.0 if s.get("zonder_compositieclaim") else 0.0)
    return sum(tekorten) / len(tekorten)


def ontbreekt(s, is_veld=False):
    """De concrete gaten, als actielijst voor een scout-/red-team-missie."""
    gaten = []
    if s.get("onweersproken"):
        gaten.append("geen overwogen tegenspraak (M1.4-plafond actief)")
    if s.get("spof"):
        gaten.append("drijft op één broncluster")
    elif not s.get("n_steun_clusters"):
        gaten.append("geen onafhankelijke bronclusters")
    if is_veld and s.get("zonder_compositieclaim"):
        gaten.append("geen compositieclaim (plafond 0,50)")
    if not is_veld and not s.get("n_instanties"):
        gaten.append("geen praktijk-instanties")
    if not s.get("n_bronnen"):
        gaten.append("geen literatuurargumenten")
    return gaten


def bouw_agenda(conn, scores):
    agenda = []
    naam = {("mechanisme", r[0]): (r[1], r[2]) for r in conn.execute(
        "SELECT id, name, filter FROM mechanisms WHERE NOT vervangen")}
    naam.update({("rol", r[0]): (r[1], r[2]) for r in conn.execute(
        "SELECT id, name, category FROM roles WHERE NOT vervangen")})
    naam.update({("veld", r[0]): (r[1], r[2]) for r in conn.execute(
        "SELECT id, label, category FROM emergent_effects WHERE NOT vervangen")})

    for soort, sleutel in (("mechanisme", "mechanisms"), ("rol", "roles"),
                           ("veld", "emergent_effects")):
        for eid, s in scores.get(sleutel, {}).items():
            is_veld = soort == "veld"
            belang = (s["geloofwaardigheid"] if is_veld
                      else max(s["geloofwaardigheid"], s["sterkte"]))
            armoede = bewijsarmoede(s, is_veld)
            n, cat = naam.get((soort, eid), (f"#{eid}", "?"))
            agenda.append({
                "type": soort, "id": eid, "naam": n, "categorie": cat,
                "belang": round(belang, 4),
                "bewijsarmoede": round(armoede, 4),
                "prioriteit": round(belang * armoede, 4),
                "geloofwaardigheid": s["geloofwaardigheid"],
                "ontbreekt": ontbreekt(s, is_veld),
            })
    agenda.sort(key=lambda a: -a["prioriteit"])
    return agenda


def bouw_redteam(conn, scores):
    """Top-N invloedrijkste edges: afgeleide invloed × afgeleide zekerheid."""
    edges = []
    for r in conn.execute("""
            SELECT r.id, e1.name AS bron, e2.name AS doel, r.relation_type,
                   m.name AS mechanisme
            FROM relations r
            JOIN entities e1 ON e1.id = r.source_id
            JOIN entities e2 ON e2.id = r.target_id
            LEFT JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE NOT r.vervangen"""):
        invloed = scores["relations_influence"].get(r["id"], 0.0)
        detail = scores["relations_detail"].get(r["id"], {})
        zekerheid = detail.get("score", 0.0)
        edges.append({
            "relatie_id": r["id"],
            "edge": f"{r['bron']} → {r['doel']}",
            "relation_type": r["relation_type"],
            "mechanisme": r["mechanisme"],
            "invloed": round(invloed, 4),
            "zekerheid": round(zekerheid, 4),
            "gewicht": round(invloed * zekerheid, 4),
            "n_voor": detail.get("n_voor", 0),
            "n_tegen": detail.get("n_tegen", 0),
            "onweersproken": detail.get("onweersproken", True),
        })
    edges.sort(key=lambda e: -e["gewicht"])
    return edges[:TOP_REDTEAM]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    scores = scoring.compute_all_scores(
        conn, bridged_weights=scoring.bridged_weights_from_file(
            DB_PATH.parent / "bridging.json"))
    agenda = bouw_agenda(conn, scores)
    redteam = bouw_redteam(conn, scores)
    conn.close()

    print(f"== Onderzoeksagenda (M3.2) — top {TOP_AGENDA} van {len(agenda)} "
          "theorie-elementen (belang × bewijsarmoede) ==\n")
    for a in agenda[:TOP_AGENDA]:
        gaten = "; ".join(a["ontbreekt"]) or "—"
        print(f"  {a['prioriteit']:.3f}  {a['type']:<11} {a['naam']:<42} {gaten}")

    print(f"\n== Red-team-doelwitten (M3.3) — top {TOP_REDTEAM} invloedrijkste "
          "edges (invloed × zekerheid) ==\n")
    for e in redteam:
        balans = f"{e['n_voor']} voor / {e['n_tegen']} tegen"
        vlag = "  [onweersproken]" if e["onweersproken"] else ""
        print(f"  {e['gewicht']:.3f}  #{e['relatie_id']:<4} {e['edge']:<60} "
              f"{balans}{vlag}")

    OUT_PATH.write_text(json.dumps({
        "gegenereerd": datetime.datetime.now().isoformat(timespec="seconds"),
        "agenda": agenda[:TOP_AGENDA],
        "redteam_top20": redteam,
    }, ensure_ascii=False, indent=2))
    print(f"\nRapport: {OUT_PATH.relative_to(ROOT)} (→ /api/health → "
          "Modelgezondheid-paneel)")


if __name__ == "__main__":
    main()
