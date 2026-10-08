"""Tweede Kamer (open data, OData v4) — uitgave ophalen en lezen (Uitbreiding C, 2026-10-07).

Haalt voor de zittende Kamerleden op: persoon + fractie (FractieZetelPersoon), lopende
nevenfuncties, loopbaan, reizen betaald door derden en geschenken (sinds GESCHENK_SINDS). Dat
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


def _per_persoon(pad: str, sleutelveld: str, ids: list[str], extra: str = "") -> list[dict]:
    uit = []
    for i in range(0, len(ids), BATCH):
        f = " or ".join(f"{sleutelveld} eq {x}" for x in ids[i:i + BATCH])
        uit += _alles(pad, {"$filter": f"({f}) and Verwijderd eq false{extra}"})
    return uit


def haal() -> Path:
    zetels = _alles("FractieZetelPersoon", {
        "$filter": "TotEnMet eq null and Verwijderd eq false",
        "$select": "Id,Functie,Van,Persoon_Id",
        "$expand": "Persoon($select=Id,Titels,Initialen,Roepnaam,Voornamen,Tussenvoegsel,Achternaam),"
                   "FractieZetel($expand=Fractie($select=Id,NaamNL,Afkorting))"})
    ids = sorted({z["Persoon_Id"] for z in zetels})
    data = {
        "bron": BRON, "opgehaald": date.today().isoformat(), "zetels": zetels,
        "nevenfuncties": _per_persoon("PersoonNevenfunctie", "PersoonId", ids),
        "loopbaan": _per_persoon("PersoonLoopbaan", "Persoon_Id", ids),
        "reizen": _per_persoon("PersoonReis", "Persoon_Id", ids),
        "geschenken": _per_persoon("PersoonGeschenk", "Persoon_Id", ids,
                                   f" and Datum ge {GESCHENK_SINDS}T00:00:00Z"),
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
            verwacht = partij_naam(rec.get("fractie_afkorting") or "") or partij_naam(rec.get("fractie") or "")
            if not verwacht or ander["type"] != "partij" or ander["name"] != verwacht:
                return f"fractie '{rec.get('fractie')}' past niet bij eindpunt #{ander['id']}"
            return None
        if ("oo", "19432") not in ander["ids"]:
            return f"eindpunt #{ander['id']} is niet de Tweede Kamer"
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
