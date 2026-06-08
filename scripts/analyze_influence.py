"""Invloedsanalyse: ranglijsten + pad-tracering over de invloedsgraaf.

Leest ``data/propaganda_model.db`` en gebruikt de gedeelde module ``influence.py``.
Het onderzoeksframe blijft staan: dit meet een *structurele* invloedspositie, geen intentie.

Gebruik:
    # Ranglijsten (directe + transitieve invloed), standaard top 15
    python3 scripts/analyze_influence.py
    python3 scripts/analyze_influence.py --top 25

    # Traceer het sterkste invloedspad van de ene entiteit naar de andere
    # (namen mogen deelstrings zijn, hoofdletterongevoelig)
    python3 scripts/analyze_influence.py --path "Bilderberg" "Volkskrant"
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import influence  # noqa: E402  (repo-root module: invloedsgraaf)

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def load_entities(conn):
    names, types = {}, {}
    for i, n, t in conn.execute("SELECT id, name, type FROM entities"):
        names[i] = n
        types[i] = t
    return names, types


def resolve(conn, names, term):
    """Vind één entiteit-id op basis van een (deel)naam; afbreken bij geen/dubbelzinnig."""
    matches = [i for i, n in names.items() if term.lower() in n.lower()]
    if not matches:
        raise SystemExit(f"FOUT: geen entiteit gevonden voor '{term}'.")
    # Exacte (case-insensitive) match wint van deelstrings
    exact = [i for i in matches if names[i].lower() == term.lower()]
    if exact:
        return exact[0]
    if len(matches) > 1:
        opties = ", ".join(sorted(names[i] for i in matches)[:8])
        raise SystemExit(f"FOUT: '{term}' is dubbelzinnig. Bedoel je: {opties} ...?")
    return matches[0]


def print_rankings(conn, names, types, top):
    # Standaard 'collapse': emergente veld-effecten (mechanisms.aard != direct) tellen gedempt mee —
    # een diffuse fan-out (bv. hegemonische naturalisatie) als één bijdrage i.p.v. N losse duwen,
    # en een veld-eigenschap (zelfcensuur) niet als uitgaande invloed. Zo geen kunstmatige inflatie.
    inf = influence.compute_influence(conn, field_mode="collapse")
    print("\n(invloed-wiskunde: veld-effecten gedempt — zie mechanisms.aard / migrate_add_mechanism_aard.py)")

    print(f"\n== TOP {top} — INVLOED OP HET PUBLIEK (eindstation: kranten/omroepen/platforms) ==")
    print("   De kernvraag: wiens invloed komt uiteindelijk bij de nieuwsconsument terecht?")
    print("   Som van het beste-pad naar elke publieksgerichte uitlaat (uitlaten tellen +1 voor")
    print("   hun eigen directe levering).\n")
    for eid in sorted(inf, key=lambda e: -inf[e].get("public", 0.0))[:top]:
        v = inf[eid]
        print(f"   #{v['public_rank']:<2} {v['public']:6.2f}              "
              f"{names[eid]}  [{types[eid]}]")

    print(f"\n== TOP {top} — TRANSITIEVE invloed (gedempte invloed op heel het netwerk, multi-hop) ==")
    print("   De maat die 'macht via het netwerk' vangt: niet wie zelf het hardst duwt,")
    print("   maar wie knooppunten aanstuurt die de rest aansturen.\n")
    for eid in sorted(inf, key=lambda e: -inf[e]["transitive"])[:top]:
        v = inf[eid]
        print(f"   #{v['rank']:<2} {v['transitive']:6.2f}  bereik {v['reach']:>3}   "
              f"{names[eid]}  [{types[eid]}]")

    print(f"\n== TOP {top} — DIRECTE invloed (som van uitgaande influence-gewichten) ==")
    print("   Rechtstreekse duwkracht: hoeveel en hoe sterk een entiteit direct beïnvloedt.\n")
    ranked_direct = sorted(inf, key=lambda e: -inf[e]["direct"])
    for pos, eid in enumerate(ranked_direct[:top], start=1):
        v = inf[eid]
        print(f"   #{pos:<2} {v['direct']:6.2f}              {names[eid]}  [{types[eid]}]")
    print()


def print_path(conn, names, types, src_term, dst_term):
    src = resolve(conn, names, src_term)
    dst = resolve(conn, names, dst_term)
    relations = [
        {"source_id": s, "target_id": t, "influence": inf, "relation_type": rt}
        for s, t, inf, rt in conn.execute(
            "SELECT source_id, target_id, influence, relation_type FROM relations")
    ]
    adj = influence.build_adjacency(relations)
    result = influence.best_path(adj, src, dst)

    print()
    if not result:
        print(f"   Geen invloedspad gevonden van «{names[src]}» naar «{names[dst]}» "
              f"(binnen {influence.MAX_HOPS} stappen).")
        print("   Dat kan: niet elke actor bereikt elke andere via gerichte invloed.")
        print()
        return
    prod, path, steps = result
    print(f"   STERKSTE INVLOEDSPAD")
    print(f"   «{names[src]}»  ──>  «{names[dst]}»")
    print(f"   Gedempte invloed = {prod:.3f}   ({len(steps)} stap{'pen' if len(steps) != 1 else ''})\n")
    for i, (rt, w) in enumerate(steps):
        a, b = names[path[i]], names[path[i + 1]]
        print(f"     {a}")
        print(f"        │  {rt}  (influence {w})")
        if i == len(steps) - 1:
            print(f"     ▼  {b}")
        else:
            print(f"     ▼")
    print()


def main():
    ap = argparse.ArgumentParser(description="Invloedsanalyse over de propagandamodel-graaf.")
    ap.add_argument("--top", type=int, default=15, help="aantal rijen per ranglijst (default 15)")
    ap.add_argument("--path", nargs=2, metavar=("VAN", "NAAR"),
                    help="traceer het sterkste invloedspad tussen twee entiteiten")
    args = ap.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: {DB_PATH} bestaat niet. Bouw eerst de database.")
    conn = sqlite3.connect(DB_PATH)
    try:
        names, types = load_entities(conn)
        if args.path:
            print_path(conn, names, types, args.path[0], args.path[1])
        else:
            print_rankings(conn, names, types, args.top)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
