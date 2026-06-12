#!/usr/bin/env python3
"""
Gevoeligheidsanalyse van de scoringsketen (verbeterplan M1.6, dicht Z7).

Twee vragen:
1. Leave-one-cluster-out: welke theorie-elementen (mechanismen, rollen, velden)
   verschuiven het hardst als één broncluster wegvalt? Een element dat op één
   cluster drijft (SPOF) hoort hier bovenaan te staan — dit kalibreert ook het
   M1.4-plafond en voedt de onderzoeksagenda (M3.2).
2. Parameter-sweep (one-at-a-time) over de constanten in scoring.py: welke
   conclusies (de top-10 mechanismen op geloofwaardigheid) zijn robuust voor de
   gekozen constanten en welke niet?

Uitvoer: leesbaar rapport op stdout + data/gevoeligheid.json (opgepikt door
/api/health en het Modelgezondheid-paneel in de viz).

Gebruik: python3 scripts/analyse_gevoeligheid.py [--drempel 0.05]
"""
import argparse
import datetime
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import scoring  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
OUT_PATH = ROOT / "data" / "gevoeligheid.json"

# One-at-a-time-sweep: per constante de varianten náást de huidige waarde.
SWEEP = {
    "K_AGG": [2.5, 10.0],
    "K_INSTANCE": [0.5, 2.0],
    "K_LIT": [0.5, 2.0],
    "K_INFLUENCE": [1.0, 4.0],
    "NO_CITATION_FACTOR": [0.15, 0.45],
    "CAP_ONWEERSPROKEN": [0.6, 0.8],
}


def theorie_scores(scores):
    """Vlakke {(soort, id): geloofwaardigheid} over mechanismen, rollen en velden."""
    plat = {}
    for soort, sleutel in (("mechanisme", "mechanisms"), ("rol", "roles"),
                           ("veld", "emergent_effects")):
        for eid, s in scores.get(sleutel, {}).items():
            plat[(soort, eid)] = s["geloofwaardigheid"]
    return plat


def namen(conn):
    n = {}
    for soort, tabel, kol in (("mechanisme", "mechanisms", "name"),
                              ("rol", "roles", "name"),
                              ("veld", "emergent_effects", "label")):
        for r in conn.execute(f"SELECT id, {kol} FROM {tabel}"):
            n[(soort, r[0])] = r[1]
    return n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--drempel", type=float, default=0.05,
                        help="rapporteer verschuivingen groter dan deze delta (default 0,05)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    naam = namen(conn)

    basis = theorie_scores(scoring.compute_all_scores(conn))

    # ── 1. Leave-one-cluster-out ─────────────────────────────
    clusters = [r[0] for r in conn.execute(
        "SELECT DISTINCT COALESCE(cluster_key, 'bron' || id) FROM sources ORDER BY 1")]
    print(f"Leave-one-cluster-out over {len(clusters)} bronclusters …")
    kwetsbaar = {}   # (soort, id) -> (max delta, boosdoener-cluster)
    per_cluster = {}
    for cl in clusters:
        scores = theorie_scores(scoring.compute_all_scores(conn, exclude_cluster=cl))
        deltas = {k: round(basis[k] - scores.get(k, 0.0), 4) for k in basis}
        geraakt = {k: d for k, d in deltas.items() if abs(d) >= args.drempel}
        if geraakt:
            per_cluster[cl] = len(geraakt)
        for k, d in deltas.items():
            if abs(d) > abs(kwetsbaar.get(k, (0.0, None))[0]):
                kwetsbaar[k] = (d, cl)

    top = sorted(((abs(d), k, d, cl) for k, (d, cl) in kwetsbaar.items()
                  if abs(d) >= args.drempel), reverse=True)[:10]
    print(f"\nTop-{len(top)} kwetsbaarste theorie-elementen (delta ≥ {args.drempel}):")
    loco_rapport = []
    for _, k, d, cl in top:
        soort, eid = k
        print(f"  {soort} {naam.get(k, eid):<38} Δ {d:+.3f} zonder cluster '{cl}' "
              f"(basis {basis[k]:.3f})")
        loco_rapport.append({"soort": soort, "id": eid, "naam": naam.get(k, str(eid)),
                             "basis": basis[k], "delta": d, "cluster": cl})

    # ── 2. Parameter-sweep (one-at-a-time) ───────────────────
    print("\nParameter-sweep (top-10 mechanismen op geloofwaardigheid):")
    basis_top10 = [k for k in sorted((k for k in basis if k[0] == "mechanisme"),
                                     key=lambda k: -basis[k])[:10]]
    sweep_rapport = []
    for const, varianten in SWEEP.items():
        origineel = getattr(scoring, const)
        for v in varianten:
            setattr(scoring, const, v)
            try:
                scores = theorie_scores(scoring.compute_all_scores(conn))
            finally:
                setattr(scoring, const, origineel)
            top10 = [k for k in sorted((k for k in scores if k[0] == "mechanisme"),
                                       key=lambda k: -scores[k])[:10]]
            overlap = len(set(basis_top10) & set(top10))
            max_delta = max(abs(basis[k] - scores[k]) for k in basis)
            print(f"  {const} = {v:<5} (nu {origineel}): top-10-overlap {overlap}/10, "
                  f"max Δ {max_delta:.3f}")
            sweep_rapport.append({"constante": const, "waarde": v, "huidig": origineel,
                                  "top10_overlap": overlap, "max_delta": round(max_delta, 4)})

    robuust = all(r["top10_overlap"] >= 8 for r in sweep_rapport)
    print(f"\nConclusie-robuustheid: top-10 mechanismen zijn "
          f"{'parameter-robuust (overlap ≥ 8/10 in elke variant)' if robuust else 'NIET parameter-robuust — zie hierboven'}")

    OUT_PATH.write_text(json.dumps({
        "gegenereerd": datetime.datetime.now().isoformat(timespec="seconds"),
        "drempel": args.drempel,
        "leave_one_cluster_out": loco_rapport,
        "clusters_met_impact": per_cluster,
        "parameter_sweep": sweep_rapport,
        "top10_robuust": robuust,
    }, ensure_ascii=False, indent=2))
    print(f"\nRapport: {OUT_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
