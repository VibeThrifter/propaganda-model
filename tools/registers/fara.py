"""FARA (Foreign Agents Registration Act, U.S. Department of Justice) — uitgave ophalen en lezen,
gefilterd op opdrachtgevers uit het Koninkrijk der Nederlanden (eigenaar 2026-10-20: "onderzoek
OpenSecrets als bron en als methodiek … relaties en verbanden die voor een NEDERLANDS model iets
toevoegen").

Wie in de VS optreedt als agent (lobby, pr, juridisch, reclame, voorlichting) van een buitenlandse
opdrachtgever, moet zich bij het DOJ registreren. OpenSecrets toonde die gegevens (bedragen uit de
pdf's); de ruwe registratie is open: efile.fara.gov/bulk/zip/ (geen account, geen sleutel; werk van
de Amerikaanse federale overheid). Vier bestanden:
  - FARA_All_Registrants        registratienummer, naam, registratie- en einddatum van de agent;
  - FARA_All_ForeignPrincipals  per registratie de buitenlandse opdrachtgevers, met land en datums;
  - FARA_All_ShortForms         de personen die voor de agent het werk doen (alleen geteld en als tip,
                                nooit een knoop: het zijn vaak privépersonen);
  - FARA_All_RegistrantDocs     de ingediende documenten per opdrachtgever (url van de pdf).
Bedragen staan alleen in de pdf's (supplemental statements), niet in de bulk; die leest dit
register niet.

De uitgave is één json-bestand data/registers/fara/fara_<ophaaldatum>.json (+ .sha256) met de
sha256 van de vier ruwe zips en alleen de rijen die bij een Nederlandse opdrachtgever horen (land
in LANDEN; de registraties van die opdrachtgevers met al hun eigen rijen). Recordsoorten:
  - 'principaal:<regnr>:<naam>:<begin>'  een opdrachtgever bij een agent (de recordregel = het citaat);
  - 'registrant:<regnr>'                 de agent;
  - 'shortform:<regnr>:<naam>:<datum>'   een persoon die voor de agent werkt (alleen telling).

Koppelen nooit op naam alleen: de agent via de externe id 'fara' (registratienummer) of
REGISTRANTEN (met de hand nagelopen), de opdrachtgever via PRINCIPALEN (met de hand nagelopen,
met de reden). Geen schrijfacties op het model (dat doet fara_naar_model.py via de REST-API).

    python3 tools/registers/fara.py haal
    python3 tools/registers/fara.py lees
"""
from __future__ import annotations

import csv
import datetime
import io
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, download, noemt, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "fara"
BULK = "https://efile.fara.gov/bulk/zip/{naam}.csv.zip"
BESTANDEN = ("FARA_All_Registrants", "FARA_All_ForeignPrincipals", "FARA_All_ShortForms",
             "FARA_All_RegistrantDocs")
URL = "https://efile.fara.gov/ords/fara/f?p=1235:10"
MAP = DATA / BRON
UITGEVER = "U.S. Department of Justice, FARA Unit (efile.fara.gov, bulkdata)"
TITEL = ("Foreign Agents Registration Act (FARA), registraties met een opdrachtgever uit het Koninkrijk der "
         "Nederlanden, bulkdata van efile.fara.gov opgehaald {uitgave}")
# Het Koninkrijk: Nederland, de (voormalige) Nederlandse Antillen en de landen en eilanden in de Cariben
LANDEN = {"NETHERLANDS", "NETHERLANDS ANTILLES", "ARUBA", "CURACAO", "ST. MARTIN", "SINT MAARTEN",
          "BONAIRE", "SABA", "ST. EUSTATIUS", "SINT EUSTATIUS"}

# ── met de hand nagelopen koppelingen (2026-10-20) ──────────────────────────
# Opdrachtgever zoals FARA hem schrijft (sleutel) → (entity_id, naam in het model, reden). Alleen wat
# dezelfde rechtspersoon is (of een onderdeel zonder eigen rechtspersoonlijkheid, zoals een ambassade
# van het ministerie). Voorgangers en fusiepartners (Akzo N.V., Amsterdamsche Bank, AMRO, Hoogovens,
# Bataafse Petroleum Maatschappij, Dutch Employers' Federation) NIET: die zijn een andere knoop.
PRINCIPALEN = {
    "klm royal dutch airlines": (125, "KLM", "Koninklijke Luchtvaart Maatschappij N.V."),
    "royal dutch airlines": (125, "KLM", "Koninklijke Luchtvaart Maatschappij N.V. (1946, Engelse naam)"),
    "klm royal dutch airline": (125, "KLM", "schrijfwijze in FARA"),
    "klm royal dutch airlines koninklijke luchtvaart maatschappij n v": (125, "KLM", "volledige naam"),
    "konimklijke luchtvaart maatschappij n v klm": (125, "KLM", "volledige naam (tikfout in FARA)"),
    "internationale nederlanden group n v": (76, "ING", "Internationale Nederlanden Groep (ING), 1991–"),
    "association of dutch insurers verbond van verzekeraars": (3908, "Verbond van Verzekeraars", "naam staat erin"),
    "royal boskalis westminster n v": (1129, "Boskalis", "Koninklijke Boskalis Westminster N.V."),
    "lever brothers unilever": (36, "Unilever", "Unilever (1929–)"),
    "heineken s breweries": (1128, "Heineken", "Heineken's Bierbrouwerij Mij. N.V."),
    "n v philips gloeilampenfabrieken": (78, "Philips", "N.V. Philips' Gloeilampenfabrieken (zetel 1940–1945 op Curaçao)"),
    "nederlandsche bank n v": (307, "De Nederlandsche Bank (DNB)", "De Nederlandsche Bank N.V."),
    "netherlands bank": (307, "De Nederlandsche Bank (DNB)", "De Nederlandsche Bank N.V. (Engelse naam)"),
    "city of amsterdam": (229, "Gemeente Amsterdam", "de gemeente"),
    "city of amsterdam kingdom of the netherlands": (229, "Gemeente Amsterdam", "de gemeente"),
    "city of rotterdam": (1575, "Gemeente Rotterdam", "de gemeente"),
    "delft university of tech": (384, "TU Delft", "Technische Universiteit Delft"),
    "netherlands government ministry of foreign affairs": (86, "Ministerie van Buitenlandse Zaken", "ministerie genoemd"),
    "netherlands government ministry of foreign affairs of the kingdom of the netherlands": (86, "Ministerie van Buitenlandse Zaken", "ministerie genoemd"),
    "netherlands embassy ministry of foreign affairs": (86, "Ministerie van Buitenlandse Zaken", "ambassade = post van BZ"),
    "royal netherlands embassy": (86, "Ministerie van Buitenlandse Zaken", "ambassade = post van BZ"),
    "netherlands embassy": (86, "Ministerie van Buitenlandse Zaken", "ambassade = post van BZ"),
    "embassy of the netherlands": (86, "Ministerie van Buitenlandse Zaken", "ambassade = post van BZ"),
    "state of the netherlands royal netherlands embassy": (86, "Ministerie van Buitenlandse Zaken", "ambassade = post van BZ"),
    "netherlands government represented by department of economic affairs": (819, "Ministerie van Economische Zaken", "ministerie genoemd"),
    "netherlands ministry of economic affairs": (819, "Ministerie van Economische Zaken", "ministerie genoemd"),
    "department of economic affairs": (819, "Ministerie van Economische Zaken", "registratie 456 (vervolg van 'Netherlands Government, Represented by Department of Economic Affairs')"),
    "economic information service of the netherlands ministry of economic affairs": (819, "Ministerie van Economische Zaken", "dienst van het ministerie"),
    "netherlands foreign investment agency": (819, "Ministerie van Economische Zaken", "NFIA: operationeel onderdeel van het ministerie van EZ(K), geen eigen rechtspersoon"),
    "netherlands foreign investment agency nfia": (819, "Ministerie van Economische Zaken", "NFIA: onderdeel van het ministerie"),
    "government of the netherlands netherlands foreign investment agency nfia": (819, "Ministerie van Economische Zaken", "NFIA: onderdeel van het ministerie"),
}
# Agent (registratienummer) → (entity_id, naam in het model, reden)
REGISTRANTEN = {
    "3301": (122, "Hill+Knowlton", "Hill and Knowlton Strategies, LLC: de Amerikaanse vennootschap van het "
                                   "internationale bureau dat het model als Hill+Knowlton kent (1927–)"),
}


class FormaatFout(Exception):
    """De bulkdata of de uitgave heeft niet het verwachte formaat."""


def _datum(waarde: str | None) -> str | None:
    """'10/12/2026' → '2026-10-12'."""
    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$", waarde or "")
    return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}" if m else None


def _csv(pad: Path, naam: str) -> list[dict]:
    with zipfile.ZipFile(pad) as z:
        leden = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(leden) != 1:
            raise FormaatFout(f"{naam}: verwacht één csv in de zip, vond {leden}")
        ruw = z.read(leden[0])
    try:
        tekst = ruw.decode("utf-8-sig")
    except UnicodeDecodeError:
        tekst = ruw.decode("cp1252")
    return list(csv.DictReader(io.StringIO(tekst)))


VELDEN = {
    "FARA_All_Registrants": {"Registration Number", "Registration Date", "Termination Date", "Name"},
    "FARA_All_ForeignPrincipals": {"Foreign Principal", "Foreign Principal Registration Date",
                                   "Foreign Principal Termination Date", "Country/Location Represented",
                                   "Registration Number", "Registrant Name"},
    "FARA_All_ShortForms": {"Short Form Last Name", "Short Form First Name", "Short Form Date",
                            "Short Form Termination Date", "Registration Number"},
    "FARA_All_RegistrantDocs": {"Date Stamped", "Registration Number", "Document Type", "Foreign Principal Name",
                                "Foreign Principal Country", "URL"},
}


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("fara_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"fara_{uitgave}.json"


def haal(meld=print) -> Path:
    """De vier bulkbestanden ophalen (ruw in data/registers/fara/ruw/, niet de uitgave), filteren op
    het Koninkrijk en de uitgave schrijven."""
    uitgave = datetime.date.today().isoformat()
    ruw_map = MAP / "ruw"
    tabellen, bulk = {}, {}
    for naam in BESTANDEN:
        pad = download(BULK.format(naam=naam), ruw_map / f"{naam}_{uitgave}.zip", timeout=300)
        rijen = _csv(pad, naam)
        if not rijen or VELDEN[naam] - set(rijen[0]):
            raise FormaatFout(f"{naam}: kolommen ontbreken: {sorted(VELDEN[naam] - set(rijen[0] if rijen else {}))}")
        tabellen[naam] = rijen
        bulk[naam] = {"url": BULK.format(naam=naam), "sha256": sha256_bestand(pad), "rijen": len(rijen)}
        meld(f"  {naam}: {len(rijen)} rijen")
    fp = [r for r in tabellen["FARA_All_ForeignPrincipals"]
          if schoon(r["Country/Location Represented"]).upper() in LANDEN]
    regs = {r["Registration Number"].strip() for r in fp}
    namen = {sleutel(r["Foreign Principal"]) for r in fp}
    uit = {
        "bron": BRON, "uitgave": uitgave, "landen": sorted(LANDEN), "bulk": bulk,
        "registranten": [r for r in tabellen["FARA_All_Registrants"] if r["Registration Number"].strip() in regs],
        "principalen": fp,
        "shortforms": [r for r in tabellen["FARA_All_ShortForms"] if r["Registration Number"].strip() in regs],
        "documenten": [r for r in tabellen["FARA_All_RegistrantDocs"]
                       if r["Registration Number"].strip() in regs
                       and (schoon(r["Foreign Principal Country"]).upper() in LANDEN
                            or sleutel(r["Foreign Principal Name"]) in namen)],
    }
    pad = pad_van(uitgave)
    pad.write_text(json.dumps(uit, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    (MAP / f"fara_{uitgave}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


# ── lezen ───────────────────────────────────────────────────────────────────
def _slug(tekst: str, n: int = 60) -> str:
    return sleutel(tekst).replace(" ", "-")[:n]


def _periode(van: str | None, tot: str | None) -> str:
    if van and tot:
        return f"geregistreerd {van}, beëindigd {tot}"
    return f"geregistreerd {van or 'zonder datum'}, nog lopend" if not tot else f"beëindigd {tot}"


def lees(pad: Path) -> dict:
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    uitgave = ruw["uitgave"]
    records: dict[str, dict] = {}
    agenten: dict[str, dict] = {}
    for r in ruw["registranten"]:
        nr = r["Registration Number"].strip()
        van, tot = _datum(r["Registration Date"]), _datum(r["Termination Date"])
        naam = schoon(r["Name"])
        agenten[nr] = {"naam": naam, "zaaknaam": schoon(r.get("Business Name")), "van": van, "tot": tot}
        records[f"registrant:{nr}"] = {
            "sleutel": f"registrant:{nr}", "soort": "registrant", "regnr": nr, "naam": naam, "van": van, "tot": tot,
            "regel": f"FARA eFile (U.S. Department of Justice) · registratie {nr} · registrant: {naam} · "
                     f"{_periode(van, tot)}"}
    docs: dict[tuple[str, str], int] = {}
    for d in ruw["documenten"]:
        k = (d["Registration Number"].strip(), sleutel(d["Foreign Principal Name"]))
        docs[k] = docs.get(k, 0) + 1
    for r in ruw["principalen"]:
        nr = r["Registration Number"].strip()
        naam = schoon(r["Foreign Principal"])
        van, tot = _datum(r["Foreign Principal Registration Date"]), _datum(r["Foreign Principal Termination Date"])
        s = f"principaal:{nr}:{_slug(naam)}:{van or 'zonder-datum'}"
        if s in records:
            continue  # dezelfde opdrachtgever dubbel bij dezelfde registratie op dezelfde dag
        agent = schoon(r["Registrant Name"]) or agenten.get(nr, {}).get("naam", "")
        land = schoon(r["Country/Location Represented"])
        records[s] = {
            "sleutel": s, "soort": "principaal", "regnr": nr, "principaal": naam, "land": land,
            "registrant": agent, "van": van, "tot": tot, "datumfout": bool(van and tot and tot < van),
            "documenten": docs.get((nr, sleutel(naam)), 0),
            "regel": f"FARA eFile (U.S. Department of Justice) · registratie {nr} · registrant: {agent} · "
                     f"buitenlandse opdrachtgever (foreign principal): {naam} · land: {land} · {_periode(van, tot)}"}
    for r in ruw["shortforms"]:
        nr = r["Registration Number"].strip()
        naam = schoon(f"{r['Short Form First Name']} {r['Short Form Last Name']}")
        van = _datum(r["Short Form Date"])
        s = f"shortform:{nr}:{_slug(naam, 40)}:{van or 'zonder-datum'}"
        records.setdefault(s, {"sleutel": s, "soort": "shortform", "regnr": nr, "naam": naam, "van": van,
                               "tot": _datum(r["Short Form Termination Date"]),
                               "regel": f"FARA eFile · registratie {nr} · short form: {naam} · "
                                        f"{_periode(van, _datum(r['Short Form Termination Date']))}"})
    if not any(r["soort"] == "principaal" for r in records.values()):
        raise FormaatFout("geen opdrachtgevers uit het Koninkrijk gelezen")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=uitgave), "bulk": ruw["bulk"], "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"fara_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


RELATIETYPES = {"adviseur"}


def principaal_id(rec: dict) -> int | None:
    """Het model-id van de opdrachtgever volgens de met de hand nagelopen lijst (of None)."""
    k = PRINCIPALEN.get(sleutel(rec.get("principaal")))
    return k[0] if k else None


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """De ene kant is de agent (externe id 'fara' = het registratienummer), de andere de
    opdrachtgever uit het record: volgens PRINCIPALEN, of zijn naam staat in de recordregel."""
    if rec["soort"] != "principaal" or relatie_type not in RELATIETYPES:
        return f"een FARA-feit is opdrachtgever ↔ agent ('adviseur'), niet '{relatie_type}'"
    agent = [e for e in eindpunten if (BRON, rec["regnr"]) in e["ids"]]
    if not agent:
        return f"geen eindpunt met externe id fara:{rec['regnr']}"
    ander = [e for e in eindpunten if e is not agent[0]][0]
    if ander.get("id") is not None and ander["id"] == principaal_id(rec):
        return None
    if noemt(rec["regel"].split("buitenlandse opdrachtgever", 1)[-1], ander["name"]):
        return None
    return f"'{ander['name']}' is niet de opdrachtgever in het record {sleutel_r}"


if __name__ == "__main__":
    import argparse
    from collections import Counter
    ap = argparse.ArgumentParser(description="FARA (Koninkrijk der Nederlanden) ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(uitgaven()[-1])
        tel = Counter(r["soort"] for r in d["records"].values())
        tel["principaal lopend"] = sum(1 for r in d["records"].values() if r["soort"] == "principaal" and not r["tot"])
        print(json.dumps({"uitgave": d["uitgave"], **tel}, ensure_ascii=False))
