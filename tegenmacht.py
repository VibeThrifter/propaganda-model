#!/usr/bin/env python3
"""Machtsvalentie — tegenmacht als GERICHTE edge-valentie, geen universele categorie.

Filosofie (zie DOCUMENTATIE.md § "Uitbreiding B: Tegenmacht" en het voorstel
VOORSTEL_tegenmacht-als-veld.md): "tegenmacht" is een tweeplaatsig predicaat
`tegenmacht(X, doel)`. In een veld van meerdere machtsblokken dient het tegenwerken
van het ene blok vaak het andere — dezelfde kracht is dan tegelijk tegenmacht én
promacht, afhankelijk van de as. Een universeel "tegenmacht"-stempel op een actor is
daarom een categoriefout; de valentie hangt aan een EDGE relatief aan een benoemd doel.

Net als de kleurmeter (politiek.py) wordt niets zelf-gerapporteerd: de valentie leeft in
GESOURCETE, BETWISTBARE `arguments` met property='machtsvalentie' op een RELATIE of
MECHANISME (een edge). Twee vormen (property_value):

  • 'filter:<eigendom|advertentie|sourcing|flak|ideologie>' — SOORT 1, verantwoording:
    deze edge checkt die filter-machtsconcentratie (de klassieke accountability-tegenmacht:
    borgingsstichting → eigendom, toezichthouder → holdingconcentratie, NVJ → flak).
  • 'as:<economisch|cultureel|establishment>:<opent|sluit>' — SOORT 2, contra-hegemonie:
    deze edge duwt een onderwerp van de sfeer van consensus naar legitieme controverse
    ('opent', contra-hegemoniaal) of verstrakt de consensus ('sluit', pro-hegemoniaal)
    op die as (Hallin 1986). Één edge mag max. één annotatie per as dragen.

De afgeleide magnitude ONTSTAAT uit hoeveel gesourcet bewijs zich per as ophoopt
(Σ(gewicht·teken)/(Σgewicht+K)), precies zoals σ in scoring.py en de positie in
politiek.py — niet uit een getal dat de bijdrager kiest. Het is een APART aspect: het
telt in NIETS mee (ASPECT_PROPERTIES sluit 'machtsvalentie' uit van de zekerheidsbalans)
en voedt geen score — puur een classificatie-/overlay-laag, zoals de kleurmeter.

Reikwijdte: de actor-aggregatie hier loopt over RELATIE-annotaties (de bron-entiteit van
de relatie oefent de valentie uit). Mechanisme-annotaties verschijnen wel in `edges` maar
worden (nog) niet naar een rol-actor geaggregeerd — een theorie-edge heeft geen entiteit.

Overerving (alleen soort 1): een verantwoording-annotatie op een MECHANISME geldt
definitioneel voor al zijn instanties — precies zoals relaties hun `aard` van het
mechanisme erven. Verantwoording is type-niveau (wat het mechanisme ís: een statuut
checkt de eigenaar); opent/sluit is casus-niveau (wat déze concrete edge met de
consensus deed) en erft daarom bewust NIET. Geërfde doelen tellen apart (`n_geerfd`,
niet in `n_annotaties`), zodat de viz eigen signalen van type-overerving kan
onderscheiden. Structuur erf je, effect bewijs je.
"""
from __future__ import annotations
import scoring
from politiek import ASSEN  # dezelfde drie assen als de kleurmeter

FILTER_DOELEN = ("eigendom", "advertentie", "sourcing", "flak", "ideologie")
RICHTINGEN = {"opent": 1.0, "sluit": -1.0}  # opent = contra-hegemoniaal (+), sluit = pro-hegemoniaal (−)
K_VAL = 1.0  # krimp voor de per-as-valentie: pos = Σ(w·teken) / (Σw + K_VAL)


def parse_machtsvalentie(prop_value):
    """→ dict | None. {'soort':'verantwoording','doel':<filter>} of
    {'soort':'contra_hegemonie','as':<as>,'richting':'opent'|'sluit','teken':±1}.
    None bij een ongeldige vorm (poort in server.py + backstop in validation.py)."""
    kind, _, rest = (prop_value or "").strip().partition(":")
    if kind == "filter":
        if rest in FILTER_DOELEN:
            return {"soort": "verantwoording", "doel": rest,
                    "as": None, "richting": None, "teken": 0.0}
        return None
    if kind == "as":
        as_, _, richting = rest.partition(":")
        if as_ in ASSEN and richting in RICHTINGEN:
            return {"soort": "contra_hegemonie", "doel": None, "as": as_,
                    "richting": richting, "teken": RICHTINGEN[richting]}
        return None
    return None


def _signaalkracht(status, citaties, preview=False):
    """Gewicht van één annotatie = statusfactor × bronfactor (weight geneutraliseerd),
    identiek aan de kleurmeter. In preview krijgt een nog-`voorgesteld` annotatie
    voorlopig het post-merge-gewicht."""
    if preview and status == "voorgesteld":
        status = "ongecontroleerd"
    return scoring.argument_force(1.0, status, citaties)


def _duiding(x):
    """NL-duiding van een per-as-valentie in [−1,1]. + = opent (contra-hegemoniaal)."""
    if x >= 0.55:  return "opent sterk"
    if x >= 0.18:  return "opent"
    if x > -0.18:  return "neutraal"
    if x > -0.55:  return "sluit"
    return "sluit sterk"


def _leeg_acc():
    """Een verse valentie-accumulator (voor een actor of één edge)."""
    return {"assen": {a: {"sw": 0.0, "w": 0.0} for a in ASSEN},
            "verantwoording": {}, "n": 0, "geerfd": 0}


def _voeg_toe(acc, mv, w):
    """Tel één gewogen annotatie bij een accumulator op (contra-hegemonie of verantwoording)."""
    acc["n"] += 1
    if mv["soort"] == "contra_hegemonie":
        ax = acc["assen"][mv["as"]]
        ax["sw"] += mv["teken"] * w
        ax["w"] += w
    else:  # verantwoording — tegen welke filter-concentratie
        acc["verantwoording"][mv["doel"]] = round(
            acc["verantwoording"].get(mv["doel"], 0.0) + w, 3)


def _finaliseer(acc):
    """Accumulator → {valentie, duiding, teken, verantwoordt, n_annotaties}.
    `teken` = netto contra-hegemonische richting over alle assen: +1 opent, −1 sluit,
    0 = geen as-signaal of precies in balans (bv. alleen verantwoording). De viz gebruikt
    `teken` om positieve/negatieve edges te selecteren, `valentie` voor de per-as-balken."""
    pos, duiding, netto = {}, {}, 0.0
    for a in ASSEN:
        ax = acc["assen"][a]
        if ax["w"] > 0:
            pos[a] = round(ax["sw"] / (ax["w"] + K_VAL), 3)  # kleine prior: lean zichtbaar
            duiding[a] = _duiding(pos[a])
            netto += ax["sw"]
        else:
            pos[a] = duiding[a] = None
    teken = 1 if netto > 1e-9 else (-1 if netto < -1e-9 else 0)
    return {"valentie": pos, "duiding": duiding, "teken": teken,
            "verantwoordt": sorted(acc["verantwoording"], key=acc["verantwoording"].get,
                                   reverse=True),
            "n_annotaties": acc["n"], "n_geerfd": acc["geerfd"]}


def compute_machtsvalentie(conn, include_voorgesteld: bool = False) -> dict:
    statussen = ("voorgesteld", "ongecontroleerd", "bronvermelding_nodig", "betwist",
                 "geverifieerd", "verouderd") if include_voorgesteld else \
                ("ongecontroleerd", "bronvermelding_nodig", "betwist",
                 "geverifieerd", "verouderd")
    qs = ",".join("?" * len(statussen))

    # Citaties per argument: (reliability, onderwerp) — zoals scoring.source_factor wil.
    cites: dict[int, list] = {}
    for arg_id, reliability, onderwerp in conn.execute(
            "SELECT c.argument_id, s.reliability, s.onderwerp FROM citations c "
            "JOIN sources s ON s.id = c.source_id"):
        cites.setdefault(arg_id, []).append((reliability, onderwerp))

    rows = conn.execute(f"""
        SELECT a.id, a.relation_id, a.mechanism_id, a.property_value, a.status, a.claim
        FROM arguments a
        WHERE a.property = 'machtsvalentie' AND a.parent_argument_id IS NULL
          AND NOT a.vervangen AND a.status IN ({qs})
        ORDER BY a.id
    """, statussen)
    rows = list(rows)

    # Relatie-context (bron-entiteit oefent de valentie uit) voor de geraakte relaties.
    rel_ids = {r[1] for r in rows if r[1]}
    rel_info: dict[int, tuple] = {}
    if rel_ids:
        rq = ",".join("?" * len(rel_ids))
        for rid, sid, sname, stype, tid, tname in conn.execute(f"""
                SELECT r.id, r.source_id, es.name, es.type, r.target_id, et.name
                FROM relations r
                JOIN entities es ON es.id = r.source_id
                JOIN entities et ON et.id = r.target_id
                WHERE r.id IN ({rq})""", tuple(rel_ids)):
            rel_info[rid] = (sid, sname, stype, tid, tname)
    mech_ids = {r[2] for r in rows if r[2]}
    mech_naam: dict[int, str] = {}
    if mech_ids:
        mq = ",".join("?" * len(mech_ids))
        for mid, name in conn.execute(
                f"SELECT id, name FROM mechanisms WHERE id IN ({mq})", tuple(mech_ids)):
            mech_naam[mid] = name

    actoren: dict[int, dict] = {}       # bron-entiteit → accumulator (+ id/naam)
    rel_acc: dict[int, dict] = {}        # relation_id → accumulator (netto edge-valentie)
    mech_acc: dict[int, dict] = {}       # mechanism_id → accumulator (theorie-edge)
    edges: list[dict] = []
    for aid, rel_id, mech_id, pval, status, claim in rows:
        mv = parse_machtsvalentie(pval)
        if not mv:
            continue
        w = _signaalkracht(status, cites.get(aid, []), preview=include_voorgesteld)
        if w <= 0:
            continue

        bron_id = bron_naam = doel_naam = None
        if rel_id and rel_id in rel_info:
            bron_id, bron_naam, _btype, _tid, doel_naam = rel_info[rel_id]
        edges.append({
            "arg_id": aid, "relation_id": rel_id, "mechanism_id": mech_id,
            "mechanisme": mech_naam.get(mech_id), "bron_id": bron_id, "bron": bron_naam,
            "doel_edge": doel_naam, "soort": mv["soort"], "as": mv["as"],
            "richting": mv["richting"], "filter_doel": mv["doel"], "gewicht": round(w, 3),
            "status": status, "claim": claim})

        # Per-edge-aggregatie: één netto valentie per relatie (praktijk) én mechanisme
        # (theorie), zodat de viz positieve/negatieve edges kan selecteren en kleuren.
        if rel_id:
            _voeg_toe(rel_acc.setdefault(rel_id, _leeg_acc()), mv, w)
        if mech_id:
            _voeg_toe(mech_acc.setdefault(mech_id, _leeg_acc()), mv, w)

        # Actor-aggregatie: alleen relatie-annotaties (de bron-entiteit is de actor).
        if bron_id is None:
            continue
        act = actoren.setdefault(bron_id, {"id": bron_id, "naam": bron_naam, **_leeg_acc()})
        _voeg_toe(act, mv, w)

    # Overerving (soort 1 alleen): een verantwoording-annotatie op een mechanisme geldt
    # definitioneel voor al zijn instanties — het patroon van `aard`. Opent/sluit erft
    # bewust niet (casus-niveau). Geërfde doelen tellen in `geerfd`, niet in `n`, zodat
    # eigen signalen en type-overerving uit elkaar te houden zijn.
    erfbaar = {mid: acc["verantwoording"] for mid, acc in mech_acc.items()
               if acc["verantwoording"]}
    if erfbaar:
        eq = ",".join("?" * len(erfbaar))
        for rid, sid, sname, mid in conn.execute(f"""
                SELECT r.id, r.source_id, es.name, r.mechanism_id
                FROM relations r JOIN entities es ON es.id = r.source_id
                WHERE r.mechanism_id IN ({eq}) AND NOT r.vervangen""", tuple(erfbaar)):
            racc = rel_acc.setdefault(rid, _leeg_acc())
            act = actoren.setdefault(sid, {"id": sid, "naam": sname, **_leeg_acc()})
            for doel, w in erfbaar[mid].items():
                for acc in (racc, act):
                    acc["verantwoording"][doel] = round(
                        acc["verantwoording"].get(doel, 0.0) + w, 3)
                    acc["geerfd"] += 1

    for act in actoren.values():
        act.update(_finaliseer(act))
        del act["assen"], act["verantwoording"], act["n"], act["geerfd"]

    return {
        "preview": include_voorgesteld,
        "K": K_VAL,
        "actoren": sorted(actoren.values(), key=lambda a: a["naam"] or ""),
        "relaties": {rid: _finaliseer(a) for rid, a in rel_acc.items()},
        "mechanismen": {mid: _finaliseer(a) for mid, a in mech_acc.items()},
        "edges": edges,
    }


if __name__ == "__main__":  # pragma: no cover — handmatige inspectie
    import sqlite3, json, sys
    from pathlib import Path
    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    res = compute_machtsvalentie(conn, include_voorgesteld="--preview" in sys.argv)
    print(json.dumps(res, ensure_ascii=False, indent=2))
