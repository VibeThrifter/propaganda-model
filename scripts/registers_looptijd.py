#!/usr/bin/env python3
"""Looptijd van registerfeiten (eigenaarsbesluit 2026-10-09: "vul bij alles de goede jaartallen
in he want het model kijkt gewoon per tijdsvak wat de relaties zijn").

Deterministisch, zonder LLM en zonder mens. Per register (oo, tk, ep, lobby, ser) bouwt dit het plan
van de nieuwste bewaarde uitgave (dezelfde koppeling als de import: externe id's en
koppelingen.json, nooit op naam alleen) en legt het naast de verbanden die al uit dat register
in het model staan. Een verband krijgt de datum die zijn eigen record noemt, alleen als:
  - het verband een registercitatie met precies die recordsleutel draagt (twee sleutels: het
    eindpuntpaar + type uit het plan, én de recordsleutel uit de citatie);
  - het veld nog leeg is (een datum wordt nooit overschreven).
Het begin (active_from) komt uit startDatum (OO: ambtsdrager of organisatie), de zetel (TK/EP:
een fractie begint met de zetel), het einde (active_until) uit eindDatum/TotEnMet. Via
POST /api/relations/<id>/looptijd onder `registercheck`, met de uitgave en het record in de
reden (edit_log oud/nieuw; terug te draaien door een maintainer).

Noemt het register geen begin (de partij van een burgemeester, de toegangspas in het
lobbyregister), dan wordt er niets verzonnen: de uitgave zegt alleen dat het verband op die dag
liep, en dat is geen begin. Het verband krijgt dan in `looptijd_onderzoek` de status
'register_zonder_datum' met de uitgave ("actief volgens uitgave 2026-10-08"). De tijdbalk blijft
zo eerlijk (geen nep-begin), de goedkeuring loopt door (een registerfeit), en de datumzoeker
pakt zulke verbanden als laatste op.

Organisaties (2026-10-13): het OO-record geeft ook het bestaan van de organisatie zelf
(startDatum/eindDatum). Dat gaat via POST /api/entities/<id>/looptijd; de server vult een leeg
veld en vervangt een andere datum alleen als die onbeschermd is (geen mens, geen register, geen
gemerged argument).

Loopt ook mee in de wekelijkse registers-sync. Los:
    python3 scripts/registers_looptijd.py [--droog] [--alleen oo,tk,ep,lobby,ser]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registers_sync  # noqa: E402

CHECK_TOKEN = registers_sync.CHECK_TOKEN
API = registers_sync.API


def _datum(waarde) -> str | None:
    tekst = str(waarde or "").strip()[:10]
    return tekst if len(tekst) >= 4 and tekst[:4].isdigit() else None


def bestaande(bron: str, conn) -> dict[int, dict]:
    """Verbanden uit dit register: id → {sleutel (s, t, type), secties, active_from/until}."""
    uit: dict[int, dict] = {}
    for r in conn.execute("""
        SELECT r.id, r.source_id, r.target_id, r.relation_type, r.active_from, r.active_until,
               c.section, c.page
        FROM relations r JOIN arguments a ON a.relation_id = r.id
        JOIN citations c ON c.argument_id = a.id JOIN sources s ON s.id = c.source_id
        WHERE c.methode = 'officieel_register_scrape' AND s.cluster_key = ?
          AND NOT r.vervangen AND r.status IN ('goedgekeurd', 'voorgesteld')
          AND a.status <> 'verworpen'""", (f"register:{bron}",)):
        v = uit.setdefault(r["id"], {"sleutel": (r["source_id"], r["target_id"], r["relation_type"]),
                                     "secties": set(), "active_from": r["active_from"],
                                     "active_until": r["active_until"]})
        v["secties"].add(r["section"])
    return uit


def onderzocht(conn) -> set[int]:
    try:
        return {r[0] for r in conn.execute("SELECT relation_id FROM looptijd_onderzoek")}
    except sqlite3.OperationalError:
        return set()


def plan_looptijden(bron: str, uitgave: str, data: dict, conn) -> dict:
    """→ {zetten: [{id, velden, reden}], zonder: [{id, detail}], tel: Counter}."""
    plan = registers_sync.plan_voor(bron, data, conn)
    gepland = registers_sync.geplande_relaties(bron, plan, conn)
    al = onderzocht(conn)
    zetten, zonder, tel = [], [], Counter()
    for rid, v in sorted(bestaande(bron, conn).items()):
        typ = v["sleutel"][2]
        r = gepland.get(v["sleutel"])
        if r is None or r["sleutel"] not in v["secties"]:
            if not (v["active_from"] or "").strip():
                tel[f"{typ}: niet in de nieuwste uitgave"] += 1
            continue
        velden = {}
        start, eind = _datum(r.get("start")), _datum(r.get("eind"))
        if start and not (v["active_from"] or "").strip():
            velden["active_from"] = start
        if eind and not (v["active_until"] or "").strip():
            velden["active_until"] = eind
        if velden:
            zetten.append({"id": rid, "velden": velden,
                           "reden": f"{bron}: record {r['sleutel']} in uitgave {uitgave}"})
            tel[f"{typ}: datum uit het record"] += 1
        elif not (v["active_from"] or "").strip():
            if rid not in al:
                zonder.append({"id": rid, "detail": f"{bron}: het register noemt geen begin; "
                                                    f"actief volgens uitgave {uitgave} "
                                                    f"(record {r['sleutel']})"})
            tel[f"{typ}: register noemt geen begin"] += 1
    return {"zetten": zetten, "zonder": zonder, "tel": tel}


def plan_organisaties(uitgave: str, data: dict, conn) -> list[dict]:
    """Het bestaan van overheidsorganisaties (2026-10-13): startDatum/eindDatum van het OO-record
    op de entiteit met die oo-id. Een leeg veld wordt gevuld; een andere datum stuurt het mee,
    en de server vervangt die alleen als hij onbeschermd is (seed- of agentwerk zonder bewijs)
    en het bestaan verfijnt of verruimt (nooit verkort).
    Zo krijgt de NPO 1988 in plaats van 2014. → [{id, velden, reden}]."""
    uit = []
    for eid, oo_id, af, au in conn.execute("""
            SELECT e.id, x.waarde, e.active_from, e.active_until FROM entities e
            JOIN externe_ids x ON x.entity_id = e.id AND x.stelsel = 'oo'
            WHERE NOT e.vervangen AND e.status IN ('goedgekeurd', 'voorgesteld')
              AND e.type <> 'persoon'"""):
        o = data["organisaties"].get(str(oo_id))
        if not o:
            continue
        velden = {}
        start, eind = _datum(o.get("start")), _datum(o.get("eind"))
        if start and start != (af or "").strip():
            velden["active_from"] = start
        if eind and eind != (au or "").strip():
            velden["active_until"] = eind
        if velden:
            uit.append({"id": eid, "velden": velden,
                        "reden": f"oo: record {o['sleutel']} ({o['naam']}) in uitgave {uitgave}"})
    return uit


def draai(*, droog: bool = False, alleen=registers_sync.BRONNEN, meld=print, rest=None,
          data_per_bron: dict | None = None) -> dict:
    if rest is None and not droog:
        rest = registers_sync.naar_model.Rest(CHECK_TOKEN.read_text().strip(), API)
    uitkomst = {}
    for bron in alleen:
        u = uitkomst[bron] = {"gezet": 0, "zonder_datum": 0, "fouten": []}
        try:
            uitgave, data = (data_per_bron or {}).get(bron) or registers_sync.nieuwste(bron)
        except Exception as e:  # noqa: BLE001 — een register dat stuk is, houdt de rest niet tegen
            u["fout"] = f"lezen: {e}"
            meld(f"{bron}: {u['fout']}")
            continue
        conn = registers_sync.db()
        try:
            p = plan_looptijden(bron, uitgave, data, conn)
        finally:
            conn.close()
        u["uitgave"], u["tel"] = uitgave, dict(p["tel"])
        for z in p["zetten"]:
            if droog:
                u["gezet"] += 1
                continue
            status, res = rest("POST", f"/api/relations/{z['id']}/looptijd",
                               {**z["velden"], "reden": z["reden"]})
            if status == 200:
                u["gezet"] += 1
            else:
                u["fouten"].append(f"#{z['id']}: {status} {res.get('error')}")
        for z in p["zonder"]:
            if droog:
                u["zonder_datum"] += 1
                continue
            status, res = rest("POST", "/api/looptijd_onderzoek",
                               {"relation_id": z["id"], "status": "register_zonder_datum",
                                "detail": z["detail"]})
            if status in (200, 201):
                u["zonder_datum"] += 1
            else:
                u["fouten"].append(f"#{z['id']}: {status} {res.get('error')}")
        if bron == "oo":
            u["organisaties"], u["blijft"] = 0, 0
            conn = registers_sync.db()
            try:
                orgs = plan_organisaties(uitgave, data, conn)
            finally:
                conn.close()
            for z in orgs:
                if droog:
                    u["organisaties"] += 1
                    continue
                status, res = rest("POST", f"/api/entities/{z['id']}/looptijd",
                                   {**z["velden"], "reden": z["reden"]})
                if status == 200 and res.get("gewijzigd"):
                    u["organisaties"] += 1
                elif status == 200:
                    u["blijft"] += 1
                else:
                    u["fouten"].append(f"entiteit #{z['id']}: {status} {res.get('error')}")
            meld(f"oo: {u['organisaties']} organisatie(s) kregen hun bestaan uit het register"
                 f"{' (droog)' if droog else ''}; {u['blijft']} houden een beschermde datum")
        meld(f"{bron}: uitgave {uitgave}: {u['gezet']} verband(en) kregen hun datum uit het "
             f"record{' (droog)' if droog else ''}, {u['zonder_datum']} vastgelegd als "
             f"'register noemt geen begin'" + (f"; {len(u['fouten'])} fout(en)" if u["fouten"] else ""))
    return uitkomst


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--droog", action="store_true", help="niets schrijven; laten zien wat")
    ap.add_argument("--alleen", default=",".join(registers_sync.BRONNEN))
    a = ap.parse_args()
    uit = draai(droog=a.droog, alleen=[b for b in a.alleen.split(",") if b in registers_sync.BRONNEN])
    print(json.dumps(uit, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
