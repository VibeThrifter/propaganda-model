"""Invloedsgraaf: de structurele invloedspositie van entiteiten.

Aparte laag naast ``scoring.py``. Waar ``scoring.py`` de *bewijslast* meet (bestaat een
relatie, hoe geloofwaardig — lokaal per edge/node), meet ``influence.py`` de *topologie*:
hoe ver en hoe sterk de invloed van een entiteit door het netwerk propageert. Pro-elite
bias als een EMERGENTE, structurele positie — geen intentie, geen complot.

De graaf is gericht en gewogen: ``bron --influence--> doel`` betekent "bron oefent invloed
uit op doel". Het gewicht is de ``influence`` (0..1) van de relatie; omdat dat tussen 0 en 1
ligt, *dempt* elke extra stap vanzelf — invloed op afstand telt zwakker (vermenigvuldigen
langs een pad).

Richtingsregels per relatietype (zie ``DIRECTION``):
  - GERICHT  (bron beïnvloedt doel): eigendom, adverteerder, beinvloeding, draaideur,
    financiering, censuur, regulering, cooptatie, bestuurder, personeel, lidmaatschap.
  - SYMMETRISCH (wederzijds): alliantie.
  - UITGESLOTEN: oppositie — dat is *tegenmacht*, een tegengestelde kracht, geen kanaal
    waarlangs pro-elite-invloed propageert. (Telt elders als tegenmacht, niet hier.)

Twee maten per entiteit:
  - ``direct``     : som van uitgaande influence-gewichten (rechtstreekse duwkracht).
  - ``transitive`` : som over alle bereikbare nodes van het *beste-pad* invloedsproduct
                     (gedempte invloed die de entiteit op de rest van het netwerk uitoefent).
  - ``reach``      : aantal nodes dat de entiteit (gedempt) bereikt.
  - ``*_norm``     : op het maximum geschaald (0..1), handig voor node-grootte in de viz.

Alle functies zijn puur en stateless; ``compute_influence(conn)`` aggregeert uit de DB en
wordt gedeeld door ``scoring.compute_all_scores`` (en daarmee de viz en /api/scores) en door
``scripts/analyze_influence.py``.
"""
from __future__ import annotations

import heapq
from collections import defaultdict

# ── Instelbare constanten ────────────────────────────────────

SYMMETRIC_TYPES = frozenset({"alliantie"})
EXCLUDED_TYPES = frozenset({"oppositie"})  # tegenmacht: geen invloedskanaal

MAX_HOPS = 6      # hoe ver invloed propageert voordat we stoppen
PRUNE = 0.01      # paden zwakker dan dit negeren we (demping maakt ze verwaarloosbaar)

# Theorie-laag (rollen + mechanismen): de praktijk-sterkte van een mechanisme is vaak 0
# (literatuur-gebaseerd, nog weinig voorbeelden). Elk mechanisme is echter een theoretisch
# invloedskanaal. Edge-gewicht = THEORY_BASE + THEORY_SPAN * sterkte, zodat de rolgraaf heel
# blijft en empirisch bevestigde kanalen zwaarder wegen. (De viz spiegelt deze formule.)
THEORY_BASE = 0.4
THEORY_SPAN = 0.4


def edge_direction(relation_type: str) -> str:
    """'directed' | 'symmetric' | 'excluded' voor een relatietype."""
    if relation_type in EXCLUDED_TYPES:
        return "excluded"
    if relation_type in SYMMETRIC_TYPES:
        return "symmetric"
    return "directed"


# ── Graafopbouw ──────────────────────────────────────────────

def build_adjacency(relations):
    """Bouw adjacency ``{node: [(doel, gewicht, relatietype), ...]}`` uit relatie-rijen.

    ``relations`` is een iterable van dicts/mappings met ten minste ``source_id``,
    ``target_id``, ``influence`` en ``relation_type``. Uitgesloten types worden overgeslagen;
    symmetrische types krijgen een edge in beide richtingen.
    """
    adj: dict = defaultdict(list)
    for r in relations:
        rt = r["relation_type"]
        direction = edge_direction(rt)
        if direction == "excluded":
            continue
        w = float(r["influence"] or 0.0)
        if w <= 0:
            continue
        s, t = r["source_id"], r["target_id"]
        adj[s].append((t, w, rt))
        if direction == "symmetric":
            adj[t].append((s, w, rt))
    return adj


# ── Maten ────────────────────────────────────────────────────

def direct_strength(adj, node) -> float:
    """Som van de uitgaande influence-gewichten van één node (rechtstreekse duwkracht)."""
    return sum(w for _, w, _ in adj.get(node, []))


def transitive_reach(adj, src, max_hops: int = MAX_HOPS, prune: float = PRUNE) -> dict:
    """Beste-pad invloedsproduct van ``src`` naar elke bereikbare node.

    Geeft ``{node: invloedsproduct}`` (exclusief ``src``). Het product langs een pad is de
    gedempte invloed; we houden per node het *sterkste* pad. Paden onder ``prune`` snoeien we.
    """
    best = {src: 1.0}
    frontier = [(src, 1.0)]
    for _ in range(max_hops):
        nxt: dict = {}
        for node, acc in frontier:
            for tgt, w, _ in adj.get(node, []):
                v = acc * w
                if v > best.get(tgt, 0.0) and v > prune:
                    best[tgt] = v
                    if v > nxt.get(tgt, 0.0):
                        nxt[tgt] = v
        if not nxt:
            break
        frontier = list(nxt.items())
    best.pop(src, None)
    return best


def best_path(adj, src, dst, max_hops: int = MAX_HOPS):
    """Sterkste (max-product) invloedspad van ``src`` naar ``dst``.

    Dijkstra over ``-log(gewicht)`` (max-product = kortste pad in negatieve log-ruimte).
    Geeft ``(product, [node-ids], [(relatietype, gewicht), ...])`` of ``None`` als er geen
    pad is binnen ``max_hops``.
    """
    if src == dst:
        return (1.0, [src], [])
    best_prod = {src: 1.0}
    paths = {src: ([src], [])}
    hops = {src: 0}
    pq = [(-1.0, src)]
    while pq:
        negp, node = heapq.heappop(pq)
        p = -negp
        if node == dst:
            break
        if p < best_prod.get(node, 0.0):
            continue
        if hops[node] >= max_hops:
            continue
        for tgt, w, rt in adj.get(node, []):
            np_ = p * w
            if np_ > best_prod.get(tgt, 0.0):
                best_prod[tgt] = np_
                nodes, steps = paths[node]
                paths[tgt] = (nodes + [tgt], steps + [(rt, w)])
                hops[tgt] = hops[node] + 1
                heapq.heappush(pq, (-np_, tgt))
    if dst not in best_prod:
        return None
    nodes, steps = paths[dst]
    return (best_prod[dst], nodes, steps)


# ── DB-aggregatie ────────────────────────────────────────────

def _centrality(node_ids, adj, max_hops: int = MAX_HOPS, prune: float = PRUNE) -> dict:
    """Bereken centraliteit voor een set nodes over een adjacency ``{node: [(to, w, *), ...]}``.

    Retourneert ``{id: {direct, transitive, reach, direct_norm, transitive_norm, rank}}``.
    ``*_norm`` is op het maximum geschaald (0..1); ``rank`` is de positie op transitieve
    invloed (1 = meeste invloed). Nodes zonder uitgaande invloed krijgen nullen.
    """
    out: dict = {}
    for n in node_ids:
        reach = transitive_reach(adj, n, max_hops=max_hops, prune=prune)
        out[n] = {
            "direct": round(direct_strength(adj, n), 4),
            "transitive": round(sum(reach.values()), 4),
            "reach": len(reach),
        }

    max_direct = max((v["direct"] for v in out.values()), default=0.0) or 1.0
    max_trans = max((v["transitive"] for v in out.values()), default=0.0) or 1.0
    for v in out.values():
        v["direct_norm"] = round(v["direct"] / max_direct, 4)
        v["transitive_norm"] = round(v["transitive"] / max_trans, 4)

    for rank, n in enumerate(
            sorted(out, key=lambda e: out[e]["transitive"], reverse=True), start=1):
        out[n]["rank"] = rank

    return out


def compute_influence(conn, max_hops: int = MAX_HOPS, prune: float = PRUNE) -> dict:
    """Invloed-centraliteit per ENTITEIT (instantiemodel) uit een SQLite-connectie.

    Gerichte gewogen graaf bron→doel met gewicht = relatie-``influence`` en de richtingsregels
    uit ``build_adjacency``. Geïsoleerde entiteiten krijgen nullen.
    """
    relations = [
        {"source_id": s, "target_id": t, "influence": inf, "relation_type": rt}
        for s, t, inf, rt in conn.execute(
            "SELECT source_id, target_id, influence, relation_type FROM relations")
    ]
    adj = build_adjacency(relations)
    entity_ids = [row[0] for row in conn.execute("SELECT id FROM entities")]
    return _centrality(entity_ids, adj, max_hops, prune)


def compute_role_influence(role_ids, mech_edges, max_hops: int = MAX_HOPS,
                           prune: float = PRUNE) -> dict:
    """Invloed-centraliteit per ROL (theoretisch model).

    De rolgraaf: elk mechanisme is een gerichte edge ``bron_rol → doel_rol``. Het gewicht is
    ``THEORY_BASE + THEORY_SPAN * sterkte`` — elk mechanisme is een theoretisch kanaal, en de
    empirische sterkte tilt het op. ``mech_edges`` is een iterable van
    ``(bron_rol_id, doel_rol_id, sterkte)``; de aanroeper laat tegenmacht-mechanismen al weg
    (tegenkracht, geen pro-elite invloedskanaal).
    """
    adj: dict = defaultdict(list)
    for src, tgt, sterkte in mech_edges:
        if src is None or tgt is None:
            continue
        w = THEORY_BASE + THEORY_SPAN * float(sterkte or 0.0)
        adj[src].append((tgt, w, None))
    return _centrality(list(role_ids), adj, max_hops, prune)


# ── CLI-sanity ───────────────────────────────────────────────

def _cli():  # pragma: no cover - handmatige inspectie
    import sqlite3
    from pathlib import Path

    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    names = {i: n for i, n in conn.execute("SELECT id, name FROM entities")}
    inf = compute_influence(conn)
    print("== Top 10 transitieve invloed ==")
    for eid in sorted(inf, key=lambda e: -inf[e]["transitive"])[:10]:
        v = inf[eid]
        print(f"  #{v['rank']:<2} {v['transitive']:6.2f}  (bereik {v['reach']:>3})  {names[eid]}")
    conn.close()


if __name__ == "__main__":
    _cli()
