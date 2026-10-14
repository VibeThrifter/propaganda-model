"""Tweede Kamer (open data, OData v4) — uitgave ophalen en lezen (Uitbreiding C, 2026-10-07).

Haalt voor de zittende Kamerleden op: persoon + fractie (FractieZetelPersoon, met de datum
waarop de fractie actief werd), lopende nevenfuncties, loopbaan, reizen betaald door derden,
geschenken (sinds GESCHENK_SINDS) en hun vaste commissiezetels (CommissieZetelVastPersoon →
CommissieZetel → Commissie, sinds 2026-10-13; een oudere uitgave heeft ze niet). Dat
gaat als één JSON-uitgave naar data/registers/tk/tk_<datum>.json (+ .sha256), zodat elk feit
later deterministisch te controleren is (scripts/registercheck.py), net als het register van
overheidsorganisaties (oo.py). De recordregels hieronder zijn het citaat in het model.

Geen schrijfacties op het model (dat doet tk_naar_model.py via de REST-API).
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, get_json, noemt, partij_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "tk"
API = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0"
URL = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/"
MAP = DATA / BRON
TITEL = "Tweede Kamer der Staten-Generaal, open data (gegevensmagazijn), uitgave {uitgave}"
UITGEVER = "Tweede Kamer der Staten-Generaal"
GESCHENK_SINDS = "2023-11-22"   # begin van de huidige zittingsperiode-reeks: alleen recente geschenken
BATCH = 10                      # de OData-server staat ~100 knopen per filter toe


class FormaatFout(Exception):
    """De uitgave mist velden die deze lezer verwacht."""


def _alles(pad: str, params: dict) -> list[dict]:
    url = f"{API}/{pad}?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="$,'()")
    uit = []
    while url:
        d = get_json(url, timeout=90)
        uit += d.get("value", [])
        url = d.get("@odata.nextLink")
    return uit


def _per_persoon(pad: str, sleutelveld: str, ids: list[str], extra: str = "",
                 expand: str | None = None) -> list[dict]:
    uit = []
    for i in range(0, len(ids), BATCH):
        f = " or ".join(f"{sleutelveld} eq {x}" for x in ids[i:i + BATCH])
        params = {"$filter": f"({f}) and Verwijderd eq false{extra}"}
        if expand:
            params["$expand"] = expand
        uit += _alles(pad, params)
    return uit


def haal() -> Path:
    zetels = _alles("FractieZetelPersoon", {
        "$filter": "TotEnMet eq null and Verwijderd eq false",
        "$select": "Id,Functie,Van,Persoon_Id",
        "$expand": "Persoon($select=Id,Titels,Initialen,Roepnaam,Voornamen,Tussenvoegsel,Achternaam),"
                   "FractieZetel($expand=Fractie($select=Id,NaamNL,Afkorting,DatumActief))"})
    ids = sorted({z["Persoon_Id"] for z in zetels})
    data = {
        "bron": BRON, "opgehaald": date.today().isoformat(), "zetels": zetels,
        "nevenfuncties": _per_persoon("PersoonNevenfunctie", "PersoonId", ids),
        "loopbaan": _per_persoon("PersoonLoopbaan", "Persoon_Id", ids),
        "reizen": _per_persoon("PersoonReis", "Persoon_Id", ids),
        "geschenken": _per_persoon("PersoonGeschenk", "Persoon_Id", ids,
                                   f" and Datum ge {GESCHENK_SINDS}T00:00:00Z"),
        # Vaste commissiezetels die nu lopen (TotEnMet leeg), met de commissie erbij
        "commissies": [c for c in _per_persoon(
            "CommissieZetelVastPersoon", "Persoon_Id", ids, " and TotEnMet eq null",
            expand="CommissieZetel($expand=Commissie($select=Id,Nummer,Afkorting,NaamNL,Soort,"
                   "Inhoudsopgave,DatumActief,DatumInactief))")
            if not (((c.get("CommissieZetel") or {}).get("Commissie") or {}).get("DatumInactief"))],
    }
    MAP.mkdir(parents=True, exist_ok=True)
    pad = MAP / f"tk_{data['opgehaald']}.json"
    pad.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (MAP / f"tk_{data['opgehaald']}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("tk_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"tk_{uitgave}.json"


def _datum(waarde) -> str | None:
    return (waarde or "")[:10] or None


def naam_van(p: dict) -> str:
    """'Ranjith Clemminck', 'Jan de Vries' — roepnaam + tussenvoegsel + achternaam."""
    return schoon(f"{p.get('Roepnaam') or (p.get('Voornamen') or '').split(' ')[0]} "
                  f"{p.get('Tussenvoegsel') or ''} {p.get('Achternaam') or ''}")


def lees(pad: Path) -> dict:
    """→ {bron, uitgave, sha256, personen{id}, records{sleutel: rec}}. Elk record heeft een
    'regel' (het citaat) en 'persoon_id'."""
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    for veld in ("zetels", "nevenfuncties", "loopbaan", "reizen", "geschenken"):
        if veld not in ruw:
            raise FormaatFout(f"veld '{veld}' ontbreekt in {pad.name}")
    uitgave = ruw["opgehaald"]
    personen, records = {}, {}
    for z in ruw["zetels"]:
        p = z["Persoon"]
        fractie = ((z.get("FractieZetel") or {}).get("Fractie") or {})
        persoon = {"id": p["Id"], "naam": naam_van(p), "initialen": p.get("Initialen"),
                   "roepnaam": naam_van(p).split(" ")[0], "tussenvoegsel": schoon(p.get("Tussenvoegsel")),
                   "achternaam": schoon(p.get("Achternaam")),
                   "fractie": fractie.get("NaamNL"), "fractie_afkorting": fractie.get("Afkorting"),
                   "fractie_id": fractie.get("Id"), "fractie_actief": _datum(fractie.get("DatumActief")),
                   "zetel_functie": z.get("Functie"), "van": _datum(z.get("Van"))}
        personen[p["Id"]] = persoon
        rec = {**persoon, "sleutel": f"persoon:{p['Id']}", "persoon_id": p["Id"], "soort": "kamerlid"}
        rec["regel"] = (f"Tweede Kamer · Kamerlid: {persoon['naam']} ({persoon['fractie_afkorting'] or persoon['fractie']})"
                        + (f" (sinds {persoon['van']})" if persoon["van"] else "")
                        + (f" · fractiefunctie: {persoon['zetel_functie']}" if persoon["zetel_functie"] else ""))
        records[rec["sleutel"]] = rec
    for n in ruw["nevenfuncties"]:
        pid = n.get("PersoonId")
        if pid not in personen:
            continue
        rec = {"sleutel": f"nevenfunctie:{n['Id']}", "persoon_id": pid, "soort": "nevenfunctie",
               "omschrijving": schoon(n.get("Omschrijving")), "van": _datum(n.get("PeriodeVan")),
               "tot": _datum(n.get("PeriodeTotEnMet")), "actief": n.get("IsActief"),
               "vergoeding": n.get("VergoedingSoort")}
        rec["regel"] = (f"{personen[pid]['naam']} · nevenfunctie: {rec['omschrijving']}"
                        + (f" (van {rec['van']})" if rec["van"] else "")
                        + (f" (tot {rec['tot']})" if rec["tot"] else "")
                        + (f" · {rec['vergoeding'].lower()}" if rec["vergoeding"] else ""))
        records[rec["sleutel"]] = rec
    for l_ in ruw["loopbaan"]:
        pid = l_.get("Persoon_Id")
        if pid not in personen:
            continue
        rec = {"sleutel": f"loopbaan:{l_['Id']}", "persoon_id": pid, "soort": "loopbaan",
               "functie": schoon(l_.get("Functie")), "werkgever": schoon(l_.get("Werkgever")),
               "van": schoon(l_.get("Van")) or None, "tot": schoon(l_.get("TotEnMet")) or None}
        rec["regel"] = (f"{personen[pid]['naam']} · loopbaan: {rec['functie']}"
                        + (f" bij {rec['werkgever']}" if rec["werkgever"] else "")
                        + f" ({rec['van'] or '?'} – {rec['tot'] or 'heden'})")
        records[rec["sleutel"]] = rec
    for r in ruw["reizen"]:
        pid = r.get("Persoon_Id")
        if pid not in personen:
            continue
        rec = {"sleutel": f"reis:{r['Id']}", "persoon_id": pid, "soort": "reis",
               "bestemming": schoon(r.get("Bestemming")), "doel": schoon(r.get("Doel")),
               "van": _datum(r.get("Van")), "tot": _datum(r.get("TotEnMet")),
               "betaald_door": schoon(r.get("BetaaldDoor"))}
        rec["regel"] = (f"{personen[pid]['naam']} · reis naar {rec['bestemming']} "
                        f"({rec['van'] or '?'} – {rec['tot'] or '?'}) · betaald door: {rec['betaald_door']}")
        records[rec["sleutel"]] = rec
    for g in ruw["geschenken"]:
        pid = g.get("Persoon_Id")
        if pid not in personen:
            continue
        rec = {"sleutel": f"geschenk:{g['Id']}", "persoon_id": pid, "soort": "geschenk",
               "omschrijving": schoon(g.get("Omschrijving")), "datum": _datum(g.get("Datum"))}
        rec["regel"] = f"{personen[pid]['naam']} · geschenk ({rec['datum']}): {rec['omschrijving']}"
        records[rec["sleutel"]] = rec
    # Vaste commissiezetels (sinds de uitgave van 2026-10-13; een oudere uitgave heeft ze niet)
    for c in ruw.get("commissies", []):
        pid = c.get("Persoon_Id")
        commissie = ((c.get("CommissieZetel") or {}).get("Commissie") or {})
        if pid not in personen or not commissie.get("NaamNL"):
            continue
        rec = {"sleutel": f"commissiezetel:{c['Id']}", "persoon_id": pid, "soort": "commissiezetel",
               "commissie": schoon(commissie["NaamNL"]), "commissie_id": commissie.get("Id"),
               "commissie_afkorting": commissie.get("Afkorting"),
               "commissie_soort": schoon(commissie.get("Inhoudsopgave")),
               "commissie_actief": _datum(commissie.get("DatumActief")),
               "functie": schoon(c.get("Functie")), "van": _datum(c.get("Van")),
               "tot": _datum(c.get("TotEnMet"))}
        rec["regel"] = (f"Tweede Kamer · {rec['commissie']} · {rec['functie'] or 'Lid'}: "
                        f"{personen[pid]['naam']}" + (f" (sinds {rec['van']})" if rec["van"] else ""))
        records[rec["sleutel"]] = rec
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad),
            "url": URL, "titel": TITEL.format(uitgave=uitgave), "personen": personen,
            "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    data = lees(pad)
    vast = MAP / f"tk_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != data["sha256"]:
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = data
    return data


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


# Functie in een commissiezetel zoals de open data hem geeft → zoals hij in relations.functie staat
COMMISSIE_FUNCTIES = {"lid": "Lid", "voorzitter": "Voorzitter", "ondervz": "Ondervoorzitter",
                      "ondervoorzitter": "Ondervoorzitter", "plvlid": "Plaatsvervangend lid",
                      "eersteondvztk": "Eerste ondervoorzitter", "tweedeondvztk": "Tweede ondervoorzitter"}
# Welke commissies controleren het bestuur (kamerzetel: "beslist mee … en controleert het bestuur"):
# de vaste, algemene en tijdelijke commissies (ook enquêtes) en twee overige met een
# controletaak. Niet: delegaties en contactgroepen, de Commissie voor de Werkwijze, het Presidium,
# de Kunstcommissie, de geloofsbrieven en de bouwbegeleiding (2026-10-13).
COMMISSIE_SOORTEN = {"Vaste commissies", "Algemene commissies", "Tijdelijke commissies"}
COMMISSIE_EXTRA = {"Commissie voor de Inlichtingen- en Veiligheidsdiensten",
                   "Commissie voor de Verzoekschriften en de Burgerinitiatieven"}
COMMISSIE_NIET = {"Bouwbegeleidingscommissie"}


def controlerende_commissie(rec: dict) -> bool:
    if rec["commissie"] in COMMISSIE_NIET:
        return False
    return rec.get("commissie_soort") in COMMISSIE_SOORTEN or rec["commissie"] in COMMISSIE_EXTRA


def commissie_functie(rec: dict) -> str:
    ruw = rec.get("functie") or "Lid"
    return COMMISSIE_FUNCTIES.get(ruw.lower(), ruw)


def commissie_naam(rec: dict) -> str:
    """Naam van de commissieknoop: de naam uit de open data met '(Tweede Kamer)' erachter, want de
    Eerste Kamer heeft commissies met dezelfde naam ('Vaste commissie voor Financiën')."""
    naam = rec["commissie"]
    return f"{naam[:1].upper()}{naam[1:]} (Tweede Kamer)"


def fractie_partij(rec: dict) -> str | None:
    """De partijknoop van een fractie: een landelijke partij uit de partijtabel, anders de
    fractienaam zelf (een afgesplitste groep als 'Groep Markuszower' of een eenmansfractie als
    'Lid Keijzer' is een eigen fractie, geen bestaande partij)."""
    return (partij_naam(rec.get("fractie_afkorting") or "") or partij_naam(rec.get("fractie") or "")
            or schoon(rec.get("fractie")) or None)


def past_naam(p: dict, naam: str) -> bool:
    """Past een modelnaam bij dit Kamerlid? Een deel van de achternaam (dubbele namen:
    'Yeşilgöz-Zegerius' ~ 'Yeşilgöz') als heel woord, en dezelfde eerste letter vooraan."""
    woorden = sleutel(naam).split()
    delen = [d for d in sleutel(p["achternaam"]).split() if len(d) >= 3] or sleutel(p["achternaam"]).split()
    return bool(woorden) and any(d in woorden for d in delen) and \
        woorden[0][:1] == sleutel(p["roepnaam"])[:1]


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Horen de eindpunten bij dit record? None = ja; anders de reden."""
    persoon = [e for e in eindpunten if ("tk_persoon", rec["persoon_id"]) in e["ids"]]
    if not persoon:
        return f"geen eindpunt is Kamerlid tk_persoon:{rec['persoon_id']}"
    p = data["personen"][rec["persoon_id"]]
    if not past_naam(p, persoon[0]["name"]):
        return f"'{persoon[0]['name']}' past niet bij '{p['naam']}'"
    ander = [e for e in eindpunten if e is not persoon[0]][0]
    if rec["soort"] == "kamerlid":
        if relatie_type == "lidmaatschap":
            verwacht = fractie_partij(rec)
            if not verwacht or ander["type"] != "partij" or ander["name"] != verwacht:
                return f"fractie '{rec.get('fractie')}' past niet bij eindpunt #{ander['id']}"
            return None
        if ("oo", "19432") not in ander["ids"]:
            return f"eindpunt #{ander['id']} is niet de Tweede Kamer"
        return None
    if rec["soort"] == "commissiezetel":
        if ander["type"] != "overheidsinstelling" or ander["name"] != commissie_naam(rec):
            return f"eindpunt #{ander['id']} is niet de {rec['commissie']}"
        return None
    # nevenfunctie, loopbaan, reis, geschenk: de organisatie moet in het record genoemd zijn, onder
    # haar naam in het model of een vastgelegde schrijfwijze uit de Kamerregisters
    namen = [ander["name"]] + [v for v, m in schrijfwijzen().items() if sleutel(m) == sleutel(ander["name"])]
    if not any(noemt(rec["regel"], n) for n in namen):
        return f"'{ander['name']}' staat niet in het record {sleutel_r}"
    return None


def schrijfwijzen() -> dict[str, str]:
    """Schrijfwijze in de Kamerregisters → naam in het model, met de hand vastgelegd in
    koppelingen.json ('tk_namen'), bv. 'Toqueville stichting' → 'Tocqueville Stichting'."""
    pad = Path(__file__).resolve().parent / "koppelingen.json"
    if not pad.exists():
        return {}
    return {k: v for k, v in json.loads(pad.read_text(encoding="utf-8")).get("tk_namen", {}).items()
            if not k.startswith("_")}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Tweede Kamer-uitgave ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        soorten = {}
        for r in d["records"].values():
            soorten[r["soort"]] = soorten.get(r["soort"], 0) + 1
        print(json.dumps({"uitgave": d["uitgave"], "personen": len(d["personen"]), **soorten},
                         ensure_ascii=False))
