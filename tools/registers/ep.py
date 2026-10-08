"""Europees Parlement (open data, API v2) — uitgave ophalen en lezen (Uitbreiding C, 2026-10-07).

Haalt de zittende Nederlandse Europarlementariërs op met hun Europese fractie en hun nationale
partij (data.europarl.europa.eu). Dat gaat als één JSON-uitgave naar
data/registers/ep/ep_<datum>.json (+ .sha256), zodat elk feit later deterministisch te
controleren is (scripts/registercheck.py), net als oo.py en tk.py. De recordregels hieronder zijn
het citaat in het model.

Geen schrijfacties op het model (dat doet ep_naar_model.py via de REST-API).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, get_json, partij_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "ep"
API = "https://data.europarl.europa.eu/api/v2"
URL = "https://data.europarl.europa.eu/api/v2/meps/show-current"
MAP = DATA / BRON
TITEL = "Europees Parlement, open data (zittende leden voor Nederland), uitgave {uitgave}"
UITGEVER = "Europees Parlement"
EP_WIKIDATA = "Q8889"   # het Europees Parlement zelf (externe id van de knoop in het model)
LAND = "NL"


class FormaatFout(Exception):
    """De uitgave mist velden die deze lezer verwacht."""


def _get(pad: str) -> dict:
    teken = "&" if "?" in pad else "?"
    return get_json(f"{API}/{pad}{teken}format=application%2Fld%2Bjson", timeout=90)


def haal() -> Path:
    lijst = [m for m in _get("meps/show-current?offset=0&limit=1000")["data"]
             if m.get("api:country-of-representation") == LAND]
    leden, orgs = [], {}
    for m in lijst:
        detail = _get(f"meps/{m['identifier']}")["data"][0]
        lid = {"id": m["identifier"], "voornaam": detail.get("givenName"), "achternaam": detail.get("familyName"),
               "fractie": m.get("api:political-group"), "lidmaatschappen": []}
        for x in detail.get("hasMembership", []):
            periode = x.get("memberDuring") or {}
            if periode.get("endDate"):
                continue  # alleen wat nu loopt
            if x.get("membershipClassification") == "def/ep-entities/NATIONAL_POLITICAL_GROUP":
                lid["lidmaatschappen"].append({"soort": "partij", "org": x.get("organization"),
                                               "van": periode.get("startDate")})
            elif x.get("role") == "def/ep-roles/MEMBER_PARLIAMENT":
                lid["lidmaatschappen"].append({"soort": "parlement", "org": x.get("organization"),
                                               "van": periode.get("startDate")})
        for org in {lm["org"] for lm in lid["lidmaatschappen"] if lm["soort"] == "partij"} - set(orgs):
            b = _get(f"corporate-bodies/{org.split('/')[-1]}")["data"][0]
            orgs[org] = {"afkorting": b.get("label"),
                         "naam": (b.get("prefLabel") or {}).get("nl") or (b.get("prefLabel") or {}).get("en")}
        leden.append(lid)
    data = {"bron": BRON, "opgehaald": date.today().isoformat(), "leden": leden, "organisaties": orgs}
    MAP.mkdir(parents=True, exist_ok=True)
    pad = MAP / f"ep_{data['opgehaald']}.json"
    pad.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (MAP / f"ep_{data['opgehaald']}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("ep_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"ep_{uitgave}.json"


def nl_naam(voornaam: str, achternaam: str) -> str:
    """'Kim' + 'Van Sparrentak' → 'Kim van Sparrentak' (het EP schrijft tussenvoegsels met een
    hoofdletter; in een Nederlandse naam met voornaam ervoor niet)."""
    achternaam = re.sub(r"\b(Van|De|Der|Den|Ter|Ten|Te|Het|In)\b(?=\s)", lambda m: m.group(1).lower(),
                        schoon(achternaam))
    return schoon(f"{voornaam} {achternaam}")


def lees(pad: Path) -> dict:
    """→ {bron, uitgave, sha256, personen{id}, records{sleutel: rec}}."""
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    for veld in ("leden", "organisaties"):
        if veld not in ruw:
            raise FormaatFout(f"veld '{veld}' ontbreekt in {pad.name}")
    uitgave = ruw["opgehaald"]
    personen, records = {}, {}
    for lid in ruw["leden"]:
        partij = next((lm for lm in lid["lidmaatschappen"] if lm["soort"] == "partij"), None)
        zetel = next((lm for lm in lid["lidmaatschappen"] if lm["soort"] == "parlement"), None)
        org = ruw["organisaties"].get(partij["org"], {}) if partij else {}
        p = {"id": lid["id"], "naam": nl_naam(lid["voornaam"] or "", lid["achternaam"] or ""),
             "roepnaam": schoon(lid["voornaam"]), "achternaam": schoon(lid["achternaam"]),
             "fractie": lid.get("fractie"), "partij": org.get("naam"), "partij_afkorting": org.get("afkorting"),
             "van": (zetel or {}).get("van")}
        personen[lid["id"]] = p
        rec = {**p, "sleutel": f"persoon:{lid['id']}", "persoon_id": lid["id"], "soort": "europarlementarier"}
        rec["regel"] = (f"Europees Parlement · lid voor Nederland: {p['naam']}"
                        + (f" · fractie: {p['fractie']}" if p["fractie"] else "")
                        + (f" · nationale partij: {p['partij']}" if p["partij"] else "")
                        + (f" ({p['partij_afkorting']})" if p["partij_afkorting"] and p["partij_afkorting"] != p["partij"] else "")
                        + (f" (sinds {p['van']})" if p["van"] else ""))
        records[rec["sleutel"]] = rec
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad),
            "url": URL, "titel": TITEL.format(uitgave=uitgave), "personen": personen, "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    data = lees(pad)
    vast = MAP / f"ep_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != data["sha256"]:
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = data
    return data


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def partij_van(p: dict) -> str | None:
    return partij_naam(p.get("partij_afkorting") or "") or partij_naam(p.get("partij") or "")


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Horen de eindpunten bij dit record? None = ja; anders de reden."""
    persoon = [e for e in eindpunten if ("ep_mep", rec["persoon_id"]) in e["ids"]]
    if not persoon:
        return f"geen eindpunt is Europarlementariër ep_mep:{rec['persoon_id']}"
    p = data["personen"][rec["persoon_id"]]
    woorden = sleutel(persoon[0]["name"]).split()
    delen = [d for d in sleutel(p["achternaam"]).split() if len(d) >= 3]
    if not (woorden and any(d in woorden for d in delen) and woorden[0][:1] == sleutel(p["roepnaam"])[:1]):
        return f"'{persoon[0]['name']}' past niet bij '{p['naam']}'"
    ander = [e for e in eindpunten if e is not persoon[0]][0]
    if relatie_type == "lidmaatschap":
        verwacht = partij_van(p)
        if not verwacht or ander["type"] != "partij" or ander["name"] != verwacht:
            return f"partij '{p.get('partij')}' past niet bij eindpunt #{ander['id']}"
        return None
    if ("wikidata", EP_WIKIDATA) not in ander["ids"]:
        return f"eindpunt #{ander['id']} is niet het Europees Parlement"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Europees Parlement-uitgave ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        for p in d["personen"].values():
            print(f"{p['naam']:<40} {p['fractie'] or '':<10} {p['partij'] or ''} → {partij_van(p)}")
        print(json.dumps({"uitgave": d["uitgave"], "leden": len(d["personen"])}, ensure_ascii=False))
