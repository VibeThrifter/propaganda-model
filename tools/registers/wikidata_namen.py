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

Toepassen (later, niet in deze droogloop): de QID hangt `register-import` aan de knoop via
POST /api/entities/<id>/register {"externe_ids": [{"stelsel": "wikidata", "waarde": QID}]}
(vult alleen aan); de naam zelf wijzigt alleen een maintainer (PATCH /api/entities/<id> name,
edit_log). Het model heeft geen aliassen: de voorletternaam verdwijnt dan als naam, de
registercheck blijft kloppen (hij toetst de achternaam en de externe id m:<medewerker>).

Gebruik:
    python3 tools/registers/wikidata_namen.py [--uitgave-oo D] [--uitgave-wikidata D]
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
            tel["volledige naam is al van een andere knoop"] += 1
            t["let_op"] = f"naam bestaat al: #{alle[sleutel(t['naam_wikidata'])]}"
        else:
            tel["klaar om te hernoemen"] += 1
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave-oo")
    ap.add_argument("--uitgave-wikidata")
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
    print(f"\n(droogloop — niets gewijzigd; zie {pad})")


if __name__ == "__main__":
    main()
