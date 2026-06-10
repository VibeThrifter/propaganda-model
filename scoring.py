"""Scoringsketen: van discussieboom naar theorie.

Pure, stateless functies die de geloofwaardigheid en sterkte van het model afleiden uit
de onderliggende bewijslast. Geïmporteerd door zowel ``server.py`` (live herberekening) als
``scripts/generate_viz.py`` (statische snapshot in de visualisatie).

De keten kent drie lagen:

  Laag A  bewijskracht per argument        -> argument_force()
  Laag B  afgeleide praktijkscore          -> instance_credibility()   (relatie/entiteit)
  Laag C  theoriescore (rol/mechanisme)    -> theory_scores()          (literatuur + praktijk)

Filosofie: pro-elite bias is een *emergente* eigenschap. Een theoretisch patroon wint aan
geloofwaardigheid naarmate (a) de literatuur het onderbouwt en (b) er meer en beter
onderbouwde concrete voorbeelden onder liggen. Geen enkele losse aanname is een "bewijs";
het geheel telt op.

Alle constanten staan hieronder en zijn bedoeld om bij te stellen.

Naast de bewijslast levert ``compute_all_scores`` ook de *structurele* invloed-centraliteit
per entiteit (uit ``influence.py``) onder de sleutel ``entity_influence`` — geloofwaardigheid
(bewijs) en invloedspositie (topologie) zijn twee losse assen.
"""
from __future__ import annotations

import influence as influence_graph  # repo-root module: invloedsgraaf (topologie naast bewijslast)

# ── Instelbare constanten ────────────────────────────────────

# Hoe betrouwbaar weegt een brontype mee (Wikipedia-achtige hiërarchie).
RELIABILITY_WEIGHT = {
    "academisch": 1.00,            # peer-reviewed, proefschrift
    "primair": 0.95,              # origineel document, dataset, wetgeving
    "institutioneel": 0.85,       # WRR, CPB, ACM, SER
    "kwaliteitsjournalistiek": 0.70,
    "regulier": 0.50,             # dagblad, omroep, ANP
    "opinie": 0.35,               # column, essay
    "grijs": 0.20,                # blog, podcast, social media
    "onbeoordeeld": 0.15,
}
DEFAULT_RELIABILITY = "onbeoordeeld"

# Verificatiestatus van een argument schaalt zijn bewijskracht.
STATUS_FACTOR = {
    "geverifieerd": 1.00,
    "ongecontroleerd": 0.50,
    "bronvermelding_nodig": 0.40,
    "verouderd": 0.40,
    "betwist": 0.25,
}
DEFAULT_STATUS_FACTOR = 0.50

DEFAULT_WEIGHT = 0.50      # argument zonder expliciet gewicht
NO_CITATION_FACTOR = 0.30  # bronfactor-ondergrens als een argument geen citaties heeft

K_INSTANCE = 1.0   # demping voor de afgeleide praktijkscore (laag B)
K_LIT = 1.0        # demping voor de literatuurcomponent (laag C)
K_AGG = 5.0        # volume-verzadiging voor de praktijkaggregatie (laag C)


# ── Laag A: bewijskracht per argument ────────────────────────

def reliability_weight(reliability: str | None) -> float:
    """Gewicht van een brontype; valt terug op 'onbeoordeeld'."""
    return RELIABILITY_WEIGHT.get(reliability or DEFAULT_RELIABILITY, RELIABILITY_WEIGHT[DEFAULT_RELIABILITY])


def source_factor(citation_reliabilities) -> float:
    """Bronfactor van een argument op basis van zijn sterkste citaat.

    Geen citaties -> NO_CITATION_FACTOR. Anders 0.3 + 0.7 * (beste reliabilitygewicht),
    zodat een goed gestaafd argument richting 1.0 gaat en een ongestaafd toch een beetje meetelt.
    """
    weights = [reliability_weight(r) for r in (citation_reliabilities or [])]
    if not weights:
        return NO_CITATION_FACTOR
    return NO_CITATION_FACTOR + (1.0 - NO_CITATION_FACTOR) * max(weights)


def argument_force(weight, status, citation_reliabilities=None) -> float:
    """Bewijskracht van één argument: weight x statusfactor x bronfactor."""
    w = DEFAULT_WEIGHT if weight is None else float(weight)
    s = STATUS_FACTOR.get(status, DEFAULT_STATUS_FACTOR)
    return w * s * source_factor(citation_reliabilities)


# ── Laag B: afgeleide praktijkscore per instantie ────────────

def support_balance(arguments, k: float) -> float | None:
    """steun / (steun + tegen + k) over een lijst argumenten.

    ``arguments`` is een iterable van dicts met ten minste 'stance', 'weight', 'status'
    en optioneel 'citation_reliabilities'. Contextual telt niet mee. Geeft None als er
    geen voor/tegen-argumenten zijn (zodat de aanroeper kan terugvallen op een prior).
    """
    steun = tegen = 0.0
    seen = False
    for a in arguments:
        stance = a.get("stance")
        if stance not in ("supporting", "contradicting"):
            continue
        seen = True
        f = argument_force(a.get("weight"), a.get("status"), a.get("citation_reliabilities"))
        if stance == "supporting":
            steun += f
        else:
            tegen += f
    if not seen:
        return None
    return steun / (steun + tegen + k)


def instance_credibility(arguments, prior_certainty=None) -> float:
    """Afgeleide geloofwaardigheid van een praktijk-instantie (relatie of entiteit).

    Uit de discussieboom; zonder voor/tegen-argumenten valt het terug op de handmatige
    certainty-kolom (prior), of 0.0 als die ontbreekt.
    """
    bal = support_balance(arguments, K_INSTANCE)
    if bal is None:
        return float(prior_certainty) if prior_certainty is not None else 0.0
    return bal


# ── Laag C: theoriescore per rol/mechanisme ──────────────────

def _noisy_or(a: float, b: float) -> float:
    """Twee onafhankelijke bewijslijnen versterken elkaar, verzadigend naar 1."""
    return 1.0 - (1.0 - a) * (1.0 - b)


def theory_scores(literature_arguments, instances) -> dict:
    """Geloofwaardigheid en sterkte van een theoretisch element (rol/mechanisme).

    literature_arguments : argumenten die direct op het theorie-element hangen (top-down).
    instances            : lijst dicts met 'exemplarity', 'certainty' (afgeleide praktijkscore
                           uit laag B) en 'influence' (0..1) per gekoppelde praktijk-instantie.

    Retourneert dict met geloofwaardigheid, sterkte en de losse componenten voor weergave.
    """
    lit = support_balance(literature_arguments, K_LIT) or 0.0

    n_eff = sum(float(i.get("exemplarity", 1.0)) for i in instances)
    if n_eff > 0:
        weighted_cred = sum(float(i.get("exemplarity", 1.0)) * float(i.get("certainty", 0.0)) for i in instances)
        gem_c = weighted_cred / n_eff
        praktijk = gem_c * (n_eff / (n_eff + K_AGG))
        denom = sum(float(i.get("exemplarity", 1.0)) * float(i.get("certainty", 0.0)) for i in instances)
        if denom > 0:
            sterkte = sum(
                float(i.get("exemplarity", 1.0)) * float(i.get("certainty", 0.0)) * float(i.get("influence", 0.0))
                for i in instances
            ) / denom
        else:
            # Geen geloofwaardige instanties: val terug op exemplariteit-gewogen invloed
            sterkte = sum(float(i.get("exemplarity", 1.0)) * float(i.get("influence", 0.0)) for i in instances) / n_eff
    else:
        praktijk = 0.0
        sterkte = 0.0

    return {
        "geloofwaardigheid": round(_noisy_or(lit, praktijk), 4),
        "sterkte": round(sterkte, 4),
        "literatuur_geloofw": round(lit, 4),
        "praktijk_geloofw": round(praktijk, 4),
        "n_instanties": len(instances),
        "n_bronnen": sum(1 for a in literature_arguments
                         if a.get("stance") in ("supporting", "contradicting")),
    }


# ── DB-aggregatie: alle afgeleide scores in één keer ────────

def compute_all_scores(conn) -> dict:
    """Bereken de volledige scoringsketen uit een SQLite-connectie.

    Retourneert dicts gekeyd op id:
      {'relations': {id: derived_certainty},
       'entities':  {id: derived_certainty},
       'roles':     {id: {geloofwaardigheid, sterkte, ...}},
       'mechanisms':{id: {...}}}

    Gedeeld door scripts/generate_viz.py (statische snapshot) en de /api/scores-endpoint
    (live herberekening), zodat de aggregatielogica op één plek staat.
    """
    # Reliability per argument
    rel_by_arg = {}
    for arg_id, reliability in conn.execute(
            "SELECT c.argument_id, s.reliability FROM citations c JOIN sources s ON c.source_id = s.id"):
        rel_by_arg.setdefault(arg_id, []).append(reliability)

    # Argumenten gegroepeerd per doel
    by_relation, by_entity, by_role, by_mech = {}, {}, {}, {}
    for aid, rel_id, ent_id, role_id, mech_id, prop, stance, weight, status in conn.execute(
            "SELECT id, relation_id, entity_id, role_id, mechanism_id, property, stance, weight, status FROM arguments"):
        payload = {"stance": stance, "weight": weight, "status": status,
                   "citation_reliabilities": rel_by_arg.get(aid, [])}
        if rel_id:
            by_relation.setdefault(rel_id, []).append(payload)
        if ent_id:
            by_entity.setdefault(ent_id, []).append(payload)
        if role_id and prop != "indirecte_invloed_op":
            # Padclaims (property 'indirecte_invloed_op') onderbouwen een afgeleide
            # pijl rol ⇢ rol, niet de rol zelf — buiten de rolscore houden.
            by_role.setdefault(role_id, []).append(payload)
        if mech_id:
            by_mech.setdefault(mech_id, []).append(payload)

    # Laag B: afgeleide praktijkscore per relatie
    rel_rows = conn.execute(
        "SELECT id, source_id, target_id, certainty, influence FROM relations").fetchall()
    rel_certainty, rel_influence = {}, {}
    ent_cert_acc, ent_infl_acc = {}, {}
    for rid, src, tgt, certainty, influence in rel_rows:
        dc = instance_credibility(by_relation.get(rid, []), prior_certainty=certainty)
        rel_certainty[rid] = dc
        rel_influence[rid] = influence or 0.0
        for eid in (src, tgt):
            ent_cert_acc.setdefault(eid, []).append(dc)
            ent_infl_acc.setdefault(eid, []).append(influence or 0.0)
    ent_infl = {eid: (sum(v) / len(v) if v else 0.0) for eid, v in ent_infl_acc.items()}

    # Afgeleide geloofwaardigheid per entiteit (prior = gem. zekerheid van haar relaties)
    entity_cred = {}
    for (eid,) in conn.execute("SELECT id FROM entities"):
        rel_cert = ent_cert_acc.get(eid)
        prior = (sum(rel_cert) / len(rel_cert)) if rel_cert else None
        entity_cred[eid] = instance_credibility(by_entity.get(eid, []), prior_certainty=prior)

    # Instanties per klasse uit de koppeltabel
    role_instances, mech_instances = {}, {}
    for role_id, mech_id, ent_id, rel_id, exemplarity in conn.execute(
            "SELECT role_id, mechanism_id, entity_id, relation_id, exemplarity FROM instantiations"):
        ex = exemplarity if exemplarity is not None else 1.0
        if role_id and ent_id:
            role_instances.setdefault(role_id, []).append({
                "exemplarity": ex, "certainty": entity_cred.get(ent_id, 0.0),
                "influence": ent_infl.get(ent_id, 0.0)})
        elif mech_id and rel_id:
            mech_instances.setdefault(mech_id, []).append({
                "exemplarity": ex, "certainty": rel_certainty.get(rel_id, 0.0),
                "influence": rel_influence.get(rel_id, 0.0)})

    roles = {role_id: theory_scores(by_role.get(role_id, []), role_instances.get(role_id, []))
             for (role_id,) in conn.execute("SELECT id FROM roles")}
    mechs = {mech_id: theory_scores(by_mech.get(mech_id, []), mech_instances.get(mech_id, []))
             for (mech_id,) in conn.execute("SELECT id FROM mechanisms")}

    # Structurele invloed-centraliteit (topologie, los van de bewijslast):
    #   - entiteiten: relatiegraaf, gewicht = influence.
    #   - rollen: mechanismegraaf, gewicht = sterkte van het mechanisme (theorie-laag).
    # Twee varianten: 'clean' (exclude) = schone dyadische graaf (default-view in de viz, toggle
    # uit); 'collapse' = eerlijk met veld-effecten, fan-out gedempt (toggle aan, en de API-default).
    entity_influence = influence_graph.compute_influence(conn, field_mode="collapse")
    entity_influence_clean = influence_graph.compute_influence(conn, field_mode="exclude")

    role_ids = [r[0] for r in conn.execute("SELECT id FROM roles")]
    mech_edges = []
    for mid, src_role, tgt_role, flt, aard in conn.execute(
            "SELECT id, source_role_id, target_role_id, filter, aard FROM mechanisms"):
        if flt == "tegenmacht":     # tegenkracht: geen pro-elite invloedskanaal
            continue
        mech_edges.append((src_role, tgt_role,
                           mechs.get(mid, {}).get("sterkte", 0.0), aard or "direct"))
    def _role_ids(*role_names):
        ids = set()
        for rn in role_names:
            row = conn.execute("SELECT id FROM roles WHERE name = ?", (rn,)).fetchone()
            if row:
                ids.add(row[0])
        return ids

    target_role_sets = {}
    if (pub := _role_ids("publiek")):
        target_role_sets["public"] = pub
    if (pol := _role_ids("politicus", "partij")):
        target_role_sets["politiek"] = pol
    role_influence = influence_graph.compute_role_influence(
        role_ids, mech_edges, target_role_sets=target_role_sets, field_mode="collapse")
    role_influence_clean = influence_graph.compute_role_influence(
        role_ids, mech_edges, target_role_sets=target_role_sets, field_mode="exclude")

    return {
        "relations": {rid: round(c, 4) for rid, c in rel_certainty.items()},
        "entities": {eid: round(c, 4) for eid, c in entity_cred.items()},
        "entity_influence": entity_influence,
        "entity_influence_clean": entity_influence_clean,
        "role_influence": role_influence,
        "role_influence_clean": role_influence_clean,
        "roles": roles,
        "mechanisms": mechs,
    }


# ── CLI-sanity ───────────────────────────────────────────────

def _cli():  # pragma: no cover - handmatige inspectie
    import sqlite3
    from pathlib import Path

    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    def args_for(column, value):
        rows = conn.execute(f"""
            SELECT a.id, a.stance, a.weight, a.status
            FROM arguments a WHERE a.{column} = ?
        """, (value,)).fetchall()
        out = []
        for r in rows:
            rels = [x[0] for x in conn.execute("""
                SELECT s.reliability FROM citations c JOIN sources s ON c.source_id = s.id
                WHERE c.argument_id = ?
            """, (r["id"],)).fetchall()]
            out.append({"stance": r["stance"], "weight": r["weight"],
                        "status": r["status"], "citation_reliabilities": rels})
        return out

    print("== Afgeleide praktijkscore (laag B) voor enkele relaties ==")
    for r in conn.execute("SELECT id, certainty FROM relations LIMIT 5"):
        c = instance_credibility(args_for("relation_id", r["id"]), prior_certainty=r["certainty"])
        print(f"  relatie {r['id']:>4}: handmatig {r['certainty']}  ->  afgeleid {c:.3f}")

    # Theoriescore per mechanisme (praktijk via mechanism_id; literatuur nog leeg pre-migratie)
    print("\n== Theoriescore (laag C) voor top-mechanismen ==")
    rows = conn.execute("""
        SELECT m.id, m.name, COUNT(r.id) n FROM mechanisms m
        JOIN relations r ON r.mechanism_id = m.id
        GROUP BY m.id ORDER BY n DESC LIMIT 5
    """).fetchall()
    for m in rows:
        instances = []
        for r in conn.execute("SELECT id, certainty, influence FROM relations WHERE mechanism_id = ?", (m["id"],)):
            cred = instance_credibility(args_for("relation_id", r["id"]), prior_certainty=r["certainty"])
            instances.append({"exemplarity": 1.0, "certainty": cred, "influence": r["influence"] or 0.0})
        lit = []  # role_id/mechanism_id-doelen bestaan pas na de migratie
        try:
            lit = args_for("mechanism_id", m["id"])
        except sqlite3.OperationalError:
            pass
        s = theory_scores(lit, instances)
        print(f"  {m['name']:<28} n={m['n']:>2}  geloofw={s['geloofwaardigheid']:.3f}  sterkte={s['sterkte']:.3f}")

    conn.close()


if __name__ == "__main__":
    _cli()
