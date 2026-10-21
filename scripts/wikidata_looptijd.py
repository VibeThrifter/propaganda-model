#!/usr/bin/env python3
"""Begin van burgemeesters en wethouders uit Wikidata (eigenaarsbesluit 2026-10-09/15: "vul bij
alles de goede jaartallen in" en "fix alles .. efficient maar klopt").

Deterministisch, zonder LLM. Het register van overheidsorganisaties noemt vaak geen begin van een
ambt (`register_zonder_datum`). Wikidata kent het begin (P39 + P580) van veel burgemeesters en
wethouders. Dezelfde koppelregels als de naamgeving (tools/registers/wikidata.py: gemeente, functie,
achternaam, voorletters, precies één kandidaat; nooit op naam alleen) beslissen of een Wikidata-
ambt hetzelfde ambt is als het verband in het model. Een verband met een QID op de knoop gebruikt
dat QID.

Wat er gebeurt:
  - alleen goedgekeurde `ambt`-verbanden zonder begin (en zonder einde) naar een gemeente (tooi gm…)
    met functie burgemeester of wethouder;
  - het ambt moet volgens Wikidata lopen (geen einddatum) en het begin staat erin;
  - bij meerdere termijnen telt de lopende (zonder einde);
  - de uitgave moet ongewijzigd zijn (sha256), en komt met QID en uitgave in de reden;
  - POST /api/relations/<id>/looptijd als `registercheck` (vult alleen een leeg veld, edit_log
    met oud/nieuw, terug te draaien).
Niets wordt verzonnen: geen unieke kandidaat, geen begin, een eindig ambt of een ambt dat niet
loopt → het verband blijft zoals het was.

    python3 scripts/wikidata_looptijd.py [--droog] [--limiet N]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "registers"))
import common  # noqa: E402
import wikidata  # noqa: E402

DB = ROOT / "data" / "propaganda_model.db"
TOKEN = ROOT / "data" / "tokens" / "registercheck.token"
API = "http://127.0.0.1:5000"


def post(pad: str, body: dict, token: str) -> tuple[int, dict]:
    req = urllib.request.Request(API + pad, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except ValueError:
            return e.code, {}


def plan(conn, wd) -> tuple[list[dict], Counter]:
    idx = wikidata.index(wd)
    per_qid: dict[str, list[dict]] = {}
    for a in wd["ambten"]:
        per_qid.setdefault(a["qid"], []).append(a)
    qid_van = {}
    for r in conn.execute("SELECT entity_id, waarde FROM externe_ids WHERE stelsel='wikidata'"):
        qid_van[r["entity_id"]] = r["waarde"]
    rijen = conn.execute("""
        SELECT r.id, r.functie, s.id sid, s.name sname, x.waarde tooi
        FROM relations r JOIN entities s ON s.id = r.source_id
        JOIN externe_ids x ON x.entity_id = r.target_id AND x.stelsel = 'tooi'
        WHERE r.relation_type = 'ambt' AND r.status = 'goedgekeurd' AND NOT r.vervangen
          AND COALESCE(r.active_from, '') = '' AND COALESCE(r.active_until, '') = ''
          AND s.type = 'persoon'""").fetchall()
    uit, tel = [], Counter()
    for r in rijen:
        soort, cbs = wikidata.soort_van(r["functie"] or ""), wikidata.cbs_van(r["tooi"])
        if not soort or not cbs:
            tel["geen burgemeester/wethouder van een gemeente"] += 1
            continue
        m = re.match(r"^([^()]*?)\s*\((.*)\)\s*$", r["sname"])
        basis = m.group(1) if m else r["sname"]
        naam = common.ontleed_naam(basis)
        qid = qid_van.get(r["sid"])
        if qid:
            kand = [k for k in idx.get((cbs, soort), []) if k["qid"] == qid]
            kand = list({k["qid"]: k for k in kand}.values())
        else:
            kand = wikidata.kandidaten(idx, cbs, soort, naam, None, wd["uitgave"])
        if len(kand) != 1:
            tel["geen unieke kandidaat" if not kand else "meerdere kandidaten"] += 1
            continue
        q = kand[0]["qid"]
        termijnen = [a for a in per_qid.get(q, []) if a["soort"] == soort and a["cbs"] == cbs]
        lopend = [a for a in termijnen if not a["eind"]]
        if not lopend:
            tel["ambt eindigde volgens Wikidata"] += 1
            continue
        met_begin = sorted(a["start"] for a in lopend if a["start"])
        if not met_begin:
            tel["Wikidata noemt geen begin"] += 1
            continue
        start = met_begin[-1]
        uit.append({"id": r["id"], "datum": start, "qid": q, "naam": r["sname"], "gemeente": cbs,
                    "soort": soort})
        tel["datum"] += 1
    return uit, tel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--droog", action="store_true")
    ap.add_argument("--limiet", type=int, default=0)
    a = ap.parse_args()
    wd = wikidata.nieuwste()
    if not wd:
        print("geen Wikidata-uitgave")
        return 1
    pad = Path(wd["bestand"])
    sha = pad.with_suffix(".sha256")
    if sha.read_text().split()[0] != common.sha256_bestand(pad):
        print("uitgave gewijzigd (sha256)")
        return 1
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    items, tel = plan(conn, wd)
    conn.close()
    print(json.dumps(dict(tel), ensure_ascii=False))
    token = TOKEN.read_text().strip()
    gedaan = Counter()
    for it in items[: a.limiet or None]:
        if a.droog:
            print(f"  (droog) #{it['id']} {it['naam']}: {it['datum']} ({it['qid']})")
            continue
        status, res = post(f"/api/relations/{it['id']}/looptijd",
                           {"active_from": it["datum"],
                            "reden": f"wikidata {it['qid']} ({it['soort']}, gemeente CBS {it['gemeente']}), "
                                     f"uitgave {wd['uitgave']}, start {it['datum']}"}, token)
        gedaan["gezet" if status == 200 else f"fout {status}: {res.get('error')}"] += 1
    print(json.dumps(dict(gedaan), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
