"""Gebieden in Nederland (CBS, opendata.cbs.nl) — de gemeentelijke indeling ophalen en lezen (2026-10-15).

In welke provincie een gemeente ligt, staat officieel in de CBS-tabel 'Gebieden in Nederland
<jaar>' (de indeling op 1 januari van dat jaar; per gemeente onder meer de provincie). Het
register van overheidsorganisaties noemt bij een gemeente alleen de provincie van een adres,
en dat is geen bestuurlijk gegeven. Deze module bewaart de tabel als uitgave
(data/registers/cbs/cbs_<datum>.json + .sha256: de ruwe tabelinfo, kolomdefinities en rijen
van de OData-API in één bestand) en leest haar tot records met een vaste recordregel
("Gebieden in Nederland 2026 (CBS, tabel 86247NED) · gemeente Druten (GM0225) · provincie
Gelderland (PV25)"): het citaat in het model, dat scripts/registercheck.py opnieuw uit de
bewaarde uitgave afleidt.

De tabel noemt geen begin: het verband krijgt geen datum (registers_looptijd legt
'register_zonder_datum' vast), nooit het jaar van de tabel of de downloaddatum.

Geen schrijfacties op het model (dat doet cbs_naar_model.py via de REST-API).
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, get_json, schoon, sha256_bestand  # noqa: E402

BRON = "cbs"
ODATA = "https://opendata.cbs.nl/ODataApi/odata"
CATALOGUS = "https://opendata.cbs.nl/ODataCatalog/Tables"
MAP = DATA / BRON
TITEL = "CBS, Gebieden in Nederland {jaar} (opendata.cbs.nl, tabel {tabel}), uitgave {uitgave}"
UITGEVER = "Centraal Bureau voor de Statistiek"
TABELTITEL = "Gebieden in Nederland {jaar}"
MIN_GEMEENTEN = 300   # minder gemeenten = een halve download; zo'n uitgave lezen we niet

# CBS-provinciecode → (naam, de provincie in het register van overheidsorganisaties). Met de hand
# nagelopen tegen exportOO_2026-10-08 (type Provincie, naam 'Provincie <naam>'); de codes zijn ook
# de TOOI-codes van de provincies (pv20 … pv31). scripts/test_registers.py toetst de lijst.
PROVINCIES = {
    "PV20": ("Groningen", "15632"), "PV21": ("Fryslân", "15184"), "PV22": ("Drenthe", "14557"),
    "PV23": ("Overijssel", "16771"), "PV24": ("Flevoland", "14866"), "PV25": ("Gelderland", "15185"),
    "PV26": ("Utrecht", "17166"), "PV27": ("Noord-Holland", "16412"), "PV28": ("Zuid-Holland", "17466"),
    "PV29": ("Zeeland", "18166"), "PV30": ("Noord-Brabant", "16317"), "PV31": ("Limburg", "16071"),
}


KOPPELINGEN = Path(__file__).resolve().parent / "koppelingen.json"


def gemeente_oo() -> dict[str, str]:
    """CBS-gemeentecode → oo-id, voor gemeenten zonder tooi-code in het register van
    overheidsorganisaties (de heringedeelde van 2018–2019, zoals Altena): met de hand nagelopen in
    koppelingen.json ('cbs_gemeenten'). Alle andere koppelen via hun tooi-code (gm0225)."""
    if not KOPPELINGEN.exists():
        return {}
    return {k: v["oo"] for k, v in json.loads(KOPPELINGEN.read_text(encoding="utf-8")).get("cbs_gemeenten", {}).items()
            if not k.startswith("_")}


class FormaatFout(Exception):
    """De uitgave heeft niet de kolommen of rijen die deze lezer verwacht."""


def _tabel(jaar: int) -> dict | None:
    titel = TABELTITEL.format(jaar=jaar)
    filt = urllib.parse.quote(f"Title eq '{titel}'")
    rijen = get_json(f"{CATALOGUS}?$format=json&$filter={filt}&$select=Identifier,Title,Period,Modified")["value"]
    return rijen[0] if rijen else None


def haal(jaar: int | None = None) -> Path:
    """Download de tabel van dit jaar (anders vorig jaar) naar data/registers/cbs/cbs_<datum>.json."""
    jaar = jaar or date.today().year
    info = _tabel(jaar) or _tabel(jaar - 1)
    if not info:
        raise FormaatFout(f"geen tabel '{TABELTITEL.format(jaar=jaar)}' in de CBS-catalogus")
    t = info["Identifier"]
    uitgave = {
        "tabel": t,
        "tabelinfo": get_json(f"{ODATA}/{t}/TableInfos?$format=json")["value"][0],
        "kolommen": get_json(f"{ODATA}/{t}/DataProperties?$format=json")["value"],
        "rijen": get_json(f"{ODATA}/{t}/TypedDataSet?$format=json", timeout=120)["value"],
    }
    vandaag = date.today().isoformat()
    pad = MAP / f"cbs_{vandaag}.json"
    MAP.mkdir(parents=True, exist_ok=True)
    pad.write_text(json.dumps(uitgave, ensure_ascii=False, indent=1), encoding="utf-8")
    lees(pad)  # een uitgave die niet te lezen is, bewaren we niet
    (MAP / f"cbs_{vandaag}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("cbs_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"cbs_{uitgave}.json"


def _kolommen(kolommen: list[dict], groep: str) -> tuple[str, str]:
    """(code-, naamkolom) onder de onderwerpgroep `groep` ('Provincies')."""
    ouder = [k["ID"] for k in kolommen if k.get("Type") == "TopicGroup" and schoon(k.get("Title")) == groep]
    if len(ouder) != 1:
        raise FormaatFout(f"onderwerpgroep '{groep}' niet (eenduidig) in de kolommen")
    onder = {schoon(k.get("Title")): k["Key"] for k in kolommen
             if k.get("Type") == "Topic" and k.get("ParentID") == ouder[0]}
    if not {"Code", "Naam"} <= set(onder):
        raise FormaatFout(f"onder '{groep}' staan {sorted(onder)}, geen Code en Naam")
    return onder["Code"], onder["Naam"]


def lees(pad: Path) -> dict:
    """→ {bron, uitgave, sha256, tabel, jaar, records{sleutel: rec}}. Elk record: gemeente,
    gemeentecode, provincie, provinciecode, regel."""
    u = json.loads(pad.read_text(encoding="utf-8"))
    info, tabel = u["tabelinfo"], u["tabel"]
    jaar = schoon(info.get("Period"))
    if schoon(info.get("Title")) != TABELTITEL.format(jaar=jaar):
        raise FormaatFout(f"tabel {tabel} heet '{info.get('Title')}'")
    gem_code, gem_naam = _kolommen(u["kolommen"], "Codes en namen van gemeenten")
    pv_code, pv_naam = _kolommen(u["kolommen"], "Provincies")
    uitgave = pad.stem.split("_", 1)[1]
    records = {}
    for r in u["rijen"]:
        code, naam = schoon(r.get(gem_code)), schoon(r.get(gem_naam))
        pc, pn = schoon(r.get(pv_code)), schoon(r.get(pv_naam))
        if not code.startswith("GM") or not naam:
            continue
        if pc not in PROVINCIES or PROVINCIES[pc][0] != pn:
            raise FormaatFout(f"onbekende provincie {pc} '{pn}' bij {code}")
        rec = {"sleutel": f"gemeente:{code.lower()}", "soort": "cbs", "gemeente": naam, "gemeentecode": code,
               "provincie": pn, "provinciecode": pc,
               "regel": f"{TABELTITEL.format(jaar=jaar)} (CBS, tabel {tabel}) · gemeente {naam} ({code}) · "
                        f"provincie {pn} ({pc})"}
        if rec["sleutel"] in records:
            raise FormaatFout(f"gemeente {code} staat twee keer in de tabel")
        records[rec["sleutel"]] = rec
    if len(records) < MIN_GEMEENTEN:
        raise FormaatFout(f"maar {len(records)} gemeenten in {pad.name}")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad),
            "tabel": tabel, "jaar": jaar, "url": f"{ODATA}/{tabel}/TypedDataSet",
            "titel": TITEL.format(jaar=jaar, tabel=tabel, uitgave=uitgave), "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    data = lees(pad)
    vast = MAP / f"cbs_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != data["sha256"]:
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = data
    return data


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Provincie → gemeente ('controle'): de bron is de provincie uit het record (haar oo-id) en
    het doel de gemeente uit het record (haar tooi-code, gm0225, of de vastgelegde oo-id)."""
    if relatie_type != "controle":
        return f"verbandsoort '{relatie_type}' hoort niet bij de gemeentelijke indeling"
    bron, doel = eindpunten
    oo_id = PROVINCIES[rec["provinciecode"]][1]
    if ("oo", oo_id) not in bron["ids"]:
        return f"de bron '{bron['name']}' is niet de provincie {rec['provincie']} (oo:{oo_id})"
    gem_oo = gemeente_oo().get(rec["gemeentecode"])
    if ("tooi", rec["gemeentecode"].lower()) not in doel["ids"] and not (gem_oo and ("oo", gem_oo) in doel["ids"]):
        return f"het doel '{doel['name']}' is niet de gemeente {rec['gemeente']} (tooi:{rec['gemeentecode'].lower()})"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="CBS Gebieden in Nederland ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    ap.add_argument("--jaar", type=int)
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(a.jaar))
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        print(json.dumps({"uitgave": d["uitgave"], "tabel": d["tabel"], "gemeenten": len(d["records"]),
                          "voorbeeld": [r["regel"] for r in list(d["records"].values())[:3]]},
                         ensure_ascii=False, indent=1))
