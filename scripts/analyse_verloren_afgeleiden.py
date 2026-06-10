#!/usr/bin/env python3
"""
Analyse (wegwerp): welke afgeleide (indirecte) pijlen toonde de ongegatede
cascade vroeger die nu wegvallen door de onderbouwingsdrempel — en op welke
schakel strandt elk pad? Repliceert computeDerivedInfluence uit template.html
op de theorielaag. Schrijft niets naar de DB.
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import scoring  # noqa: E402

THEORY_BASE, THEORY_SPAN = 0.4, 0.4
DERIVED_MIN, GATE, MAX_HOPS = 0.05, 0.10, 6

con = sqlite3.connect(ROOT / "data" / "propaganda_model.db")
con.row_factory = sqlite3.Row
scores = scoring.compute_all_scores(con)
mech_scores = scores["mechanisms"]

roles = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM roles")}
links = []
for m in con.execute("""SELECT id, name, source_role_id s, target_role_id t, filter
                        FROM mechanisms WHERE aard='direct'
                        AND source_role_id IS NOT NULL AND target_role_id IS NOT NULL"""):
    sc = mech_scores.get(m["id"], {})
    if m["filter"] == "tegenmacht":
        continue
    links.append({
        "name": m["name"], "s": m["s"], "t": m["t"],
        "w": THEORY_BASE + THEORY_SPAN * (sc.get("sterkte") or 0),
        "sup": sc.get("geloofwaardigheid") or 0,
    })


def cascade(start, min_sup):
    adj = {}
    for li, l in enumerate(links):
        if l["sup"] < min_sup:
            continue
        adj.setdefault(l["s"], []).append((l["t"], l["w"], l["sup"], li))
    best, supmin, meta = {start: 1.0}, {start: 1.0}, {}
    frontier = [(start, 1.0)]
    for _ in range(MAX_HOPS):
        nxt = {}
        for node, acc in frontier:
            for to, w, sup, li in adj.get(node, []):
                v = acc * w
                if v > best.get(to, 0) and v > DERIVED_MIN:
                    best[to] = v
                    supmin[to] = min(supmin.get(node, 1), sup)
                    meta[to] = (node, li)
                    if v > nxt.get(to, 0):
                        nxt[to] = v
        if not nxt:
            break
        frontier = list(nxt.items())

    def prefix(end):
        path, cur, guard = [end], end, 0
        while cur != start and cur in meta and guard < 20:
            cur = meta[cur][0]
            path.insert(0, cur)
            guard += 1
        return path

    cands = {}
    for u, edges in adj.items():
        if u == start or u not in best:
            continue
        for to, w, sup, li in edges:
            if to == start:
                continue
            val = best[u] * w
            if val < DERIVED_MIN:
                continue
            cands.setdefault(to, []).append((val, u, li))
    out = {}
    for tid, cs in cands.items():
        for val, u, li in sorted(cs, reverse=True):
            p = prefix(u)
            if p[0] != start or tid in p:
                continue
            chain = p + [tid]
            lidx = []
            for k in range(len(p) - 1, 0, -1):
                if p[k] in meta:
                    lidx.insert(0, meta[p[k]][1])
            lidx.append(li)
            hops = [(links[i]["name"], links[i]["sup"]) for i in lidx]
            out[tid] = (val, chain, hops)
            break
    return out


for start in sorted(roles, key=lambda i: roles[i]):
    old = cascade(start, 0.0)
    new = cascade(start, GATE)
    lost = {t: v for t, v in old.items() if t not in new}
    if not lost:
        continue
    print(f"\n== {roles[start]} ==  (nu: {len(new)} pijlen, vroeger: {len(old)})")
    for t, (val, chain, hops) in sorted(lost.items(), key=lambda kv: -kv[1][0]):
        route = " → ".join(roles[c] for c in chain)
        weak = [f"{n} ({s:.0%})" for n, s in hops if s < GATE]
        print(f"  ⇢ {roles[t]:24} {val:.3f}  via {route}")
        print(f"      strandt op: {', '.join(weak) if weak else '?'}")
