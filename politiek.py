#!/usr/bin/env python3
"""Politieke kleurmeter — afgeleide ideologische positie van personen & organisaties.

Filosofie identiek aan de rest van het model: NIETS wordt zelf-gerapporteerd. Een
politieke positie wordt opgebouwd uit GESOURCETE, BETWISTBARE signalen in de
discussieboom — `arguments` met property='politieke_positie'. Een signaal draagt
GEEN zelf-getypt getal: het codeert alleen een RICHTING (pool), property_value
'<as>:<pool>' (bv. 'establishment:anti-establishment', 'economisch:links',
'cultureel:conservatief'). De magnitude is AFGELEID — Σ(gewicht·richting)/(Σgewicht+K),
precies zoals σ in scoring.py: ze ONTSTAAT uit hoeveel gesourcet bewijs zich elke kant
op stapelt (concurrentie × betrouwbaarheid × aantal), niet uit een cijfer dat de
bijdrager kiest. Uitzondering: een EXTERNE METING (CHES) draagt '<as>:meting:<-1..1>'
— dát getal komt uit een peer-reviewed dataset, niet uit een mens, en wint op de as.
Elk signaal draagt een verbatim citaat en is aanvechtbaar met een contradicting reply
(ondergraving) — net als elk ander argument.

Twee lagen:
  • PERSOON — afgeleide positie per as uit haar RICHTING-signalen:
    positie = Σ(gewicht·richting)/(Σgewicht+K_POS), richting ∈ {−1,+1}; gewicht per signaal
    = scoring.argument_force(1.0, status, citaties) = statusfactor × bronfactor (zelfde weging
    als de gewone scores; self-reported `weight` blijft geneutraliseerd). Vertrouwen
    α = Σgewicht/(Σgewicht+K_CONF) is een APARTE maat (dun bewijs → lage α), zodat een
    duidelijke lean al zichtbaar is terwijl de onzekerheid eerlijk blijft.
  • ORGANISATIE — "opgemaakt uit de personen die erin zitten": gewogen gemiddelde
    van de posities van de aangesloten personen (affiliatie-edges persoon→org), met
    gewicht = aard van de band (bestuurder zwaarder dan los personeel) × het vertrouwen
    van die persoon × actualiteit (lopend zwaarder dan beëindigd). Een org krijgt GEEN
    eigen signaal — ze erft de kleur van haar mensen (vandaar 'afgeleid').

Telt in niets anders mee (ASPECT_PROPERTIES sluit politieke_positie uit van de
zekerheidsbalans). `voorgesteld` signalen tellen pas mee na merge; include_voorgesteld
geeft een VOORLOPIGE preview (zoals score_diff), duidelijk als zodanig gelabeld.
"""
from __future__ import annotations
import scoring

ASSEN = ("economisch", "cultureel", "establishment")
# Magnitude en vertrouwen zijn TWEE dingen (zoals scoring.py een puntschatting én een
# interval geeft). De POSITIE krimpt met een kleine prior K_POS — zo wordt een duidelijke,
# eensluidende richting al bij bescheiden bewijs zichtbaar (concurrentie bouwt de magnitude
# op). Het VERTROUWEN α krimpt met de conservatievere K_CONF — dat blijft eerlijk over hoe
# dun het bewijs is (|positie| kan dus groter zijn dan α: "leunt zus, maar onzeker").
K_POS = 1.0   # krimp voor de positie:   pos = Σ(w·richting) / (Σw + K_POS)
K_CONF = 3.0  # krimp voor het vertrouwen: α = Σw / (Σw + K_CONF)
K_MEAS = 0.5  # krimp voor een EXTERNE METING (CHES): één gezaghebbende meting telt al zwaar

# Welke relatietypes laten iemands ideologie de org-kleur informeren, en hoe sterk.
# Een org-kleur komt van wie de org BESTUURT / er lid van is — niet van personeel of
# draaideur-passanten: één (oud-)medewerker zegt niets over de kleur van een grote org
# (dat zou ABN AMRO 'progressief' maken op één ex-bankier). Vandaar alleen governance/
# membership-banden; personeel/draaideur tellen bewust NIET mee in de aggregatie.
AFFIL_GEWICHT = {
    "bestuurder": 1.0, "commissaris": 1.0, "raad_van_toezicht": 1.0,
    "woordvoerder_van": 0.8, "lidmaatschap": 0.7, "adviseur": 0.6,
}
ORG_MIN_LEDEN = 2  # onder dit aantal bekende leden is een org-kleur slechts 'indicatief'


# Pool-namen per as: (− pool, + pool). De −kant is overal de "linkse/buiten"-pool.
POLEN = {
    "economisch": ("links", "rechts"),
    "cultureel": ("progressief", "conservatief"),
    "establishment": ("anti-establishment", "establishment"),
}
# Pool → teken (±1). Een richting-signaal codeert alleen een pool; het teken voedt de
# afleiding. − = eerste pool (links/progressief/anti-establishment), + = tweede pool.
POOL_TEKEN = {a: {POLEN[a][0]: -1.0, POLEN[a][1]: 1.0} for a in POLEN}


def _parse(prop_value):
    """→ (as, soort, waarde). soort='richting' (waarde = teken ±1) | 'meting' (waarde =
    float −1..1). Een richting-signaal draagt alleen een pool; de magnitude wordt afgeleid.
    Legacy '<as>:<float>' wordt als richting (teken) gelezen — de magnitude was zelf-
    gerapporteerd en telt dus NIET mee (alleen het teken overleeft)."""
    as_, _, rest = (prop_value or "").partition(":")
    if rest.startswith("meting:"):
        return as_, "meting", float(rest.split(":", 1)[1])
    polen = POOL_TEKEN.get(as_, {})
    if rest in polen:
        return as_, "richting", polen[rest]
    v = float(rest)  # legacy kale float → richting via teken
    return as_, "richting", (1.0 if v > 0 else -1.0 if v < 0 else 0.0)


def _label_as(x, soort):
    """Korte NL-duiding per as. − = eerste pool (links/progressief/anti-establishment),
    + = tweede pool (rechts/conservatief/establishment)."""
    laag, hoog = POLEN[soort]
    if x <= -0.55:  return laag
    if x <= -0.18:  return f"licht {laag}"
    if x <   0.18:  return "centrum"
    if x <   0.55:  return f"licht {hoog}"
    return hoog


def _kleur(econ, cult, est=None):
    """Eén headline-duiding uit de assen (None = as zonder signaal)."""
    delen = []
    if cult is not None: delen.append(_label_as(cult, "cultureel"))
    if econ is not None: delen.append(f"economisch {_label_as(econ, 'economisch')}")
    if est is not None:  delen.append(_label_as(est, "establishment"))
    return " · ".join(delen) if delen else "onbepaald"


def _signaalkracht(status, citaties, preview=False):
    """Gewicht van één signaal = statusfactor × bronfactor (weight geneutraliseerd).

    In preview krijgt een nog-`voorgesteld` signaal voorlopig het post-merge-gewicht
    ('ongecontroleerd'), zodat de meter een indicatie geeft vóór menselijke review;
    zonder preview is voorgesteld = factor 0 (telt in niets, net als de echte scores).
    """
    if preview and status == "voorgesteld":
        status = "ongecontroleerd"
    return scoring.argument_force(1.0, status, citaties)


def compute_kleurmeter(conn, include_voorgesteld: bool = False) -> dict:
    statussen = ("voorgesteld", "ongecontroleerd", "bronvermelding_nodig", "betwist",
                 "geverifieerd", "verouderd") if include_voorgesteld else \
                ("ongecontroleerd", "bronvermelding_nodig", "betwist",
                 "geverifieerd", "verouderd")
    qs = ",".join("?" * len(statussen))

    # Citaties per argument: (reliability, onderwerp) — zoals scoring.source_factor wil.
    cites = {}
    for arg_id, reliability, onderwerp in conn.execute(
            "SELECT c.argument_id, s.reliability, s.onderwerp FROM citations c "
            "JOIN sources s ON s.id = c.source_id"):
        cites.setdefault(arg_id, []).append((reliability, onderwerp))

    # ── Laag 1: EIGEN positie per entiteit (persoon ÓF organisatie) uit eigen signalen ──
    # Elke entiteit kan eigen positie-signalen dragen: een persoon via haar uitspraken,
    # een organisatie (partij/krant/stichting) via haar programma/redactionele lijn/missie —
    # die hoeft niet uit de leden te worden samengevat.
    eigen: dict[int, dict] = {}
    rows = conn.execute(f"""
        SELECT a.id, a.entity_id, a.property_value, a.status, a.claim, e.name, e.type
        FROM arguments a JOIN entities e ON e.id = a.entity_id
        WHERE a.property = 'politieke_positie' AND a.parent_argument_id IS NULL
          AND NOT a.vervangen AND a.status IN ({qs})
        ORDER BY a.entity_id, a.id
    """, statussen)
    for aid, eid, pval, status, claim, naam, etype in rows:
        try:
            as_, soort, waarde = _parse(pval)
        except (ValueError, AttributeError):
            continue
        if as_ not in ASSEN:
            continue
        w = _signaalkracht(status, cites.get(aid, []), preview=include_voorgesteld)
        if w <= 0:
            continue
        e = eigen.setdefault(eid, {"id": eid, "naam": naam, "type": etype,
                                   "assen": {a: {"dir_sw": 0.0, "dir_w": 0.0,
                                                 "meet_sw": 0.0, "meet_w": 0.0, "n": 0}
                                             for a in ASSEN},
                                   "signalen": []})
        ax = e["assen"][as_]
        if soort == "meting":
            ax["meet_sw"] += waarde * w; ax["meet_w"] += w
        else:
            ax["dir_sw"] += waarde * w; ax["dir_w"] += w
        ax["n"] += 1
        pool = None if soort == "meting" else (POLEN[as_][0] if waarde < 0 else POLEN[as_][1])
        e["signalen"].append({"arg_id": aid, "as": as_, "soort": soort, "pool": pool,
                              "meting": round(waarde, 3) if soort == "meting" else None,
                              "gewicht": round(w, 3), "status": status, "claim": claim})

    for e in eigen.values():
        pos, conf, assoort, totw = {}, {}, {}, 0.0
        for a in ASSEN:
            ax = e["assen"][a]
            if ax["meet_w"] > 0:                         # externe meting (CHES) wint op de as
                pos[a] = round(ax["meet_sw"] / ax["meet_w"], 3)   # echte meetwaarde, niet gekrompen
                conf[a] = round(ax["meet_w"] / (ax["meet_w"] + K_MEAS), 3)
                assoort[a] = "meting"; totw += ax["meet_w"]
            elif ax["dir_w"] > 0:                        # afgeleid uit richting-signalen
                pos[a] = round(ax["dir_sw"] / (ax["dir_w"] + K_POS), 3)   # kleine prior: lean zichtbaar
                conf[a] = round(ax["dir_w"] / (ax["dir_w"] + K_CONF), 3)  # conservatief vertrouwen
                assoort[a] = "afgeleid"; totw += ax["dir_w"]
            else:
                pos[a], conf[a], assoort[a] = None, 0.0, None
        e["positie"] = pos
        e["vertrouwen"] = conf
        e["as_soort"] = assoort
        e["n_signalen"] = sum(e["assen"][a]["n"] for a in ASSEN)
        e["kleur"] = _kleur(pos["economisch"], pos["cultureel"], pos["establishment"])
        e["alpha"] = round(totw / (totw + K_CONF), 3)
        del e["assen"]

    # ── Laag 2: AFGELEIDE organisatiepositie uit de leden (elk met hun EIGEN positie) ──
    # Een affiliatie-band is per definitie persoon↔organisatie. De PERSOON-kant kleurt de
    # ORG-kant — en welke rol wie heeft bepalen we op TYPE, niet op source/target: de DB
    # bevat namelijk BEIDE richtingen (persoon→org voor bestuurszetels, maar partij→persoon
    # voor 'lidmaatschap'). Zonder die type-poort werd een partij (mét eigen signalen) als
    # 'lid' gelezen en de persoon als 'org', waardoor personen als organisatie verschenen met
    # de partijkleur. We eisen daarom precies één persoon + één org; persoon↔persoon of
    # org↔org levert geen afleidbare org-kleur en wordt overgeslagen.
    afgeleid: dict[int, dict] = {}
    affil_qs = ",".join("?" * len(AFFIL_GEWICHT))
    aff_rows = conn.execute(f"""
        SELECT r.source_id, es.type, es.name, r.target_id, et.type, et.name,
               r.relation_type, r.active_until
        FROM relations r
        JOIN entities es ON es.id = r.source_id
        JOIN entities et ON et.id = r.target_id
        WHERE r.relation_type IN ({affil_qs}) AND NOT r.vervangen
          AND r.status IN ('goedgekeurd','voorgesteld')
    """, tuple(AFFIL_GEWICHT))
    for sid, stype, sname, tid, ttype, tname, rtype, act_until in aff_rows:
        # Rol op type: de persoon-kant levert de kleur, de org-kant ontvangt 'm.
        if stype == "persoon" and ttype != "persoon":
            pid, oid, org_naam, org_type = sid, tid, tname, ttype
        elif ttype == "persoon" and stype != "persoon":
            pid, oid, org_naam, org_type = tid, sid, sname, stype
        else:
            continue  # persoon↔persoon of org↔org: geen afleidbare org-kleur
        lid = eigen.get(pid)
        if not lid:
            continue  # alleen leden met een eigen positie informeren een org
        recency = 1.0 if not act_until else 0.45
        band = AFFIL_GEWICHT.get(rtype, 0.5)
        for a in ASSEN:
            if lid["positie"][a] is None:
                continue
            g = band * lid["alpha"] * recency
            o = afgeleid.setdefault(oid, {"id": oid, "naam": org_naam, "type": org_type,
                                          "assen": {x: {"sw": 0.0, "w": 0.0} for x in ASSEN},
                                          "leden": {}})
            o["assen"][a]["sw"] += lid["positie"][a] * g
            o["assen"][a]["w"] += g
            o["leden"][pid] = {"naam": lid["naam"], "band": rtype,
                               "kleur": lid["kleur"], "lopend": not act_until}
    for o in afgeleid.values():
        pos, assoort = {}, {}
        for a in ASSEN:
            ax = o["assen"][a]
            pos[a] = round(ax["sw"] / ax["w"], 3) if ax["w"] > 0 else None
            assoort[a] = "afgeleid" if ax["w"] > 0 else None
        o["positie"] = pos
        o["as_soort"] = assoort
        o["kleur"] = _kleur(pos["economisch"], pos["cultureel"], pos["establishment"])
        o["n_leden"] = len(o["leden"])
        o["leden"] = list(o["leden"].values())
        del o["assen"]

    # ── Output: personen (type persoon) en organisaties (eigen ⊕ afgeleid) ──
    personen = [e for e in eigen.values() if e["type"] == "persoon"]
    org_ids = set(afgeleid) | {eid for eid, e in eigen.items() if e["type"] != "persoon"}
    organisaties = []
    for oid in sorted(org_ids):
        eig = eigen.get(oid)          # eigen signalen (partij-programma/redactionele lijn/missie)
        afl = afgeleid.get(oid)       # afgeleid uit de leden
        basis = eig or afl
        # Getoonde positie: eigen signaal heeft voorrang (een partij ís haar programma),
        # anders de leden-afleiding.
        toon = eig if eig else afl
        organisaties.append({
            "id": oid, "naam": basis["naam"], "type": basis["type"],
            "positie": toon["positie"], "kleur": toon["kleur"],
            "bron": "eigen" if eig else "afgeleid",
            # 'bepaald' = eigen bewijs, óf genoeg bekende leden voor de afleiding
            "genoeg": bool(eig) or (afl is not None and afl["n_leden"] >= ORG_MIN_LEDEN),
            "eigen": {"positie": eig["positie"], "kleur": eig["kleur"], "alpha": eig["alpha"],
                      "as_soort": eig["as_soort"], "n_signalen": eig["n_signalen"],
                      "signalen": eig["signalen"]} if eig else None,
            "afgeleid": {"positie": afl["positie"], "kleur": afl["kleur"],
                         "as_soort": afl["as_soort"], "n_leden": afl["n_leden"],
                         "leden": afl["leden"]} if afl else None,
        })

    return {
        "preview": include_voorgesteld,
        "K": K_CONF,
        "personen": sorted(personen, key=lambda p: p["naam"]),
        "organisaties": sorted(organisaties, key=lambda o: (not o["genoeg"], o["naam"])),
    }


if __name__ == "__main__":  # pragma: no cover — handmatige inspectie
    import sqlite3, json, sys
    from pathlib import Path
    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    res = compute_kleurmeter(conn, include_voorgesteld="--preview" in sys.argv)
    print(json.dumps(res, ensure_ascii=False, indent=2))
