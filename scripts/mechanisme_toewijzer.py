#!/usr/bin/env python3
"""Mechanisme-toewijzer — kandidaat-verbanden wachten niet meer op een mens (eigenaarsbesluit
2026-10-06: "niks door mensen, alles door agents").

Een kandidaat is een voorgestelde relatie zonder mechanisme ("nog geen theorie-huis"). Per
kandidaat kiest Claude Sonnet (`claude -p`, geen tools) uit de bestaande mechanismen het
mechanisme dat het verband beschrijft — met de precedenten (welke mechanismen goedgekeurde
relaties van hetzelfde type hebben) bovenaan — of zegt dat er geen past. Een keuze gaat via
POST /api/beoordeling/mechanisme/<id> (merge-service; de server checkt dat het een kandidaat
is en het mechanisme bestaat); daarna beslist de gewone bewijspoort over de relatie. Past er
geen, dan blijft ze kandidaat en komt ze na 30 dagen terug (nieuwe mechanismen komen via
RfC's, die nu ook door agents beslist worden).

Gebruik:
    python3 scripts/mechanisme_toewijzer.py --droog --max 5
    python3 scripts/mechanisme_toewijzer.py --max 12 --json
    python3 scripts/mechanisme_toewijzer.py --ids 1765
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "merge-service.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "mechanisme_toewijzer_log.jsonl"
POGINGEN_PATH = ROOT / "data" / "mechanisme_pogingen.json"
MODEL = "sonnet"
OPNIEUW_NA_DAGEN = 30
OMSCHRIJVING_TEKENS = 220

SYSTEM_PROMPT = (
    "Je classificeert verbanden in een onderzoeksdatabase over het Nederlandse mediasysteem "
    "(propagandamodel van Herman & Chomsky). Elk verband moet bij precies één mechanisme horen: "
    "het mechanisme beschrijft HOE de ene partij de andere beïnvloedt of eraan verbonden is. "
    "Kies alleen een mechanisme waarvan de omschrijving dit verband echt dekt (bron- en "
    "doeltype, richting, soort band); volg bij twijfel de precedenten van hetzelfde relatietype. "
    "Past er geen, kies dan 0. Antwoord alleen met het gevraagde JSON."
)
SCHEMA = {
    "type": "object",
    "properties": {"mechanism_id": {"type": "integer"}, "reden": {"type": "string"}},
    "required": ["mechanism_id", "reden"],
    "additionalProperties": False,
}


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def laad_pogingen() -> dict:
    try:
        return json.loads(POGINGEN_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def bewaar_pogingen(pogingen: dict) -> None:
    POGINGEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    POGINGEN_PATH.write_text(json.dumps(pogingen, indent=1), encoding="utf-8")


def kandidaten(conn, ids=None) -> list[dict]:
    """Voorgestelde relaties zonder mechanisme, nooit door een maintainer ingetrokken."""
    filt, params = "", []
    if ids:
        filt = f" AND r.id IN ({','.join('?' * len(ids))})"
        params = list(ids)
    return [dict(r) for r in conn.execute(f"""
        SELECT r.id, r.relation_type, r.description, s.name AS bron, s.type AS bron_type,
               t.name AS doel, t.type AS doel_type FROM relations r
        JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
        WHERE r.status = 'voorgesteld' AND NOT r.vervangen AND r.mechanism_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM edit_log l WHERE l.table_name = 'relations'
                          AND l.record_id = r.id AND l.reason LIKE 'intrekken%'){filt}
        ORDER BY r.id""", params)]  # noqa: S608 - alleen placeholders


def mechanismen(conn) -> list[dict]:
    return [dict(m) for m in conn.execute("""
        SELECT id, name, filter, description FROM mechanisms WHERE NOT vervangen
        ORDER BY filter, name""")]


def precedenten(conn, relation_type: str) -> list[dict]:
    """De mechanismen van goedgekeurde relaties van hetzelfde type, meest gebruikt eerst."""
    return [dict(r) for r in conn.execute("""
        SELECT m.id, m.name, COUNT(*) AS n FROM relations r JOIN mechanisms m
          ON m.id = r.mechanism_id
        WHERE r.relation_type = ? AND r.status = 'goedgekeurd' AND NOT r.vervangen
          AND NOT m.vervangen
        GROUP BY m.id ORDER BY n DESC LIMIT 8""", (relation_type,))]


def prompt_voor(conn, rel: dict, alle: list[dict]) -> str:
    claims = [r["claim"] for r in conn.execute("""
        SELECT claim FROM arguments WHERE relation_id = ? AND NOT vervangen
          AND status <> 'verworpen' ORDER BY id LIMIT 4""", (rel["id"],))]
    regels = [f"Verband: {rel['bron']} ({rel['bron_type']}) → {rel['doel']} ({rel['doel_type']}),"
              f" relatietype '{rel['relation_type']}'."]
    if (rel.get("description") or "").strip():
        regels.append(f"Omschrijving: {rel['description'].strip()[:600]}")
    for claim in claims:
        regels.append(f"Argument: {claim[:400]}")
    voor = precedenten(conn, rel["relation_type"])
    if voor:
        regels.append("\nPrecedenten (mechanismen van goedgekeurde relaties van dit type): "
                      + "; ".join(f"#{p['id']} {p['name']} ({p['n']}×)" for p in voor))
    regels.append("\nMechanismen (id, naam, filter: omschrijving):")
    for m in alle:
        omschrijving = " ".join((m["description"] or "").split())[:OMSCHRIJVING_TEKENS]
        regels.append(f"#{m['id']} {m['name']} [{m['filter']}]: {omschrijving}")
    regels.append("\nGeef het id van het mechanisme dat dit verband beschrijft (0 = geen past) en "
                  "in 'reden' één korte zin waarom.")
    return "\n".join(regels)


def kies(rel_id: int) -> dict:
    conn = db()
    try:
        rel = kandidaten(conn, [rel_id])
        if not rel:
            return {"uitkomst": "fout", "reden": "geen kandidaat meer"}
        alle = mechanismen(conn)
        prompt = prompt_voor(conn, rel[0], alle)
    finally:
        conn.close()
    antwoord = bc.vraag_model(prompt, SCHEMA, systeem=SYSTEM_PROMPT, model=MODEL)
    if not antwoord or not isinstance(antwoord.get("mechanism_id"), int):
        return {"uitkomst": "fout", "reden": "model gaf geen bruikbaar antwoord"}
    mid = antwoord["mechanism_id"]
    namen = {m["id"]: m["name"] for m in alle}
    if mid == 0:
        return {"uitkomst": "geen", "reden": (antwoord.get("reden") or "").strip()}
    if mid not in namen:
        return {"uitkomst": "fout", "reden": f"onbekend mechanisme {mid}"}
    return {"uitkomst": "gekozen", "mechanism_id": mid, "mechanisme": namen[mid],
            "reden": (antwoord.get("reden") or "").strip()}


def draai(*, api=DEFAULT_API, token_pad=DEFAULT_TOKEN, max_n=12, droog=False, ids=None,
          parallel=2, meld=print) -> dict:
    """Eén ronde. → {bekeken, gekozen, geen, fout, gezet}."""
    token = None
    if not droog:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad}")
    nu = datetime.datetime.now()
    pogingen = laad_pogingen()
    conn = db()
    try:
        alle = kandidaten(conn, ids)
    finally:
        conn.close()

    def mag(rel):
        poging = pogingen.get(str(rel["id"]))
        if ids or not poging:
            return True
        try:
            op = datetime.datetime.fromisoformat(poging["op"])
        except (KeyError, ValueError):
            return True
        return nu - op >= datetime.timedelta(days=OPNIEUW_NA_DAGEN)

    rijen = [r for r in alle if mag(r)][:max_n]
    meld(f"Mechanisme-toewijzer: {len(rijen)} van {len(alle)} kandidaat-verband(en)"
         f"{' (droog)' if droog else ''}")
    tel = {"bekeken": 0, "gekozen": 0, "geen": 0, "fout": 0, "gezet": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        toekomst = {pool.submit(kies, r["id"]): r for r in rijen}
        for f in concurrent.futures.as_completed(toekomst):
            rel = toekomst[f]
            try:
                uitkomst = f.result()
            except Exception as exc:  # noqa: BLE001
                uitkomst = {"uitkomst": "fout", "reden": str(exc)[:200]}
            tel["bekeken"] += 1
            tel[uitkomst["uitkomst"]] += 1
            regel = {"ts": nu.isoformat(timespec="seconds"), "relation_id": rel["id"],
                     **uitkomst}
            if uitkomst["uitkomst"] == "gekozen" and not droog:
                status, antwoord = post(api, token, f"/api/beoordeling/mechanisme/{rel['id']}",
                                        {"mechanism_id": uitkomst["mechanism_id"],
                                         "motivatie": uitkomst["reden"] or "past het best"})
                regel["http"] = status
                if status == 200:
                    tel["gezet"] += 1
                else:
                    regel["fout"] = antwoord.get("error") or antwoord.get("redenen")
            meld(f"  · relatie #{rel['id']} ({rel['bron']} → {rel['doel']}): {uitkomst['uitkomst']}"
                 f"{' ' + uitkomst['mechanisme'] if uitkomst.get('mechanisme') else ''}"
                 f" — {uitkomst['reden'][:100]}")
            if not droog and uitkomst["uitkomst"] != "fout":
                pogingen[str(rel["id"])] = {"op": nu.isoformat(timespec="seconds"),
                                            "uitkomst": uitkomst["uitkomst"]}
                LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(LOG_PATH, "a", encoding="utf-8") as log:
                    log.write(json.dumps(regel, ensure_ascii=False) + "\n")
    if not droog:
        bewaar_pogingen(pogingen)
    return tel


def post(api, token, pad, body):
    """POST met het merge-service-token (vrijgesteld van de rate limit)."""
    req = urllib.request.Request(f"{api}{pad}", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except json.JSONDecodeError:
            return e.code, {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max", type=int, default=12, help="hooguit zoveel kandidaten per ronde")
    ap.add_argument("--ids", default="", help="alleen deze relatie-id's (komma's)")
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--droog", action="store_true", help="kies, maar schrijf niets")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    tel = draai(api=args.api, token_pad=args.token, max_n=args.max, droog=args.droog, ids=ids,
                parallel=args.parallel)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
