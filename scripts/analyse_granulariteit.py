#!/usr/bin/env python3
"""
Granulariteitsanalyse (verbeterplan M2.6): vlag splits-/samenvoegkandidaten.

Het script BESLIST NIETS — het rangschikt kandidaten voor de onderzoeksagenda
(M3.2); een echte splitsing/samenvoeging loopt altijd via het voorstelpad
(POST /api/voorstellen, twee reviewers op de theorielaag).

Heuristieken (alleen stdlib):
  Samenvoegkandidaten (paren mechanismen of rollen):
    - bron-overlap: Jaccard van de bron-id-verzamelingen onder hun argumenten
      ("vrijwel identieke bron- en argumentverzamelingen wijzen op samenvoegen");
    - tekstgelijkenis van naam + beschrijving (difflib);
    - mechanismen: overlap in entiteit-paren van hun relaties (dezelfde dyade
      twee keer gemodelleerd — zoals de omgekeerde duplicaten uit M0.4).
  Splitskandidaten (één element):
    - de argumenten vallen uiteen in ≥ 2 onderling bronvreemde clustergroepen
      (geen gedeelde bronclusters) — disjuncte bewijslijnen wijzen op een
      element dat twee dingen vermengt.

Uitvoer: leesbaar rapport + data/granulariteit.json.
Gebruik: python3 scripts/analyse_granulariteit.py
"""
import difflib
import itertools
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
OUT_PATH = ROOT / "data" / "granulariteit.json"

MERGE_BRON_JACCARD = 0.5   # ≥ → kandidaat
MERGE_TEKST = 0.55         # ≥ → kandidaat
MIN_ARGS_SPLIT = 4         # splitsanalyse vergt wat bewijsvolume


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def analyse(conn):
    elementen = {}
    for soort, tabel, kolom in (("mechanisme", "mechanisms", "mechanism_id"),
                                ("rol", "roles", "role_id")):
        for r in conn.execute(f"SELECT id, name, description FROM {tabel} "
                              "WHERE NOT vervangen"):
            bronnen, clusters = set(), {}
            for rij in conn.execute(f"""
                SELECT a.id, s.id AS source_id, COALESCE(s.cluster_key, 'bron' || s.id) AS ck
                FROM arguments a
                LEFT JOIN citations c ON c.argument_id = a.id
                LEFT JOIN sources s ON s.id = c.source_id
                WHERE a.{kolom} = ? AND a.parent_argument_id IS NULL
                  AND (a.property IS NULL OR a.property != 'indirecte_invloed_op')""",
                    (r["id"],)):
                if rij["source_id"]:
                    bronnen.add(rij["source_id"])
                    clusters.setdefault(rij["id"], set()).add(rij["ck"])
                else:
                    clusters.setdefault(rij["id"], set())
            paren = set()
            if soort == "mechanisme":
                paren = {tuple(sorted(p)) for p in conn.execute(
                    "SELECT source_id, target_id FROM relations WHERE mechanism_id = ? "
                    "AND NOT vervangen", (r["id"],))}
            elementen[(soort, r["id"])] = {
                "id": r["id"], "soort": soort, "naam": r["name"],
                "tekst": f"{r['name']} {r['description'] or ''}".lower(),
                "bronnen": bronnen, "arg_clusters": clusters, "paren": paren,
            }

    merge_kandidaten = []
    per_soort = {}
    for (soort, _), e in elementen.items():
        per_soort.setdefault(soort, []).append(e)
    for soort, lijst in per_soort.items():
        for a, b in itertools.combinations(lijst, 2):
            bron_j = jaccard(a["bronnen"], b["bronnen"])
            tekst = difflib.SequenceMatcher(None, a["tekst"], b["tekst"]).ratio()
            paar_j = jaccard(a["paren"], b["paren"]) if soort == "mechanisme" else 0.0
            redenen = []
            # ≥ 2 gedeelde bronnen: één gedeeld standaardwerk (Chomsky) zegt niets
            if bron_j >= MERGE_BRON_JACCARD and len(a["bronnen"] & b["bronnen"]) >= 2:
                redenen.append(f"bron-overlap {bron_j:.2f}")
            if tekst >= MERGE_TEKST:
                redenen.append(f"tekstgelijkenis {tekst:.2f}")
            if paar_j >= 0.5 and a["paren"]:
                redenen.append(f"zelfde entiteit-paren {paar_j:.2f}")
            if redenen:
                merge_kandidaten.append({
                    "soort": soort, "a": {"id": a["id"], "naam": a["naam"]},
                    "b": {"id": b["id"], "naam": b["naam"]},
                    "score": round(max(bron_j, tekst, paar_j), 3),
                    "redenen": redenen})
    merge_kandidaten.sort(key=lambda k: -k["score"])

    split_kandidaten = []
    for e in elementen.values():
        bezet = {aid: cl for aid, cl in e["arg_clusters"].items() if cl}
        if len(bezet) < MIN_ARGS_SPLIT:
            continue
        # groepeer argumenten die (transitief) een broncluster delen
        groepen = []
        for aid, cl in bezet.items():
            geraakt = [g for g in groepen if g["clusters"] & cl]
            if not geraakt:
                groepen.append({"args": {aid}, "clusters": set(cl)})
            else:
                basis = geraakt[0]
                basis["args"].add(aid)
                basis["clusters"] |= cl
                for g in geraakt[1:]:
                    basis["args"] |= g["args"]
                    basis["clusters"] |= g["clusters"]
                    groepen.remove(g)
        grote = [g for g in groepen if len(g["args"]) >= 2]
        if len(grote) >= 2:
            split_kandidaten.append({
                "soort": e["soort"], "id": e["id"], "naam": e["naam"],
                "n_groepen": len(grote),
                "groepsgroottes": sorted((len(g["args"]) for g in grote), reverse=True),
                "reden": f"{len(grote)} onderling bronvreemde bewijsgroepen"})
    split_kandidaten.sort(key=lambda k: -k["n_groepen"])

    return {"merge_kandidaten": merge_kandidaten, "split_kandidaten": split_kandidaten}


def main():
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rapport = analyse(conn)
    conn.close()

    print(f"== Samenvoegkandidaten ({len(rapport['merge_kandidaten'])}) ==")
    for k in rapport["merge_kandidaten"][:15]:
        print(f"  [{k['soort']}] {k['a']['naam']} + {k['b']['naam']}"
              f"  ({'; '.join(k['redenen'])})")
    print(f"\n== Splitskandidaten ({len(rapport['split_kandidaten'])}) ==")
    for k in rapport["split_kandidaten"][:15]:
        print(f"  [{k['soort']}] {k['naam']}: {k['reden']} "
              f"(groottes {k['groepsgroottes']})")

    OUT_PATH.write_text(json.dumps(rapport, ensure_ascii=False, indent=1))
    print(f"\nGeschreven: {OUT_PATH} — kandidaten zijn input voor RfC's (M2.3/M2.6), "
          "geen besluiten.")


if __name__ == "__main__":
    main()
