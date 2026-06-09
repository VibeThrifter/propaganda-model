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

# Aard van het mechanisme (kolom mechanisms.aard; relaties erven 'm). Bepaalt of een instantie
# een echt dyadisch kanaal is of een emergente systeemeigenschap — en daarmee hoe ze in de
# invloed-wiskunde telt. Zie migrate_add_mechanism_aard.py voor de driedeling.
FIELD_INSTANTIATION = "veld_instantiatie"  # niveau 1: dyade = steekproef uit een veld-regelmaat
FIELD_PROPERTY = "veld_eigenschap"         # niveau 2: geen echte bron; eigenschap ván de node
# 'indirect' is GEEN veld-effect: het is een echt gericht, maar gemedieerd kanaal (A→B via
# tussen-nodes). Het telt hier daarom als gewone gerichte edge — de demping zit al in de
# (lagere) influence-waarde van de relatie. Geen aparte behandeling in build_adjacency nodig;
# het valt vanzelf in de 'else' (niet FIELD_PROPERTY, niet FIELD_INSTANTIATION). Alleen de viz
# tekent het anders (gestippelde achtergrondpijl mét punt). Zie migrate_add_indirect_aard.py.

# Hoe veld-effecten meetellen in de centraliteit:
#   'full'     — alles op volle sterkte (legacy/pad-tracering; negeert aard).
#   'collapse' — eerlijk "met veld": veld-eigenschap (niveau 2) telt niet als uitgaande invloed;
#                een veld-instantiatie (niveau 1) telt als ÉÉN gedempte bijdrage per bron — de
#                fan-out wordt door k gedeeld i.p.v. N losse duwen op te tellen.
#   'exclude'  — schone dyadische graaf: niveau 1 én 2 volledig weggelaten.
FIELD_MODES = ("full", "collapse", "exclude")

# Publieksgerichte eindstations (instantiemodel): de uitlaten die de nieuwsconsument direct
# bereiken. Persbureaus (ANP) staan hier NIET tussen — die voeden uitlaten, het publiek leest
# ze niet rechtstreeks. In het theoriemodel is er één expliciet doel: de rol 'publiek'.
PUBLIC_TYPES = frozenset({"mediaorganisatie", "omroep", "platform"})

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

def build_adjacency(relations, field_mode: str = "full"):
    """Bouw adjacency ``{node: [(doel, gewicht, relatietype), ...]}`` uit relatie-rijen.

    ``relations`` is een iterable van dicts/mappings met ten minste ``source_id``,
    ``target_id``, ``influence`` en ``relation_type``; optioneel ``aard`` en ``mechanism_id``
    (ontbreken → 'direct'). Uitgesloten types (oppositie) worden overgeslagen; symmetrische
    types krijgen een edge in beide richtingen.

    ``field_mode`` (zie ``FIELD_MODES``) bepaalt hoe emergente veld-effecten meetellen:
      - 'full'     : aard genegeerd, alles op volle sterkte.
      - 'collapse' : veld-eigenschap (niveau 2) telt niet als uitgaande invloed; een
                     veld-instantiatie (niveau 1) telt als één gedempte bijdrage — het gewicht
                     wordt gedeeld door de fan-out k per (bron, mechanisme).
      - 'exclude'  : niveau 1 én 2 volledig weggelaten (schone dyadische graaf).
    """
    relations = list(relations)
    # Fan-out per (bron, mechanisme) tellen voor veld-instantiaties (alleen bij 'collapse').
    fanout: dict = defaultdict(int)
    if field_mode == "collapse":
        for r in relations:
            if r.get("aard") == FIELD_INSTANTIATION and edge_direction(r["relation_type"]) != "excluded":
                if float(r["influence"] or 0.0) > 0:
                    fanout[(r["source_id"], r.get("mechanism_id"))] += 1

    adj: dict = defaultdict(list)
    for r in relations:
        rt = r["relation_type"]
        direction = edge_direction(rt)
        if direction == "excluded":
            continue
        aard = r.get("aard", "direct") if field_mode != "full" else "direct"
        if aard == FIELD_PROPERTY:
            continue  # node-eigenschap (zelfcensuur e.d.): geen uitgaande invloed
        if aard == FIELD_INSTANTIATION and field_mode == "exclude":
            continue  # schone dyadische graaf
        w = float(r["influence"] or 0.0)
        if w <= 0:
            continue
        if aard == FIELD_INSTANTIATION:  # collapse: één diffuse bijdrage i.p.v. N
            k = fanout.get((r["source_id"], r.get("mechanism_id")), 1) or 1
            w = w / k
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

def _centrality(node_ids, adj, max_hops: int = MAX_HOPS, prune: float = PRUNE,
                target_sets=None) -> dict:
    """Bereken centraliteit voor een set nodes over een adjacency ``{node: [(to, w, *), ...]}``.

    Retourneert ``{id: {direct, transitive, reach, *_norm, rank, ...}}``. ``*_norm`` is op het
    maximum geschaald (0..1); ``rank`` is de positie op transitieve invloed (1 = meeste).

    ``target_sets`` is een optioneel dict ``{naam: {'ids': set, 'self': bool}}``. Voor elke
    doelverzameling wordt ``<naam>`` berekend: de invloed die uiteindelijk bij die doelen
    terechtkomt = som van het beste-pad-product naar elke bereikte node in ``ids``. Met
    ``'self': True`` telt een node die zelf een eindstation is +1.0 mee (eigen directe levering
    aan dat publiek). Levert dan ook ``<naam>_norm`` en ``<naam>_rank``.
    """
    target_sets = target_sets or {}
    out: dict = {}
    for n in node_ids:
        reach = transitive_reach(adj, n, max_hops=max_hops, prune=prune)
        rec = {
            "direct": round(direct_strength(adj, n), 4),
            "transitive": round(sum(reach.values()), 4),
            "reach": len(reach),
        }
        for name, spec in target_sets.items():
            ids = spec["ids"]
            s = sum(v for nid, v in reach.items() if nid in ids)
            if spec.get("self") and n in ids:
                s += 1.0
            rec[name] = round(s, 4)
        out[n] = rec

    max_direct = max((v["direct"] for v in out.values()), default=0.0) or 1.0
    max_trans = max((v["transitive"] for v in out.values()), default=0.0) or 1.0
    for v in out.values():
        v["direct_norm"] = round(v["direct"] / max_direct, 4)
        v["transitive_norm"] = round(v["transitive"] / max_trans, 4)
    for rank, n in enumerate(
            sorted(out, key=lambda e: out[e]["transitive"], reverse=True), start=1):
        out[n]["rank"] = rank

    for name in target_sets:
        mx = max((v[name] for v in out.values()), default=0.0) or 1.0
        for v in out.values():
            v[name + "_norm"] = round(v[name] / mx, 4)
        for rank, n in enumerate(
                sorted(out, key=lambda e: out[e][name], reverse=True), start=1):
            out[n][name + "_rank"] = rank

    return out


def compute_influence(conn, max_hops: int = MAX_HOPS, prune: float = PRUNE,
                      field_mode: str = "collapse") -> dict:
    """Invloed-centraliteit per ENTITEIT (instantiemodel) uit een SQLite-connectie.

    Gerichte gewogen graaf bron→doel met gewicht = relatie-``influence`` en de richtingsregels
    uit ``build_adjacency``. ``field_mode`` regelt hoe emergente veld-effecten meetellen (zie
    ``FIELD_MODES``); standaard 'collapse' = eerlijk met veld, fan-out gedempt. Geïsoleerde
    entiteiten krijgen nullen.
    """
    rows = conn.execute("SELECT id, type FROM entities").fetchall()
    entity_ids = [r[0] for r in rows]
    public_ids = {r[0] for r in rows if r[1] in PUBLIC_TYPES}
    # De politiek als doelwit: individuele politici worden in de data vooral als BRON
    # gemodelleerd (draaideur ván politicus); de invloed landt op de partijen. Daarom
    # politici-personen ∪ partij-entiteiten.
    politiek_ids = {r[0] for r in conn.execute(
        "SELECT e.id FROM entities e JOIN roles r ON e.primary_role_id = r.id "
        "WHERE r.name = 'politicus'")}
    politiek_ids |= {r[0] for r in rows if r[1] == "partij"}

    relations = [
        {"source_id": s, "target_id": t, "influence": inf, "relation_type": rt,
         "mechanism_id": mid, "aard": aard or "direct"}
        for s, t, inf, rt, mid, aard in conn.execute(
            "SELECT r.source_id, r.target_id, r.influence, r.relation_type, r.mechanism_id, "
            "       COALESCE(m.aard, 'direct') "
            "FROM relations r LEFT JOIN mechanisms m ON m.id = r.mechanism_id")
    ]
    adj = build_adjacency(relations, field_mode=field_mode)
    target_sets = {
        # uitlaten leveren zelf direct aan het publiek (+1); de politiek zijn doelen ín de graaf.
        "public": {"ids": public_ids, "self": True},
        "politiek": {"ids": politiek_ids, "self": False},
    }
    return _centrality(entity_ids, adj, max_hops, prune, target_sets=target_sets)


def compute_role_influence(role_ids, mech_edges, target_role_sets=None,
                           max_hops: int = MAX_HOPS, prune: float = PRUNE,
                           field_mode: str = "collapse") -> dict:
    """Invloed-centraliteit per ROL (theoretisch model).

    De rolgraaf: elk mechanisme is een gerichte edge ``bron_rol → doel_rol``. Het gewicht is
    ``THEORY_BASE + THEORY_SPAN * sterkte`` — elk mechanisme is een theoretisch kanaal, en de
    empirische sterkte tilt het op. ``mech_edges`` is een iterable van
    ``(bron_rol_id, doel_rol_id, sterkte[, aard])``; de aanroeper laat tegenmacht-mechanismen
    al weg (tegenkracht, geen pro-elite invloedskanaal).

    ``field_mode`` werkt als bij ``compute_influence``: bij 'collapse'/'exclude' telt een
    veld-eigenschap-mechanisme (niveau 2) niet mee als uitgaande invloed, en bij 'exclude'
    ook een veld-instantiatie (niveau 1) niet. In de rolgraaf is er geen fan-out om te dempen
    (elk mechanisme is één rol→rol-edge), dus 'collapse' en 'full' verschillen alleen in niveau 2.

    ``target_role_sets`` is een dict ``{naam: ids_set}`` met de doel-rollen per maat (typisch
    'public' → rol 'publiek', 'politicus' → rol 'politicus').
    """
    adj: dict = defaultdict(list)
    for edge in mech_edges:
        src, tgt, sterkte = edge[0], edge[1], edge[2]
        aard = edge[3] if len(edge) > 3 else "direct"
        if src is None or tgt is None:
            continue
        if field_mode != "full":
            if aard == FIELD_PROPERTY:
                continue
            if aard == FIELD_INSTANTIATION and field_mode == "exclude":
                continue
        w = THEORY_BASE + THEORY_SPAN * float(sterkte or 0.0)
        adj[src].append((tgt, w, None))
    target_sets = {name: {"ids": set(ids), "self": False}
                   for name, ids in (target_role_sets or {}).items() if ids}
    return _centrality(list(role_ids), adj, max_hops, prune, target_sets=target_sets)


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
