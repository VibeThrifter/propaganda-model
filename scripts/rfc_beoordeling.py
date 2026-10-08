#!/usr/bin/env python3
"""RfC-beoordeling — open voorstellen (RfC's) wachten niet meer op een mens (eigenaarsbesluit
2026-10-06: "niks door mensen, alles door agents").

Twee onafhankelijke agents reviewen elk open voorstel, elk onder een eigen account en met een
eigen rol en model:
- `rfc-toetser` (Claude Opus): klopt het en past het? Feiten nagaan (met WebSearch/WebFetch,
  bv. een naamswijziging of een fusie), past het in de theorie, is het geen duplicaat van een
  bestaand element, is de definitie helder en onderscheidend;
- `rfc-criticus` (Claude Sonnet): zoekt redenen om af te wijzen (duplicaat, te vaag, feitelijk
  onjuist, buiten het model) en wijst alleen af met een concrete reden.
Elk oordeel gaat via POST /api/voorstellen/<id>/reviews (agent-advies). Daarna beslist de
automatische beoordeling via POST /api/beoordeling/rfc/<id>: twee akkoorden van verschillende
agent-accounts en geen afwijzing → aangenomen en uitgevoerd; één afwijzing → afgewezen met die
motivatie (de indiener kan herzien).

Gebruik:
    python3 scripts/rfc_beoordeling.py --droog          # oordelen tonen, niets schrijven
    python3 scripts/rfc_beoordeling.py --json           # echt
    python3 scripts/rfc_beoordeling.py --ids 52,63
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_API = "http://127.0.0.1:5000"
TOKENS = ROOT / "data" / "tokens"
LOG_PATH = ROOT / "data" / "rfc_beoordeling_log.jsonl"
LLM_TIMEOUT_S = 900
ROLLEN = {
    "rfc-toetser": {
        "model": "opus",
        "systeem": (
            "Je bent toetser van voorstellen (RfC's) voor een onderzoeksdatabase over het "
            "Nederlandse media- en bestuurssysteem als één netwerk: het propagandamodel van "
            "Herman & Chomsky plus de besluitvormingscategorieën (formele macht, belangen, kennis "
            "& advies, polder, werving; naar Domhoff). Je "
            "toetst of een voorstel klopt en past: (1) feiten kloppen (ga ze na op het web met "
            "WebSearch/WebFetch; verzin niets); (2) het past in de theorie en het model; (3) het "
            "is geen duplicaat of bijna-duplicaat van een bestaand element; (4) een nieuwe "
            "definitie is helder en onderscheidend. 'akkoord' als het aan alles voldoet, anders "
            "'afwijzen' met een concrete, controleerbare reden. Antwoord alleen met het JSON."),
    },
    "rfc-criticus": {
        "model": "sonnet",
        "systeem": (
            "Je bent de criticus van voorstellen (RfC's) voor een onderzoeksdatabase over het "
            "Nederlandse media- en bestuurssysteem als één netwerk (propagandamodel van Herman & "
            "Chomsky plus besluitvorming: formele macht, belangen, kennis & advies, polder, "
            "werving). Hoe besluiten tot stand komen valt BINNEN het onderwerp. Je zoekt redenen "
            "om een voorstel af te wijzen: een duplicaat van een bestaand element, te vaag of "
            "niet onderscheidend, feitelijk onjuist (ga feiten na op het web met "
            "WebSearch/WebFetch), of buiten het onderwerp van het model. Wijs alleen af met een "
            "concrete, controleerbare reden; vind je die niet, dan 'akkoord'. Antwoord alleen "
            "met het JSON."),
    },
}
SCHEMA = {
    "type": "object",
    "properties": {"oordeel": {"type": "string", "enum": ["akkoord", "afwijzen"]},
                   "motivatie": {"type": "string"}},
    "required": ["oordeel", "motivatie"],
    "additionalProperties": False,
}


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def open_voorstellen(conn, ids=None) -> list[dict]:
    filt, params = "", []
    if ids:
        filt = f" AND id IN ({','.join('?' * len(ids))})"
        params = list(ids)
    return [dict(r) for r in conn.execute(
        f"SELECT * FROM voorstellen WHERE status = 'open'{filt} ORDER BY id",  # noqa: S608
        params)]


def al_gereviewd(conn, vid: int, reviewer: str) -> bool:
    return conn.execute("SELECT 1 FROM voorstel_reviews WHERE voorstel_id = ? AND reviewer = ?",
                        (vid, reviewer)).fetchone() is not None


def context(conn, voorstel: dict) -> str:
    """Wat een reviewer van het model moet weten om dit voorstel te beoordelen."""
    payload = json.loads(voorstel["payload"])
    regels = []
    if payload.get("element_type") == "mechanisme" or voorstel["soort"] == "nieuw_theorie_element":
        filt = payload.get("filter")
        rijen = conn.execute("""SELECT name, filter, description FROM mechanisms
                                WHERE NOT vervangen AND (? IS NULL OR filter = ?)
                                ORDER BY name""", (filt, filt)).fetchall()
        regels.append(f"Bestaande mechanismen{f' in filter {filt}' if filt else ''}:")
        regels += [f"- {r['name']}: {' '.join((r['description'] or '').split())[:260]}"
                   for r in rijen]
    ids = [payload.get("element_id"), *(payload.get("oud_ids") or [])]
    doel = payload.get("doel") or {}
    ids.append(doel.get("bestaand_id") if isinstance(doel, dict) else None)
    if payload.get("element_type") == "entiteit":
        for eid in [i for i in ids if isinstance(i, int)]:
            e = conn.execute("SELECT id, name, type, description FROM entities WHERE id = ?",
                             (eid,)).fetchone()
            if e:
                n_rel = conn.execute("SELECT COUNT(*) FROM relations WHERE (source_id = ? OR "
                                     "target_id = ?) AND NOT vervangen", (eid, eid)).fetchone()[0]
                regels.append(f"Entiteit #{e['id']}: {e['name']} ({e['type']}), {n_rel} relaties"
                              f"{'; ' + e['description'][:300] if e['description'] else ''}")
    return "\n".join(regels)


def vraag(rol: str, prompt: str) -> dict | None:
    """Eén `claude -p`-sessie met alleen WebSearch/WebFetch."""
    instelling = ROLLEN[rol]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [bc.CLAUDE, "-p", "--output-format", "json", "--tools", "WebSearch,WebFetch",
           "--allowedTools", "WebSearch,WebFetch", "--strict-mcp-config", "--setting-sources",
           "", "--no-session-persistence", "--model", instelling["model"], "--system-prompt",
           instelling["systeem"], "--json-schema", json.dumps(SCHEMA)]
    with tempfile.TemporaryDirectory(prefix="rfc-") as leeg:
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=leeg,
                               env=env, timeout=LLM_TIMEOUT_S)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    try:
        envelope = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return None
    uit = envelope.get("structured_output")
    if envelope.get("is_error") or not isinstance(uit, dict):
        return None
    if uit.get("oordeel") not in ("akkoord", "afwijzen") or not (uit.get("motivatie") or "").strip():
        return None
    return uit


def post_review(api, token, vid, oordeel) -> tuple[int, dict]:
    body = {"oordeel": oordeel["oordeel"], "motivatie": oordeel["motivatie"].strip()[:1500]}
    req = urllib.request.Request(f"{api}/api/voorstellen/{vid}/reviews",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except json.JSONDecodeError:
            return e.code, {}


def draai(*, api=DEFAULT_API, droog=False, ids=None, max_n=6, meld=print) -> dict:
    """Eén ronde over de open voorstellen. → {voorstellen, reviews, akkoord, afwijzen, fout}."""
    conn = db()
    try:
        voorstellen = open_voorstellen(conn, ids)[:max_n]
        werk = []
        for v in voorstellen:
            for rol in ROLLEN:
                if rol == v["ingediend_door"] or al_gereviewd(conn, v["id"], rol):
                    continue
                werk.append((v, rol, context(conn, v)))
    finally:
        conn.close()
    meld(f"RfC-beoordeling: {len(voorstellen)} open voorstel(len), {len(werk)} review(s) te doen"
         f"{' (droog)' if droog else ''}")
    tel = {"voorstellen": len(voorstellen), "reviews": 0, "akkoord": 0, "afwijzen": 0, "fout": 0}
    if not droog:
        zonder = {rol for _v, rol, _c in werk if not (TOKENS / f"{rol}.token").exists()}
        for rol in sorted(zonder):
            meld(f"  ✗ geen token voor {rol}")
        werk = [taak for taak in werk if taak[1] not in zonder]

    def review(v, rol, ctx):
        prompt = (f"Voorstel #{v['id']} ({v['soort']}), ingediend door {v['ingediend_door']}:\n"
                  f"Titel: {v['titel']}\nPayload (JSON): {v['payload'][:6000]}\n\n"
                  f"{ctx}\n\nGeef je oordeel ('akkoord' of 'afwijzen') en in 'motivatie' twee of "
                  "drie zinnen, met de bronnen die je raadpleegde.")
        return vraag(rol, prompt)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        toekomst = {pool.submit(review, *taak): taak for taak in werk}
        klaar = [(toekomst[f], f.result()) for f in concurrent.futures.as_completed(toekomst)]
    for (v, rol, _ctx), oordeel in klaar:
        token_pad = TOKENS / f"{rol}.token"
        if oordeel is None:
            tel["fout"] += 1
            meld(f"  · #{v['id']} {rol}: geen bruikbaar oordeel (volgende ronde opnieuw)")
            continue
        tel["reviews"] += 1
        tel[oordeel["oordeel"]] += 1
        regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                 "voorstel_id": v["id"], "reviewer": rol, **oordeel}
        if not droog:
            status, antwoord = post_review(api, token_pad.read_text().strip(), v["id"], oordeel)
            regel["http"] = status
            if status not in (200, 201):
                regel["fout"] = antwoord.get("error")
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as log:
                log.write(json.dumps(regel, ensure_ascii=False) + "\n")
        meld(f"  · #{v['id']} {rol}: {oordeel['oordeel']} — {oordeel['motivatie'][:120]}")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--ids", default="", help="alleen deze voorstel-id's (komma's)")
    ap.add_argument("--max", type=int, default=6, help="hooguit zoveel voorstellen per ronde")
    ap.add_argument("--droog", action="store_true", help="oordeel, maar schrijf niets")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    tel = draai(api=args.api, droog=args.droog, ids=ids, max_n=args.max)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
