#!/usr/bin/env python3
"""Tijdsvakken: een verband loopt nooit buiten het bestaan van zijn eindpunten.

Eén plek voor de tijdlogica die de viz-data, het partijnetwerk, de validatie en de goedkeurpoort
delen (eigenaarsbesluiten 2026-10-09 "het model kijkt gewoon per tijdsvak wat de relaties zijn"
en 2026-10-13 "zorg goed dat alle tijdsintervallen worden gehandhaafd"):

* **Datums** zijn JJJJ, JJJJ-MM of JJJJ-MM-DD. Vergelijken gebeurt op de gemeenschappelijke
  precisie: '1946' en '1946-02-09' vallen samen, zodat een grovere bron nooit een schijnconflict
  geeft.
* **Bestaan begrenst.** Bij een organisatie is `active_from` de oprichting en `active_until` de
  opheffing of fusie. De effectieve looptijd van een verband is zijn eigen looptijd binnen het
  bestaan van bron en doel. Zo loopt een ongedateerd PvdA-lidmaatschap niet door na 1 juli 2026,
  zonder dat iemand een einddatum hoeft te verzinnen. Opgeslagen wordt daarbij niets.
* **Personen vallen (nog) buiten die grens.** Hun `active_from`/`active_until` staat in het model
  vaak als functieperiode ('sinds 2020 CEO') in plaats van als leven. Als harde grens zou dat hun
  eerdere loopbaan uit het model drukken. De controle PERSOON-LOOPTIJD (validation.py) wijst ze aan.
* **Fusies** zijn opvolging, geen samenvoeging. Een opgeheven organisatie wijst met een gesourcet
  aspect-argument (`property` 'opgegaan_in', `property_value` = id van de opvolger) naar waar ze in
  opging. Haar banden blijven van haar, want dat is wat er gebeurde. Weergaven kunnen ze langs de
  stamboom bij de opvolger tonen (`stamboom`). Samenvoegen (M2.6) is voor dubbele knopen: dat zou
  een PvdA-lidmaatschap uit 1980 tot PRO-lidmaatschap maken.

Puur stdlib en alleen lezend.
"""
from __future__ import annotations

import datetime
import re

DATUM_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

# Aspect-property van een fusie of opheffing: de opgeheven entiteit → de opvolger (entiteit-id).
OPVOLGING_PROPERTY = "opgegaan_in"
# Alleen gemerged en niet betwist werk legt de stamboom vast (zelfde lat als een goedgekeurd verband).
OPVOLGING_STATUSSEN = ("ongecontroleerd", "geverifieerd")


def geldig(d) -> bool:
    return bool(d) and bool(DATUM_RE.match(str(d).strip()))


def _schoon(d):
    d = (str(d).strip() if d is not None else "")
    return d if DATUM_RE.match(d) else None


def voor(a, b) -> bool:
    """Ligt datum a vóór datum b, op hun gemeenschappelijke precisie? ('1945' vóór '1946-02-09'
    wel, '1946' vóór '1946-02-09' niet.) Een lege of ongeldige datum is nooit ergens vóór."""
    a, b = _schoon(a), _schoon(b)
    if not a or not b:
        return False
    n = min(len(a), len(b))
    return a[:n] < b[:n]


def _vroegste(*ds):
    """Vroegste datum; bij gelijkheid op gemeenschappelijke precisie wint de preciezere."""
    best = None
    for d in map(_schoon, ds):
        if d and (best is None or voor(d, best) or (not voor(best, d) and len(d) > len(best))):
            best = d
    return best


def _laatste(*ds):
    best = None
    for d in map(_schoon, ds):
        if d and (best is None or voor(best, d) or (not voor(d, best) and len(d) > len(best))):
            best = d
    return best


def vandaag() -> str:
    return datetime.date.today().isoformat()


def begrenst(entiteit) -> bool:
    """Begrenst het bestaan van deze entiteit haar verbanden? Organisaties wel, personen (nog)
    niet (zie de moduletekst)."""
    return bool(entiteit) and entiteit.get("type") != "persoon"


def bestaan(entiteit):
    """(van, tot) waarbinnen deze entiteit verbanden kan dragen; (None, None) = onbegrensd."""
    if not begrenst(entiteit):
        return None, None
    return _schoon(entiteit.get("active_from")), _schoon(entiteit.get("active_until"))


def effectief(rel, bron, doel):
    """Effectieve looptijd van een verband: zijn eigen looptijd binnen het bestaan van bron en
    doel. → (van, tot, einde_door): einde_door is het id van de entiteit wier einde het verband
    afkapt (None als het verband zelf vroeger eindigt of open blijft)."""
    van = _laatste(rel.get("active_from"), bestaan(bron)[0], bestaan(doel)[0])
    eigen_tot = _schoon(rel.get("active_until"))
    tot, door = eigen_tot, None
    for ent in (bron, doel):
        e_tot = bestaan(ent)[1]
        if e_tot and (tot is None or voor(e_tot, tot)):
            tot, door = e_tot, ent.get("id")
    return van, tot, door


def afgelopen(rel, bron=None, doel=None, peil=None) -> bool:
    """Loopt het verband niet meer? Expliciet inactief, of het (effectieve) einde ligt vóór de
    peildatum (standaard vandaag; een jaar als peil vergelijkt op jaarbasis)."""
    if rel.get("active") in (0, False):
        return True
    tot = effectief(rel, bron, doel)[1] if (bron or doel) else _schoon(rel.get("active_until"))
    return bool(tot) and voor(tot, peil or vandaag())


def overlapt(a_van, a_tot, b_van, b_tot) -> bool:
    """Overlappen twee looptijden? Een open grens overlapt altijd."""
    return not voor(a_tot, b_van) and not voor(b_tot, a_van)


def _naam(ent):
    return (ent or {}).get("name") or (ent or {}).get("naam") or f"#{(ent or {}).get('id')}"


def conflicten(rel, bron, doel, opvolgers_van=None, namen=None) -> list[str]:
    """Waarom de eigen datums van dit verband niet kunnen: begin na einde, of een datum buiten
    het bestaan van een (begrenzend) eindpunt. Alleen wat er staat telt: een open grens is nooit
    een conflict, want de effectieve looptijd kapt die al af. `opvolgers_van` ({id: [opvolger-id]})
    en `namen` ({id: naam}) maken de melding bruikbaar: na een fusie hoort een later verband bij
    de opvolger."""
    van, tot = _schoon(rel.get("active_from")), _schoon(rel.get("active_until"))
    uit = []
    for veld in ("active_from", "active_until"):
        w = rel.get(veld)
        if w not in (None, "") and not _schoon(w):
            uit.append(f"{veld} '{w}' is geen datum (JJJJ, JJJJ-MM of JJJJ-MM-DD)")
    if van and tot and voor(tot, van):
        uit.append(f"het begin ({van}) ligt na het einde ({tot})")
    for ent in (bron, doel):
        e_van, e_tot = bestaan(ent)
        if not (e_van or e_tot):
            continue
        naam = _naam(ent)
        tijd = f"{e_van or '…'}–{e_tot or 'heden'}"
        if van and e_van and voor(van, e_van):
            uit.append(f"begint ({van}) voordat {naam} bestond ({tijd}); hoort het bij een voorganger?")
        elif tot and e_van and voor(tot, e_van):
            uit.append(f"eindigt ({tot}) voordat {naam} bestond ({tijd})")
        if van and e_tot and voor(e_tot, van):
            hint = ""
            opv = (opvolgers_van or {}).get(ent.get("id")) or []
            if opv:
                hint = (f"; {naam} ging op in "
                        + " en ".join((namen or {}).get(o, f"#{o}") for o in opv)
                        + " — koppel het verband daaraan")
            uit.append(f"begint ({van}) nadat {naam} ophield te bestaan ({e_tot}){hint}")
        elif tot and e_tot and voor(e_tot, tot):
            uit.append(f"loopt ({tot}) door na het einde van {naam} ({e_tot})")
    return uit


# ── Fusies en opvolging ─────────────────────────────────────────

def opvolgingen(conn) -> dict:
    """{voorganger_id: [{'opvolger': id, 'argument_id': id}]} uit gemergede, niet-betwiste
    'opgegaan_in'-argumenten tussen goedgekeurde entiteiten. Een gemerged tegenargument met
    dezelfde opvolger schakelt de schakel uit (de discussieboom beslist, niet deze functie)."""
    def rijen(sql, args=()):
        cur = conn.execute(sql, args)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    qs = ",".join("?" * len(OPVOLGING_STATUSSEN))
    try:
        args = rijen(f"""
            SELECT a.id, a.entity_id, a.property_value, a.stance FROM arguments a
            JOIN entities e ON e.id = a.entity_id
            WHERE a.property = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
              AND a.status IN ({qs}) AND e.status = 'goedgekeurd' AND NOT e.vervangen
            ORDER BY a.id""", (OPVOLGING_PROPERTY, *OPVOLGING_STATUSSEN))  # noqa: S608 - vaste SQL
    except Exception:  # noqa: BLE001 - database van vóór de kolom/enum: geen stamboom
        return {}
    levend = {r["id"] for r in rijen(
        "SELECT id FROM entities WHERE status = 'goedgekeurd' AND NOT vervangen")}
    tegen = {(a["entity_id"], str(a["property_value"]).strip())
             for a in args if a["stance"] == "contradicting"}
    uit = {}
    for a in args:
        waarde = str(a["property_value"] or "").strip()
        if a["stance"] != "supporting" or not waarde.isdigit():
            continue
        opv = int(waarde)
        if opv == a["entity_id"] or opv not in levend or (a["entity_id"], waarde) in tegen:
            continue
        lijst = uit.setdefault(a["entity_id"], [])
        if all(x["opvolger"] != opv for x in lijst):
            lijst.append({"opvolger": opv, "argument_id": a["id"]})
    return uit


def stamboom(opv: dict):
    """Uit {voorganger: [opvolgers]} → (hoofd, voorgangers):
    hoofd[id] = de laatste opvolger langs de keten (bij een splitsing de eerste schakel);
    voorgangers[id] = alle (transitieve) voorgangers van id. Een kring wordt genegeerd."""
    def volgende(eid):
        lijst = opv.get(eid) or []
        return lijst[0]["opvolger"] if lijst else None

    hoofd = {}
    for start in opv:
        pad, eid = [start], volgende(start)
        while eid is not None and eid not in pad:
            pad.append(eid)
            eid = volgende(eid)
        if eid is None:                     # geen kring
            hoofd[start] = pad[-1]
    voorgangers = {}
    for eid, h in hoofd.items():
        # Elke schakel tussen eid en het hoofd heeft eid als (transitieve) voorganger.
        nxt = volgende(eid)
        while nxt is not None:
            voorgangers.setdefault(nxt, set()).add(eid)
            if nxt == h:
                break
            nxt = volgende(nxt)
    return hoofd, voorgangers


def kring(opv: dict, voorganger: int, opvolger: int) -> bool:
    """Zou de schakel voorganger → opvolger een kring maken?"""
    gezien, eid = set(), opvolger
    while eid is not None and eid not in gezien:
        if eid == voorganger:
            return True
        gezien.add(eid)
        lijst = opv.get(eid) or []
        eid = lijst[0]["opvolger"] if lijst else None
    return False
