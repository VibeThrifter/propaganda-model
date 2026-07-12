#!/usr/bin/env python3
"""Bereikmeter — gesourcet publieksbereik (kijkers/lezers/invullers) per media-entiteit, per jaar.

Zusje van de welstandsmeter (doelgroep.py). Filosofie identiek: NIETS wordt zelf-
gerapporteerd. Hoeveel publiek een outlet bereikt wordt opgebouwd uit GESOURCETE,
BETWISTBARE signalen in de discussieboom — `arguments` met property='bereik' op een
entiteit. Eén signaal = één cijfer uit één bron: property_value '<maat>:<aantal>:<jaar>'
(bv. 'kijkers:650000:2024'), met een verbatim citaat uit SKO/NMO/NOM-rapport, jaarverslag
of persbericht. Het jaar is verplicht — de tijdreeks is het punt: de viz laat node-grootte
meebewegen met de tijdlijn-slider (DWDD groot in 2010, weg in 2026).

Anders dan welstand/kleur is er geen as en geen gewogen gemiddelde: een bereikcijfer is
een autoritatieve puntopgave; de autoriteit zit in de bron die de reviewer beoordeelt, en
een fout cijfer wordt aangevochten met een ondergraving, net als elk ander argument. Bij
meerdere maten/bronnen in hetzelfde jaar wint per jaar de GROOTSTE publieksmaat (dat is de
weergave-afspraak van de eigenaar: 'grootste beschikbare publieksmaat', juli 2026) — alle
onderliggende signalen blijven per stuk zichtbaar in het detailpaneel.

Telt in NIETS mee (ASPECT_PROPERTIES sluit 'bereik' uit van de zekerheidsbalans): puur een
overlay-laag. `voorgesteld` signalen tellen pas na merge; include_voorgesteld geeft een
VOORLOPIGE preview (zoals score_diff), duidelijk gelabeld.
"""
from __future__ import annotations

# Publieksmaten (weergavelabels in shared_vocab/NAAM_WEERGAVE horen bij de UI-laag).
MATEN = {
    "kijkers": "kijkers (gem. per uitzending)",
    "luisteraars": "luisteraars",
    "oplage": "oplage",
    "bereik_totaal": "totaalbereik print+online",
    "online": "maandbereik online",
    "invullers": "invullers per verkiezing",
    "volgers": "volgers/leden/abonnees",
}

JAAR_MIN, JAAR_MAX = 1800, 2100


def _parse(prop_value):
    """'<maat>:<aantal>:<jaar>' → (maat, aantal, jaar). Gooit ValueError bij een
    onbruikbare vorm — dezelfde poort in server.py (400) en hier (signaal overslaan)."""
    delen = (prop_value or "").split(":")
    if len(delen) != 3:
        raise ValueError(f"onbruikbaar bereik-signaal: {prop_value!r}")
    maat, aantal_s, jaar_s = delen
    if maat not in MATEN:
        raise ValueError(f"onbekende maat: {maat!r} (kies uit {', '.join(MATEN)})")
    aantal = int(aantal_s)
    if aantal <= 0:
        raise ValueError(f"aantal moet positief zijn: {aantal_s!r}")
    if len(jaar_s) != 4 or not jaar_s.isdigit() or not (JAAR_MIN <= int(jaar_s) <= JAAR_MAX):
        raise ValueError(f"jaar moet 4 cijfers zijn ({JAAR_MIN}-{JAAR_MAX}): {jaar_s!r}")
    return maat, aantal, int(jaar_s)


def compute_bereik(conn, include_voorgesteld: bool = False) -> dict:
    """Afgeleid publieksbereik per entiteit uit gesourcete `bereik`-signalen.

    Per entiteit: alle signalen (stuk voor stuk, met status), een jaarreeks
    {jaar → grootste aantal over de maten/bronnen van dat jaar} en het nieuwste punt.
    """
    statussen = ("voorgesteld", "ongecontroleerd", "bronvermelding_nodig", "betwist",
                 "geverifieerd", "verouderd") if include_voorgesteld else \
                ("ongecontroleerd", "bronvermelding_nodig", "betwist",
                 "geverifieerd", "verouderd")
    qs = ",".join("?" * len(statussen))

    entiteiten: dict[int, dict] = {}
    rows = conn.execute(f"""
        SELECT a.id, a.entity_id, a.property_value, a.status, a.claim, e.name, e.type
        FROM arguments a JOIN entities e ON e.id = a.entity_id
        WHERE a.property = 'bereik' AND a.parent_argument_id IS NULL
          AND NOT a.vervangen AND a.status IN ({qs})
        ORDER BY a.entity_id, a.id
    """, statussen)
    for aid, eid, pval, status, claim, naam, etype in rows:
        try:
            maat, aantal, jaar = _parse(pval)
        except (ValueError, AttributeError):
            continue
        o = entiteiten.setdefault(eid, {"id": eid, "naam": naam, "type": etype,
                                        "signalen": [], "reeks": {}})
        o["signalen"].append({"arg_id": aid, "maat": maat, "jaar": jaar,
                              "aantal": aantal, "status": status, "claim": claim})
        # Grootste publieksmaat per jaar (weergave-afspraak; details blijven per signaal).
        if aantal > o["reeks"].get(jaar, 0):
            o["reeks"][jaar] = aantal

    for o in entiteiten.values():
        o["n_signalen"] = len(o["signalen"])
        if o["reeks"]:
            jaar = max(o["reeks"])
            beste = max((s for s in o["signalen"] if s["jaar"] == jaar),
                        key=lambda s: s["aantal"])
            o["nieuwste"] = {"jaar": jaar, "aantal": beste["aantal"], "maat": beste["maat"]}
        else:
            o["nieuwste"] = None

    return {
        "preview": include_voorgesteld,
        "entiteiten": sorted(entiteiten.values(), key=lambda o: o["naam"] or ""),
    }


if __name__ == "__main__":  # pragma: no cover — handmatige inspectie
    import sqlite3, json, sys
    from pathlib import Path
    db = Path(__file__).parent / "data" / "propaganda_model.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    res = compute_bereik(conn, include_voorgesteld="--preview" in sys.argv)
    print(json.dumps(res, ensure_ascii=False, indent=2))
