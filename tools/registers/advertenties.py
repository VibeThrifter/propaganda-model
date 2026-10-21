"""Meta Ad Library Report, Nederland — uitgave ophalen en lezen (verkenning 2026-10-20).

Meta publiceert per land een samenvatting van zijn advertentiebibliotheek voor advertenties over
"maatschappelijke kwesties, verkiezingen of politiek": per Facebook/Instagram-pagina en per
disclaimer ("betaald door") het totaal uitgegeven bedrag in euro en het aantal advertenties. Die
twee kolommen samen zijn het verband: wie betaalt voor wiens advertenties.

Toegang (getoetst 2026-10-20):
  - facebook.com/ads/library/report geeft zonder browser 403; de Ad Library API vereist een
    Facebook-account met identiteitsverificatie en een toegangstoken. Geen van beide gebruikt.
  - Fabio Votta (metatargetr, UvA/Who Targets Me) archiveert het rapport dagelijks als
    GitHub-release (github.com/favstats/meta_ad_reports, tag NL-lifelong, één zip per dag:
    Meta's eigen download, ongewijzigd: FacebookAdLibraryReport_<datum>_NL_lifelong_*.csv +
    Meta's README). Die zip is hier de uitgave. Het archief loopt t/m 2025-04-21 (lifelong) en
    2025-07-05 (laatste 90 dagen); sinds 6 oktober 2025 neemt Meta in de EU geen politieke
    advertenties meer aan (TTPA), dus daarna komt er niets nieuws bij.
  - Het bedrag is cumulatief ("lifelong", alles wat de bibliotheek nog bewaart; Meta houdt een
    advertentie zeven jaar). Het verschil tussen twee uitgaven is wat in die periode is uitgegeven
    (`haal --reeks` haalt een uitgave per kwartaal voor de piekanalyse).

Uitgave: data/registers/advertenties/advertenties_<rapportdatum>.zip (+ .sha256), rapportdatum
zoals Meta haar in de bestandsnaam zet. Een record is één rij van het adverteerdersbestand;
recordsleutel = pagina-id | disclaimer | volgnummer (Meta geeft soms twee rijen voor hetzelfde
paar). De recordregel is het citaat.

Geen schrijfacties op het model (dat doet advertenties_naar_model.py, alleen als droogloop).

    python3 tools/registers/advertenties.py haal [--datum 2025-04-21]
    python3 tools/registers/advertenties.py haal --reeks
    python3 tools/registers/advertenties.py lees
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
from common import DATA, download, get_json, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "advertenties"
LAND = "NL"
URL = f"https://www.facebook.com/ads/library/report/?country={LAND}"
ARCHIEF = "https://github.com/favstats/meta_ad_reports/releases/download/{tag}/{datum}.zip"
ARCHIEF_API = "https://api.github.com/repos/favstats/meta_ad_reports/releases/tags/{tag}"
TAG = f"{LAND}-lifelong"
MAP = DATA / BRON
UITGEVER = "Meta Platforms (Ad Library Report), gearchiveerd door F. Votta (metatargetr)"
TITEL = ("Meta Ad Library Report Nederland, advertenties over maatschappelijke kwesties, verkiezingen of "
         "politiek, cumulatief t/m {uitgave} (per pagina en disclaimer)")
GEEN_DISCLAIMER = "These ads ran without a disclaimer"
# Kwartaalreeks voor de piekanalyse (PS/WS 15-03-2023, TK 22-11-2023, EP 06-06-2024). De eerste
# uitgave na Meta's vernieuwde rapport (2021-12-31, 3.236 rijen) is onvolledig; de reeks begint
# daarom bij 2022-03-31 en de gemeenteraadsverkiezingen van 16-03-2022 vallen erbuiten.
REEKS = ["2022-04-01", "2022-07-01", "2022-10-01", "2023-01-01", "2023-04-01",
         "2023-07-01", "2023-10-01", "2024-01-01", "2024-04-01", "2024-07-01", "2024-10-01",
         "2025-01-01", "2025-04-21"]
KOLOMMEN = ["Page ID", "Page name", "Disclaimer", "Amount spent (EUR)", "Number of ads in Library"]


class FormaatFout(Exception):
    """De zip heeft niet het verwachte adverteerdersbestand."""


def beschikbaar() -> list[str]:
    """Datums (zip-namen) in het archief, oplopend."""
    d = get_json(ARCHIEF_API.format(tag=TAG), timeout=120)
    return sorted(a["name"][:-4] for a in d.get("assets", []) if re.match(r"^\d{4}-\d{2}-\d{2}\.zip$", a["name"]))


def haal(datum: str | None = None) -> Path:
    """Eén dagarchief ophalen; standaard het nieuwste. Uitgave = de rapportdatum in de zip."""
    datum = datum or beschikbaar()[-1]
    MAP.mkdir(parents=True, exist_ok=True)
    tijdelijk = download(ARCHIEF.format(tag=TAG, datum=datum), MAP / "nieuw.zip")
    uitgave = _rapportdatum(tijdelijk)
    pad = pad_van(uitgave)
    tijdelijk.replace(pad)
    (MAP / f"{BRON}_{uitgave}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def haal_reeks() -> list[Path]:
    """De kwartaalreeks (REEKS); een datum die het archief niet heeft, schuift naar de eerstvolgende."""
    alle = beschikbaar()
    uit = []
    for d in REEKS:
        kandidaat = next((a for a in alle if a >= d), None)
        # het archief heet naar de dag van ophalen, de uitgave naar Meta's rapportdatum (een dag eerder)
        al = {p.stem.split("_", 1)[1] for p in uitgaven()}
        vorige = (datetime.date.fromisoformat(kandidaat) - datetime.timedelta(days=1)).isoformat() \
            if kandidaat else None
        if kandidaat and not {kandidaat, vorige} & al:
            uit.append(haal(kandidaat))
    return uit


def _adverteerders_csv(z: zipfile.ZipFile) -> str:
    namen = [n for n in z.namelist() if re.search(rf"_{LAND}_lifelong_advertisers\.csv$", n)]
    if len(namen) != 1:
        raise FormaatFout("geen (of meer dan één) adverteerdersbestand in de zip")
    return namen[0]


def _rapportdatum(pad: Path) -> str:
    with zipfile.ZipFile(pad) as z:
        m = re.search(r"FacebookAdLibraryReport(?:Revamp)?_(\d{4}-\d{2}-\d{2})_", _adverteerders_csv(z))
    if not m:
        raise FormaatFout("geen rapportdatum in de bestandsnaam")
    return m.group(1)


def uitgaven() -> list[Path]:
    return sorted(MAP.glob(f"{BRON}_????-??-??.zip"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"{BRON}_{uitgave}.zip"


def bedrag(waarde: str) -> int | None:
    """'2839326' → 2839326; '≤100' → None (Meta noemt kleine bedragen niet)."""
    return int(waarde) if waarde.isdigit() else None


def lees(pad: Path) -> dict:
    with zipfile.ZipFile(pad) as z:
        naam = _adverteerders_csv(z)
        tekst = z.read(naam).decode("utf-8-sig")
    m = re.search(r"FacebookAdLibraryReport(?:Revamp)?_(\d{4}-\d{2}-\d{2})_", naam)
    uitgave = m.group(1)
    lezer = csv.DictReader(io.StringIO(tekst))
    if lezer.fieldnames != KOLOMMEN:
        raise FormaatFout(f"onverwachte kolommen: {lezer.fieldnames}")
    records, volg = {}, {}
    for r in lezer:
        r = {k: schoon(v) for k, v in r.items()}
        basis = f"{r['Page ID']}|{sleutel(r['Disclaimer']).replace(' ', '-') or '-'}"
        volg[basis] = volg.get(basis, 0) + 1
        s = f"{basis}|{volg[basis]}"
        records[s] = {
            "sleutel": s, "soort": "advertentie", "pagina_id": r["Page ID"], "pagina": r["Page name"],
            "disclaimer": r["Disclaimer"], "eur": bedrag(r["Amount spent (EUR)"]),
            "eur_tekst": r["Amount spent (EUR)"], "advertenties": int(r["Number of ads in Library"] or 0),
            "regel": (f"Meta Ad Library Report {LAND} (cumulatief t/m {uitgave}) · pagina: {r['Page name']} "
                      f"(pagina-id {r['Page ID']}) · disclaimer (betaald door): {r['Disclaimer']} · "
                      f"uitgegeven: € {r['Amount spent (EUR)']} · advertenties: {r['Number of ads in Library']}")}
    if not records:
        raise FormaatFout("geen rijen gelezen")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=uitgave), "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"{BRON}_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """'donor': de bron is de disclaimer (exacte naam), het doel de partij van de pagina (exacte
    naam of de partijtabel uit common). 'adverteerder': de bron is de disclaimer, het doel Meta."""
    from common import partij_naam
    bron, doel = eindpunten
    if rec["disclaimer"] == GEEN_DISCLAIMER:
        return "record zonder disclaimer"
    hand = {}
    kp = Path(__file__).resolve().parent / "koppelingen.json"
    if kp.exists():
        hand = {sleutel(k): sleutel(v) for k, v in json.loads(kp.read_text(encoding="utf-8"))
                .get("advertenties_namen", {}).items() if not k.startswith("_")}
    if sleutel(bron["name"]) not in {sleutel(rec["disclaimer"]), hand.get(sleutel(rec["disclaimer"]))}:
        return f"'{bron['name']}' is niet de disclaimer van record {sleutel_r}"
    if relatie_type == "donor":
        if doel["type"] != "partij":
            return "een advertentiedonatie gaat naar een partij"
        if sleutel(doel["name"]) not in {sleutel(rec["pagina"]), sleutel(partij_naam(rec["pagina"]) or "")}:
            return f"'{doel['name']}' is niet de pagina van record {sleutel_r}"
        return None
    if relatie_type == "adverteerder":
        return None if doel["type"] == "platform" and sleutel(doel["name"]).startswith("meta") \
            else "een advertentiefeit uit dit rapport heeft Meta als doel"
    return "dit rapport levert alleen 'donor' en 'adverteerder'"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Meta Ad Library Report NL ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--datum", help="dagarchief (YYYY-MM-DD); standaard het nieuwste")
    ap.add_argument("--reeks", action="store_true", help="de kwartaalreeks voor de piekanalyse")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal_reeks() if a.reeks else haal(a.datum))
    else:
        for p in uitgaven():
            d = lees(p)
            print(json.dumps({"uitgave": d["uitgave"], "rijen": len(d["records"]),
                              "eur": sum(r["eur"] or 0 for r in d["records"].values())}))
