#!/usr/bin/env python3
"""Welstandsmeter — afgeleide marketing-/welstandsklasse die een nieuwsoutlet TARGET.

Zusje van de politieke kleurmeter (politiek.py). Filosofie identiek: NIETS wordt
zelf-gerapporteerd. Welke publieksklasse een outlet bedient/aan adverteerders verkoopt
wordt opgebouwd uit GESOURCETE, BETWISTBARE signalen in de discussieboom — `arguments`
met property='doelgroepklasse' op een OUTLET-entiteit. Een signaal draagt GEEN zelf-getypt
getal: het codeert een marketingklasse (property_value '<as>:<klasse>', bv. 'welstand:A'),
en de positie op de as is een BRON-GEWOGEN GEMIDDELDE van de opgegeven/gemeten klassen
(Σ(gewicht·waarde)/Σgewicht). Een klasse-opgave (mediakit) en een EXTERNE METING (een
NOM/NMO-bereikindex, '<as>:meting:<-1..1>') zijn allebei autoritatieve puntschattingen —
géén concurrerende 'lean'; de autoriteit zit in de bronbetrouwbaarheid (die het gewicht
bepaalt), niet in een krimp-prior. Het vertrouwen α blijft wél eerlijk laag bij dun bewijs.

Dit is de operationele brug van `koopkrachtselectie` (#176): adverteerders kopen koopkrachtig
publiek via het marketing-klassensysteem (welstandsklasse A/B1/B2/C/D; sociale klasse; NRS
social grade AB1↔C2DE). De meter maakt per outlet zichtbaar wélke klasse wordt getarget —
hoog (A/AB1, kapitaalkrachtig) tot laag (C/D, minste bestedingsmacht).

Eén ordinale as `welstand`. Klassen → teken: A +1 (hoog) · B1 +0,5 · B2 0 (standaard) ·
C −0,5 · D −1 (laag). Elk signaal draagt een verbatim citaat (mediakit/bereikdata) en is
aanvechtbaar met een contradicting reply (ondergraving), net als elk ander argument.

Telt in NIETS mee (ASPECT_PROPERTIES sluit 'doelgroepklasse' uit van de zekerheidsbalans):
puur een overlay-laag, zoals de kleurmeter. `voorgesteld` signalen tellen pas na merge;
include_voorgesteld geeft een VOORLOPIGE preview (zoals score_diff), duidelijk gelabeld.

v1 leidt per outlet af uit EIGEN signalen. Een groep (bv. DPG) die z'n klasse uit z'n
titels erft (spiegel van politiek's org-uit-leden) is bewust buiten scope gehouden.
"""
from __future__ import annotations
import scoring

AS = "welstand"                       # één ordinale as (hoog ↔ laag)
# Marketingklassen → ordinaal teken op de as. A = kapitaalkrachtige bovenlaag, D = onderkant.
KLASSE_TEKEN = {"A": 1.0, "B1": 0.5, "B2": 0.0, "C": -0.5, "D": -1.0}
KLASSEN = tuple(KLASSE_TEKEN)          # ("A","B1","B2","C","D") — poort in server.py/validation.py

# De positie is een BRON-GEWOGEN GEMIDDELDE van de opgegeven/gemeten klassen (ongekrompen):
# positie = Σ(gewicht·waarde) / Σgewicht. Vertrouwen krimpt wél met een prior — dun bewijs
# (weinig/zwakke bronnen) blijft eerlijk onzeker. K bewust klein (0,7): welstand is few-signal
# van aard (een handvol autoritatieve mediakit-/bereik-opgaven), anders dan de politieke lean
# die uit vele kleine signalen opbouwt — één gezaghebbende opgave telt hier dus al.
K_CONF = 0.7  # krimp voor het vertrouwen α (bleker in de viz):  α = Σw / (Σw + K_CONF)


def _parse(prop_value):
    """→ (as, soort, waarde). soort='klasse' (waarde = ordinaal uit KLASSE_TEKEN) | 'meting'
    (waarde = float −1..1, NOM/NMO-index). BEIDE zijn autoritatieve puntschattingen van de
    getargette klasse — géén concurrerende 'lean' die uit vele signalen opbouwt (zoals de
    politieke as). De afgeleide positie is daarom een BRON-GEWOGEN GEMIDDELDE (ongekrompen);
    autoriteit zit in de bronbetrouwbaarheid, niet in een krimp-prior. Gooit ValueError bij
    een onbruikbare vorm."""
    as_, _, rest = (prop_value or "").partition(":")
    if rest.startswith("meting:"):
        return as_, "meting", float(rest.split(":", 1)[1])
    if rest in KLASSE_TEKEN:
        return as_, "klasse", KLASSE_TEKEN[rest]
    raise ValueError(f"onbruikbare doelgroepklasse: {prop_value!r}")


def _label_klasse(x):
    """Afgeleide positie in [−1,1] → marketingklasse-duiding. + = hoog (A/AB1), − = laag (C/D)."""
    if x >= 0.75:  return "A (kapitaalkrachtig)"
    if x >= 0.25:  return "B1 (hogere middenklasse)"
    if x > -0.25:  return "B2/C (standaard)"
    if x > -0.75:  return "C (praktisch)"
    return "D (onderkant)"


def _signaalkracht(status, citaties, preview=False):
    """Gewicht van één signaal = statusfactor × bronfactor (weight geneutraliseerd),
    identiek aan de kleurmeter. In preview krijgt een nog-`voorgesteld` signaal voorlopig
    het post-merge-gewicht ('ongecontroleerd')."""
    if preview and status == "voorgesteld":
        status = "ongecontroleerd"
    return scoring.argument_force(1.0, status, citaties)


def compute_doelgroepmeter(conn, include_voorgesteld: bool = False) -> dict:
    """Afgeleide welstandsklasse per outlet uit gesourcete `doelgroepklasse`-signalen."""
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

    outlets: dict[int, dict] = {}
    rows = conn.execute(f"""
        SELECT a.id, a.entity_id, a.property_value, a.status, a.claim, e.name, e.type
        FROM arguments a JOIN entities e ON e.id = a.entity_id
        WHERE a.property = 'doelgroepklasse' AND a.parent_argument_id IS NULL
          AND NOT a.vervangen AND a.status IN ({qs})
        ORDER BY a.entity_id, a.id
    """, statussen)
    for aid, eid, pval, status, claim, naam, etype in rows:
        try:
            as_, soort, waarde = _parse(pval)
        except (ValueError, AttributeError):
            continue
        if as_ != AS:
            continue
        w = _signaalkracht(status, cites.get(aid, []), preview=include_voorgesteld)
        if w <= 0:
            continue
        o = outlets.setdefault(eid, {"id": eid, "naam": naam, "type": etype,
                                     "sw": 0.0, "w": 0.0, "n_meting": 0, "signalen": []})
        o["sw"] += waarde * w; o["w"] += w
        if soort == "meting":
            o["n_meting"] += 1; klasse = None
        else:
            klasse = next(k for k, t in KLASSE_TEKEN.items() if t == waarde)
        o["signalen"].append({"arg_id": aid, "klasse": klasse,
                              "meting": round(waarde, 3) if soort == "meting" else None,
                              "soort": soort, "gewicht": round(w, 3),
                              "status": status, "claim": claim})

    for o in outlets.values():
        if o["w"] > 0:                                       # bron-gewogen gemiddelde (ongekrompen)
            o["positie"] = round(o["sw"] / o["w"], 3)
            o["alpha"] = round(o["w"] / (o["w"] + K_CONF), 3)
            # 'meting' = ≥1 externe NOM/NMO-index (viz-badge); anders klasse-opgave (mediakit e.d.).
            o["as_soort"] = "meting" if o["n_meting"] else "opgave"
        else:
            o["positie"] = None; o["alpha"] = 0.0; o["as_soort"] = None
        o["vertrouwen"] = o["alpha"]                          # één vertrouwensmaat (single-axis)
        o["klasse_label"] = _label_klasse(o["positie"]) if o["positie"] is not None else "onbepaald"
        o["n_signalen"] = len(o["signalen"])
        for k in ("sw", "w", "n_meting"):
            del o[k]

    return {
        "preview": include_voorgesteld,
        "K": K_CONF,
        "outlets": sorted(outlets.values(), key=lambda o: o["naam"] or ""),
    }


if __name__ == "__main__":  # pragma: no cover — handmatige inspectie
    import sqlite3, json, sys
    from pathlib import Path
    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    res = compute_doelgroepmeter(conn, include_voorgesteld="--preview" in sys.argv)
    print(json.dumps(res, ensure_ascii=False, indent=2))
