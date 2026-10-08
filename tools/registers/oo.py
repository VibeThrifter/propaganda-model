"""Register van overheidsorganisaties (organisaties.overheid.nl) — uitgave ophalen en lezen.

Uitbreiding C (besluitvorming, eigenaarsbesluit 2026-10-07). De export is open data (dagelijks,
~38 MB XML). Deze module downloadt een uitgave naar data/registers/oo/, legt de sha256 vast en
leest haar in tot records met een vaste **recordregel**: de letterlijke, canonieke weergave
van wat het register over een organisatie of een ambtsdrager zegt. Diezelfde regel staat als
citaat in het model; scripts/registercheck.py leidt haar opnieuw af uit de bewaarde uitgave
en vergelijkt. Verandert de regelvorm, dan moet de registercheck dat dus ook — beide gebruiken
deze module.

Geen schrijfacties op het model (dat doet naar_model.py via de REST-API). Contactgegevens
(adressen, telefoon, e-mail) van medewerkers worden nooit gelezen.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, download, ontleed_naam, partij_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "oo"
URL = "https://organisaties.overheid.nl/archive/exportOO.xml"
NS = "{https://organisaties.overheid.nl/static/schema/oo/export/2.6.13}"
MAP = DATA / BRON
TITEL = "Register van overheidsorganisaties (organisaties.overheid.nl), uitgave {uitgave}"
UITGEVER = "Ministerie van Binnenlandse Zaken en Koninkrijksrelaties (Overheid.nl)"

# Registersoort → bestuurslaag (entities.bestuurslaag)
LAAG = {
    "Ministerie": "rijk", "Organisatieonderdeel": None, "Agentschap": "rijk",
    "Zelfstandig bestuursorgaan": "rijk", "Adviescollege": "rijk", "Inspectie": "rijk",
    "Hoog College van Staat": "rijk", "Rechtspraak": "rijk", "Politie": "rijk",
    "Interdepartementale commissie": "rijk", "Externe commissie": "rijk",
    "Provincie": "provincie", "Gemeente": "gemeente", "Waterschap": "waterschap",
    "Caribisch openbaar lichaam": "caribisch", "Regionaal samenwerkingsorgaan": "regio",
    "Grensoverschrijdend regionaal samenwerkingsorgaan": "regio",
}


class FormaatFout(Exception):
    """De uitgave heeft een andere namespace/versie dan deze lezer kent."""


def _t(el, pad):
    return schoon(el.findtext(NS + pad)) if el is not None else ""


def haal() -> Path:
    """Download de actuele uitgave naar data/registers/oo/exportOO_<datum>.xml (+ .sha256)."""
    tijdelijk = MAP / "exportOO_nieuw.xml"
    download(URL, tijdelijk)
    uitgave = uitgave_van(tijdelijk)
    doel = MAP / f"exportOO_{uitgave}.xml"
    tijdelijk.replace(doel)
    (MAP / f"exportOO_{uitgave}.sha256").write_text(sha256_bestand(doel) + "\n")
    return doel


def uitgave_van(pad: Path) -> str:
    """Datum van de uitgave (YYYY-MM-DD) uit het timestamp-attribuut van het wortelelement."""
    for _evt, el in ET.iterparse(pad, events=("start",)):
        if not el.tag.startswith(NS):
            raise FormaatFout(f"onbekende namespace {el.tag[:80]!r} (verwacht {NS})")
        return (el.get(NS + "timestamp") or "")[:10]
    raise FormaatFout("lege uitgave")


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("exportOO_????-??-??.xml"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"exportOO_{uitgave}.xml"


def regel_org(o: dict) -> str:
    """Canonieke recordregel van een organisatie."""
    delen = [o["naam"] + (f" ({o['afkorting']})" if o.get("afkorting") else ""),
             ", ".join(o["types"]) or "onbekend type"]
    if o.get("ministerie_naam"):
        delen.append(f"relatie met ministerie: {o['ministerie_naam']}")
    if o.get("ouder_naam"):
        delen.append(f"onderdeel van: {o['ouder_naam']}")
    return " · ".join(delen)


def regel_functie(f: dict) -> str:
    """Canonieke recordregel van een ambtsdrager."""
    regel = f"{f['org_pad']} · {f['functie']}: {f['naam_register']}"
    if f.get("start"):
        regel += f" (sinds {f['start']})"
    if f.get("partij"):
        regel += f" · partij: {f['partij']}"
    return regel


def lees(pad: Path) -> dict:
    """Lees een uitgave. → {bron, uitgave, sha256, bestand, organisaties{oo_id: org},
    functies{sleutel: functie}}. Elke org en functie heeft een 'regel' en een 'sleutel'."""
    sha = sha256_bestand(pad)
    root = ET.parse(pad).getroot()
    if not root.tag.startswith(NS):
        raise FormaatFout(f"onbekende namespace {root.tag[:80]!r}")
    uitgave = (root.get(NS + "timestamp") or "")[:10]
    orgs: dict[str, dict] = {}
    functies: dict[str, dict] = {}

    def loop(el, ouder: dict | None, pad_namen: list[str]):
        oo_id = el.get(NS + "systeemId")
        types = [schoon(t.text) for t in el.findall(f"{NS}types/{NS}type") if t.text]
        rel = el.find(NS + "relatieMetMinisterie")
        tooi = None
        for rid in el.findall(f"{NS}identificatiecodes/{NS}resourceIdentifier"):
            if rid.get(NS + "naam") == "Organisatiecode" and rid.text:
                tooi = schoon(rid.text)
        hoofdtype = types[0] if types else ""
        laag = LAAG.get(hoofdtype)
        if laag is None and ouder is not None:
            laag = ouder["bestuurslaag"]
        org = {
            "sleutel": f"org:{oo_id}",
            "oo_id": oo_id,
            "tooi": tooi,
            "naam": _t(el, "naam"),
            "afkorting": _t(el, "afkorting") or None,
            "types": types,
            "bestuurslaag": laag,
            "ministerie_oo": rel.get(NS + "systeemId") if rel is not None else None,
            "ministerie_naam": schoon(rel.text) if rel is not None and rel.text else None,
            "ouder_oo": ouder["oo_id"] if ouder else None,
            "ouder_naam": ouder["naam"] if ouder else None,
            "top_oo": ouder["top_oo"] if ouder else oo_id,
            "start": _t(el, "startDatum") or None,
            "eind": _t(el, "eindDatum") or None,
            "soort_zbo": _t(el, "soortZbo") or None,
            "soort_adviescollege": _t(el, "soortAdviescollege") or None,
            "beschrijving": _t(el, "organisatieBeschrijving/" + NS + "beschrijvingText")[:400] or None,
            "url": f"https://organisaties.overheid.nl/{oo_id}/",
        }
        org["regel"] = regel_org(org)
        orgs[oo_id] = org
        nieuw_pad = pad_namen + [org["naam"]]
        for f in el.findall(f"{NS}functies/{NS}functie"):
            fnaam = _t(f, "naam")
            for m in f.findall(f"{NS}medewerkers/{NS}medewerker"):
                naam = _t(m, "naam")
                if not naam:
                    continue
                rec = {
                    "sleutel": f"fn:{oo_id}:{f.get(NS + 'systeemId')}:{m.get(NS + 'systeemId')}",
                    "oo_id": oo_id,
                    "org_naam": org["naam"],
                    "org_pad": " > ".join(nieuw_pad),
                    "functie": fnaam,
                    "naam_register": naam,
                    "start": _t(m, "startDatum") or None,
                    "eind": _t(m, "eindDatum") or None,
                    "partij": _t(m, "partijLidmaatschap") or None,
                }
                rec["regel"] = regel_functie(rec)
                functies[rec["sleutel"]] = rec
        sub = el.find(NS + "organisaties")
        if sub is not None:
            for kind in sub.findall(NS + "organisatie"):
                loop(kind, org, nieuw_pad)

    for el in root.find(NS + "organisaties").findall(NS + "organisatie"):
        loop(el, None, [])
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha, "bestand": str(pad),
            "url": URL, "titel": TITEL.format(uitgave=uitgave),
            "organisaties": orgs, "functies": functies}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    """Gecachet lezen van een bewaarde uitgave (registercheck); None als ze er niet is."""
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    data = lees(pad)
    vast = MAP / f"exportOO_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != data["sha256"]:
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = data
    return data


def record(uitgave: str, sleutel: str) -> dict | None:
    data = lees_uitgave(uitgave)
    if data is None:
        return None
    if sleutel.startswith("org:"):
        return data["organisaties"].get(sleutel[4:])
    return data["functies"].get(sleutel)


def _fractie(rec: dict) -> str | None:
    delen = (rec.get("org_pad") or "").split(" > ")
    if len(delen) >= 3 and delen[-2].startswith("Fracties"):
        return delen[-1]
    return None


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Horen de eindpunten van een verband bij dit record? None = ja; anders de reden.
    eindpunten: [{id, name, type, ids: {(stelsel, waarde)}}] (bron en doel)."""
    if sleutel_r.startswith("org:"):
        kind = [e for e in eindpunten if ("oo", rec["oo_id"]) in e["ids"]]
        if not kind:
            return f"geen eindpunt draagt externe id oo:{rec['oo_id']}"
        ander = [e for e in eindpunten if e is not kind[0]][0]
        ouders = {rec.get("ministerie_oo"), rec.get("top_oo"), rec.get("ouder_oo")} - {None}
        if not any(("oo", o) in ander["ids"] for o in ouders):
            return f"eindpunt #{ander['id']} is niet het ministerie of de bovenliggende organisatie"
        return None
    medewerker = sleutel_r.rsplit(":", 1)[-1]
    persoon = [e for e in eindpunten if ("oo", f"m:{medewerker}") in e["ids"]]
    if not persoon:
        return f"geen eindpunt is ambtsdrager m:{medewerker}"
    achter = sleutel(ontleed_naam(rec["naam_register"])["achternaam"] or "")
    if achter and achter not in sleutel(persoon[0]["name"]):
        return f"'{persoon[0]['name']}' past niet bij registernaam '{rec['naam_register']}'"
    ander = [e for e in eindpunten if e is not persoon[0]][0]
    if relatie_type == "lidmaatschap":
        partij = rec.get("partij") or _fractie(rec)
        verwacht = partij_naam(partij or "")
        if not verwacht or ander["type"] != "partij" or ander["name"] != verwacht:
            return f"partij '{partij}' past niet bij eindpunt #{ander['id']}"
        return None
    org = data["organisaties"].get(rec["oo_id"]) or {}
    if not any(("oo", o) in ander["ids"] for o in {rec["oo_id"], org.get("top_oo")} if o):
        return f"eindpunt #{ander['id']} is niet de organisatie van {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Register van overheidsorganisaties ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave", help="YYYY-MM-DD (lees); standaard de nieuwste")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        pad = pad_van(a.uitgave) if a.uitgave else uitgaven()[-1]
        d = lees(pad)
        print(json.dumps({"uitgave": d["uitgave"], "sha256": d["sha256"][:16],
                          "organisaties": len(d["organisaties"]),
                          "functies": len(d["functies"])}, ensure_ascii=False))
