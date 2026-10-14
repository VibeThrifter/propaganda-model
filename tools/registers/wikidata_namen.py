#!/usr/bin/env python3
"""Volledige namen uit Wikidata voor burgemeesters en wethouders met voorletters (plan fase 3f).

Droogloop, schrijft niets in het model. Per ambtsdrager uit het register van
overheidsorganisaties (burgemeester, ook waarnemend, of wethouder) die er alleen met voorletters
of een achternaam staat, zoekt dit de ene Wikidata-persoon die past (wikidata.kandidaten: zelfde
gemeente, functie, achternaam, passende voorletters, ambt niet geëindigd vóór het begin uit het
register; precies één kandidaat en één registerrecord). Uitkomst:
  - telling: eenduidig / meer kandidaten / geen kandidaat / registernaam niet uniek;
  - per eenduidige treffer: de knoop in het model (via de externe id oo:m:<medewerker>), de
    huidige naam, de QID en de volledige naam →
    data/registers/wikidata/namen_<uitgave oo>_<uitgave wikidata>.json.

Toepassen ("via de routes", eigenaarsbesluit 2026-10-14), onder het account `register-import`:
  --indienen   de QID gaat via POST /api/entities/<id>/register {"externe_ids": [{"stelsel":
               "wikidata", "waarde": QID}]} aan de knoop (vult alleen aan), voor elke eenduidige
               treffer, ook de voorletterknoop van een duplicaat (bij samenvoegen verhuist de QID
               naar de opvolger);
  --hernoemen  daarna de naam via POST /api/entities/<id>/registernaam {"waarde": QID, "uitgave":
               …}: de server toetst zelf (label in de bewaarde uitgave, achternaam en voorletters,
               ambt en gemeente) en houdt de toevoeging "(burgemeester …)" alleen bij een
               naamgenoot. Zonder PROPAGANDA_REGISTERNAAM=1 op de server is dat een droogloop.
Een duplicaat (de volledige naam is al van dezelfde persoon) wordt niet hernoemd maar
samengevoegd via een samenvoegen-RfC; een naamgenoot staat in NAAMGENOTEN (nagegaan).

Gebruik:
    python3 tools/registers/wikidata_namen.py [--uitgave-oo D] [--uitgave-wikidata D]
    python3 tools/registers/wikidata_namen.py --indienen [--hernoemen]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import oo  # noqa: E402
import wikidata  # noqa: E402
from common import ROOT, ontleed_naam, sleutel  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
TOKEN = ROOT / "data" / "tokens" / "register-import.token"
API = "http://127.0.0.1:5000"
# QID → waarom de knoop met dezelfde volledige naam een ándere persoon is (nagegaan 2026-10-14).
# Zo'n treffer wordt hernoemd mét de toevoeging uit het register; elke andere botsing is een
# duplicaat en gaat via een samenvoegen-RfC.
NAAMGENOTEN = {
    "Q128804255": "Inge van Dijk (VVD, burgemeester van Mook en Middelaar sinds 2024, geboren 1984) is niet "
                  "de knoop Inge van Dijk (CDA, Tweede Kamerlid sinds 2021): Wikidata P39/P102 en de open "
                  "data van de Tweede Kamer",
}


def registersleutel(rec: dict, org: dict, naam: dict) -> tuple | None:
    cbs = wikidata.cbs_van(org.get("tooi"))
    soort = wikidata.soort_van(rec["functie"])
    achter = sleutel(f"{naam.get('tussenvoegsel') or ''} {naam.get('achternaam') or ''}")
    return (cbs, soort, achter) if cbs and soort and achter else None


def zoek(oo_data: dict, wd: dict) -> dict:
    """→ {treffers: [...], tel: Counter, per_sleutel}. Alle lopende burgemeesters/wethouders
    zonder voornaam in het register."""
    idx = wikidata.index(wd)
    orgs = oo_data["organisaties"]
    records = []
    per_sleutel: Counter = Counter()
    for f in oo_data["functies"].values():
        if f["eind"]:
            continue
        org = orgs.get(f["oo_id"]) or {}
        if (org.get("types") or [""])[0] != "Gemeente" or org.get("ouder_oo"):
            continue
        naam = ontleed_naam(f["naam_register"])
        k = registersleutel(f, org, naam)
        if not k:
            continue
        per_sleutel[k] += 1
        if naam["volledig"]:
            continue
        records.append((f, org, naam, k))
    tel, treffers = Counter(), []
    for f, org, naam, k in records:
        soort = "alleen achternaam" if naam["alleen_achternaam"] else "voorletters"
        tel[f"{soort}: totaal"] += 1
        if per_sleutel[k] > 1:
            tel[f"{soort}: registernaam niet uniek in de gemeente"] += 1
            continue
        kand = wikidata.kandidaten(idx, k[0], k[1], naam, f["start"], oo_data["uitgave"])
        if len(kand) != 1:
            tel[f"{soort}: {'geen kandidaat' if not kand else 'meer kandidaten'}"] += 1
            continue
        tel[f"{soort}: eenduidig"] += 1
        treffers.append({"sleutel": f["sleutel"], "medewerker": f["sleutel"].rsplit(":", 1)[-1],
                         "register": f["naam_register"], "functie": f["functie"], "gemeente": org["naam"],
                         "qid": kand[0]["qid"], "naam_wikidata": kand[0]["naam"],
                         "voorletters_wikidata": kand[0]["voorletters"], "soort": soort})
    return {"treffers": treffers, "tel": tel}


def met_model(treffers: list[dict], conn) -> Counter:
    """Zet bij elke treffer de knoop in het model (externe id oo:m:<medewerker>) en telt."""
    ext = {w: e for e, w in conn.execute("SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'oo'")}
    wd_bezet = {w: e for e, w in conn.execute(
        "SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'wikidata'")}
    namen = {i: n for i, n in conn.execute("SELECT id, name FROM entities")}
    alle = {sleutel(n): i for i, n in namen.items()}
    tel = Counter()
    for t in treffers:
        eid = ext.get(f"m:{t['medewerker']}")
        t["entity_id"], t["naam_model"] = eid, namen.get(eid)
        achter = sleutel(ontleed_naam(t["register"])["achternaam"] or "")
        if achter and achter not in sleutel(t["naam_wikidata"]):
            # de registercheck eist de registerachternaam in de naam van de knoop
            tel["Wikidata-naam mist een deel van de achternaam"] += 1
            t["let_op"] = "achternaam uit het register ontbreekt in de Wikidata-naam"
        elif eid is None:
            tel["nog niet in het model"] += 1
        elif t["qid"] in wd_bezet and wd_bezet[t["qid"]] != eid:
            tel["QID al bij een andere knoop"] += 1
            t["let_op"] = f"QID hoort al bij #{wd_bezet[t['qid']]}"
        elif sleutel(t["naam_wikidata"]) in alle and alle[sleutel(t["naam_wikidata"])] != eid:
            if t["qid"] in NAAMGENOTEN:
                tel["naamgenoot: hernoemen met de toevoeging"] += 1
                t["naamgenoot"] = NAAMGENOTEN[t["qid"]]
                t["hernoemen"] = True
            else:
                tel["volledige naam is al van een andere knoop (duplicaat: samenvoegen)"] += 1
                t["let_op"] = f"naam bestaat al: #{alle[sleutel(t['naam_wikidata'])]}"
        elif t["naam_model"] == t["naam_wikidata"]:
            tel["heeft de volledige naam al"] += 1
        else:
            tel["klaar om te hernoemen"] += 1
            t["hernoemen"] = True
    return tel


def indienen(treffers: list[dict], rest, uitgave_wd: str, hernoemen: bool, log=print) -> Counter:
    """QID's aan de knopen hangen en (met `hernoemen`) de naam laten wijzigen, via de REST-API
    onder register-import. `rest(methode, pad, body)` → (status, json)."""
    tel = Counter()
    for t in treffers:
        eid = t.get("entity_id")
        if not eid or (t.get("let_op") or "").startswith("QID hoort al"):
            tel["QID: overgeslagen (geen knoop of QID bezet)"] += 1
            continue
        status, res = rest("POST", f"/api/entities/{eid}/register",
                           {"externe_ids": [{"stelsel": "wikidata", "waarde": t["qid"]}],
                            "reden": f"Wikidata-naam bij het register (uitgave {uitgave_wd})"})
        if status != 200:
            tel[f"QID: fout {status}"] += 1
            log(f"  ✗ QID {t['qid']} → #{eid}: {status} {res.get('error')}")
            continue
        tel["QID: gezet" if res.get("gewijzigd") else "QID: had hem al"] += 1
        if not (hernoemen and t.get("hernoemen")):
            continue
        status, res = rest("POST", f"/api/entities/{eid}/registernaam",
                           {"stelsel": "wikidata", "waarde": t["qid"], "uitgave": uitgave_wd})
        if status != 200:
            tel[f"naam: geweigerd {status}"] += 1
            log(f"  ✗ naam #{eid} '{t['naam_model']}': {status} {res.get('error')}")
            continue
        tel["naam: droogloop (server)" if res.get("droog") else "naam: gewijzigd"] += 1
        if "(" in res.get("nieuw", ""):
            tel["naam: met toevoeging (naamgenoot)"] += 1
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave-oo")
    ap.add_argument("--uitgave-wikidata")
    ap.add_argument("--indienen", action="store_true", help="QID's aan de knopen hangen (register-import)")
    ap.add_argument("--hernoemen", action="store_true",
                    help="met --indienen: ook de naam (de server toetst; droogloop tenzij PROPAGANDA_REGISTERNAAM=1)")
    ap.add_argument("--api", default=API)
    a = ap.parse_args()
    oo_data = oo.lees(oo.pad_van(a.uitgave_oo) if a.uitgave_oo else oo.uitgaven()[-1])
    wd = wikidata.lees(wikidata.pad_van(a.uitgave_wikidata) if a.uitgave_wikidata else wikidata.uitgaven()[-1])
    uit = zoek(oo_data, wd)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    model = met_model(uit["treffers"], conn)
    pad = wikidata.MAP / f"namen_{oo_data['uitgave']}_{wd['uitgave']}.json"
    pad.write_text(json.dumps(uit["treffers"], ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"uitgave_oo": oo_data["uitgave"], "uitgave_wikidata": wd["uitgave"],
                      "register": dict(sorted(uit["tel"].items())), "model": dict(model)},
                     ensure_ascii=False, indent=1))
    if not a.indienen:
        print(f"\n(droogloop — niets gewijzigd; zie {pad})")
        return
    if not TOKEN.exists():
        sys.exit(f"Token ontbreekt: {TOKEN}")
    from naar_model import Rest
    tel = indienen(uit["treffers"], Rest(TOKEN.read_text().strip(), a.api), wd["uitgave"], a.hernoemen)
    print(json.dumps(tel, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
