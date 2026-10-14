"""Sociaal-Economische Raad (ser.nl) — samenstelling ophalen en lezen (2026-10-13).

De SER zegt op "Wie zitten er in de SER?" welke werkgevers- en werknemersorganisaties zetels in
de raad hebben, met het aantal zetels. Deze module bewaart die pagina als uitgave
(data/registers/ser/ser_<datum>.html + .sha256) en leest de twee lijsten tot records met een vaste
recordregel ("Sociaal-Economische Raad · Werkgeversorganisaties: VNO-NCW (8 zetels)"): het citaat
in het model, dat scripts/registercheck.py opnieuw uit de bewaarde pagina afleidt.

Personen niet: de pagina met de raadsleden noemt alleen de zittingsperiode van de hele raad
(en die is voorbij), geen datum per persoon. Kroonleden zijn geen organisatie. De pagina noemt
ook geen begin van een zetel: het verband krijgt geen datum (registers_looptijd legt
'register_zonder_datum' vast), nooit de downloaddatum.

Geen schrijfacties op het model (dat doet ser_naar_model.py via de REST-API).
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, download, noemt, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "ser"
URL = "https://www.ser.nl/nl/ser/over-ser/wie-zitten-er-in-de-ser"
MAP = DATA / BRON
TITEL = "Sociaal-Economische Raad, 'Wie zitten er in de SER?' (ser.nl), uitgave {uitgave}"
UITGEVER = "Sociaal-Economische Raad"
SER_OO = "28455002"   # de SER in het register van overheidsorganisaties
GROEPEN = ("Werkgeversorganisaties", "Werknemersorganisaties")


class FormaatFout(Exception):
    """De pagina heeft niet de lijsten die deze lezer verwacht."""


def haal() -> Path:
    vandaag = date.today().isoformat()
    pad = download(URL, MAP / f"ser_{vandaag}.html", timeout=60)
    lees(pad)  # een pagina zonder de lijsten bewaren we niet als uitgave
    (MAP / f"ser_{vandaag}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("ser_????-??-??.html"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"ser_{uitgave}.html"


def _tekst(fragment: str) -> str:
    return schoon(html.unescape(re.sub(r"<[^>]+>", " ", fragment)))


def lees(pad: Path) -> dict:
    """→ {bron, uitgave, sha256, records{sleutel: rec}}. Elk record: groep, org, zetels, regel."""
    bron = pad.read_text(encoding="utf-8")
    uitgave = pad.stem.split("_", 1)[1]
    records = {}
    for groep in GROEPEN:
        m = re.search(rf"<p>\s*{groep}:\s*</p>\s*<ul>(.*?)</ul>", bron, re.S)
        if not m:
            raise FormaatFout(f"de lijst '{groep}' staat niet op de pagina ({pad.name})")
        for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S):
            tekst = _tekst(li)
            z = re.match(r"^(.*?)\s*\((\d+)\s+zetels?\)$", tekst)
            if not z:
                raise FormaatFout(f"onverwachte regel '{tekst}' in '{groep}'")
            org, zetels = z.group(1), int(z.group(2))
            rec = {"sleutel": f"zetels:{sleutel(org)}", "soort": "ser", "groep": groep, "org": org, "zetels": zetels,
                   "regel": f"Sociaal-Economische Raad · {groep}: {tekst}"}
            records[rec["sleutel"]] = rec
    if not records:
        raise FormaatFout(f"geen zetels gevonden in {pad.name}")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad),
            "url": URL, "titel": TITEL.format(uitgave=uitgave), "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    data = lees(pad)
    vast = MAP / f"ser_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != data["sha256"]:
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = data
    return data


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def schrijfwijzen() -> dict[str, str]:
    """Naam op ser.nl → naam in het model, met de hand vastgelegd in koppelingen.json
    ('ser_organisaties'): alleen voor een organisatie die er nieuw bij komt (VCP)."""
    pad = Path(__file__).resolve().parent / "koppelingen.json"
    if not pad.exists():
        return {}
    return {k: v["naam"] for k, v in json.loads(pad.read_text(encoding="utf-8")).get("ser_organisaties", {}).items()
            if not k.startswith("_")}


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Organisatie → SER (lidmaatschap): het doel is de SER (oo:28455002) en de bron is de
    organisatie uit het record, onder haar naam in het model (of een vastgelegde schrijfwijze)."""
    if relatie_type != "lidmaatschap":
        return f"verbandsoort '{relatie_type}' hoort niet bij een SER-zetel"
    ser_eind = [e for e in eindpunten if ("oo", SER_OO) in e["ids"]]
    if not ser_eind:
        return "geen eindpunt is de SER (oo:28455002)"
    ander = [e for e in eindpunten if e is not ser_eind[0]][0]
    namen = [ander["name"]] + [k for k, v in schrijfwijzen().items() if sleutel(v) == sleutel(ander["name"])]
    if not any(noemt(rec["org"], n) or sleutel(n) == sleutel(rec["org"]) for n in namen):
        return f"'{ander['name']}' is niet '{rec['org']}' uit het record {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="SER-samenstelling ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        print(json.dumps({"uitgave": d["uitgave"], "records": [r["regel"] for r in d["records"].values()]},
                         ensure_ascii=False, indent=1))
