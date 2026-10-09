#!/usr/bin/env python3
"""Smaadtoets — de smaad-firewall door een agent (eigenaarsbesluit 2026-10-06: "laat de
smaad-firewall checken of het feitelijk is; als het niet feitelijk is koppel het terug, en
anders is het geen smaad").

Kandidaten: argumenten over een natuurlijk persoon (het doel van de boom is een persoon, of
een relatie met een persoon als bron of doel) die geen neutraal structuurfeit zijn (lid van,
werkt bij, bestuurder van: die mergen al op de bron-check alleen), en waarvan een
onafhankelijk A1-oordeel zegt dat de bron de bewering draagt. Voorgesteld, onder smaad_hold,
of door de automatische beoordeling verworpen omdat de oude firewall ze nooit doorliet.

Per argument leest Claude Opus de bewering naast de brontekst (die het script zelf ophaalt;
`claude -p` zonder tools) en oordeelt:
- 'feitelijk': een controleerbaar feit (geen mening of waardeoordeel als feit gebracht),
  gedragen door de bron (niet verder dan de bron: geen overdrijving, insinuatie of conclusie
  die de bron niet trekt), over de publieke rol (functie, beroep, publieke uitspraken en
  optredens) en niet over het privéleven;
- 'niet_feitelijk': anders, met de reden en waar mogelijk een feitelijke formulering die de
  bron wél draagt.
Het oordeel gaat naar POST /api/arguments/<id>/smaadtoets (account 'smaadtoets', nooit de
auteur). Daarna beslist scripts/automatische_beoordeling.py: 'feitelijk' → smaad_hold eraf en
de gewone poorten (A1, en A2 voor wat geen bronrevisie is); 'niet_feitelijk' → teruggekoppeld:
verworpen met de reden en de feitelijke formulering.

Gebruik:
    python3 scripts/smaadtoets.py --droog --max 5      # oordelen tonen, niets schrijven
    python3 scripts/smaadtoets.py --max 20 --json      # echt
    python3 scripts/smaadtoets.py --ids 3713           # alleen dit argument
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "smaadtoets"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "smaadtoets_log.jsonl"
MODEL = "opus"
# Spiegelt server.BEOORDELING_STRUCTUURTYPES (neutrale structuurfeiten: geen smaadtoets nodig)
STRUCTUURTYPES = ("personeel", "dienstverband", "bestuurder", "adviseur", "woordvoerder_van",
                  "lidmaatschap", "eigendom", "draaideur",
                  "ambt", "zeggenschap", "controle", "geschenk")  # Uitbreiding C (2026-10-07)

SYSTEM_PROMPT = (
    "Je bent de smaadtoets van een onderzoeksdatabase over het Nederlandse media- en "
    "bestuurssysteem. Een "
    "bewering raakt een met naam genoemd natuurlijk persoon. Je toetst of ze publiceerbaar is "
    "zonder smaad: (1) het is een controleerbaar FEIT, geen mening of waardeoordeel dat als feit "
    "wordt gebracht; (2) de BRON draagt het: de bewering gaat niet verder dan wat de brontekst "
    "zegt — geen overdrijving, geen insinuatie, geen conclusie over motieven of schuld die de "
    "bron niet zelf trekt; (3) het gaat over de PUBLIEKE ROL van de persoon (functie, beroep, "
    "publieke uitspraken en optredens), niet over het privéleven (gezondheid, gezin, relaties, "
    "geloof, adres) tenzij de bron dat zelf in verband met de publieke rol publiek maakt. "
    "Een kritisch of onwelgevallig feit is publiceerbaar als het aan alle drie voldoet. "
    "Een herformulering schrijf je in neutrale eigen woorden: wie deed of zei wat, wanneer; "
    "geen oordeel over gevolgen of motieven en geen etiket, zo'n oordeel alleen als citaat met "
    "de naam van wie het uitsprak (de stemtoets toetst dat daarna). "
    "Antwoord alleen met het gevraagde JSON."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "oordeel": {"type": "string", "enum": ["feitelijk", "niet_feitelijk"]},
        "reden": {"type": "string"},
        "herformulering": {"type": "string"},
    },
    "required": ["oordeel", "reden", "herformulering"],
    "additionalProperties": False,
}


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def wortel(conn, arg) -> sqlite3.Row:
    """De root van de boom (die draagt het doel)."""
    gezien = set()
    while arg["parent_argument_id"] is not None and arg["id"] not in gezien:
        gezien.add(arg["id"])
        ouder = conn.execute("SELECT * FROM arguments WHERE id = ?",
                             (arg["parent_argument_id"],)).fetchone()
        if ouder is None:
            break
        arg = ouder
    return arg


def personen_van(conn, arg) -> tuple[list[str], str | None]:
    """(namen van de geraakte personen, relatietype) voor het doel van de boom."""
    doel = wortel(conn, arg)
    if doel["entity_id"]:
        e = conn.execute("SELECT name, type FROM entities WHERE id = ?",
                         (doel["entity_id"],)).fetchone()
        return ([e["name"]] if e and e["type"] == "persoon" else []), None
    if doel["relation_id"]:
        r = conn.execute("""SELECT r.relation_type, s.name AS sn, s.type AS st, t.name AS tn,
                                   t.type AS tt FROM relations r
                            JOIN entities s ON s.id = r.source_id
                            JOIN entities t ON t.id = r.target_id WHERE r.id = ?""",
                         (doel["relation_id"],)).fetchone()
        if r:
            return ([n for n, typ in ((r["sn"], r["st"]), (r["tn"], r["tt"]))
                     if typ == "persoon"], r["relation_type"])
    return [], None


def nieuwste_a1(conn, arg_id):
    return conn.execute("""SELECT verdict, door, created_at FROM immuun_oordelen
                           WHERE argument_id = ? AND fase = 'herverificatie'
                           ORDER BY created_at DESC, id DESC LIMIT 1""", (arg_id,)).fetchone()


def kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Persoonsclaims met een onafhankelijke A1 'klopt' en nog geen smaadtoets van dit account:
    voorgesteld, onder smaad_hold, of door de automatische beoordeling verworpen omdat de oude
    firewall ze nooit doorliet (wat het nieuws toont eerst)."""
    filt, params = "", [ACCOUNT]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    rijen = conn.execute(f"""
        SELECT a.*, r.source_id AS rel_bron, r.target_id AS rel_doel FROM arguments a
        LEFT JOIN relations r ON r.id = a.relation_id
        WHERE NOT a.vervangen
          AND NOT EXISTS (SELECT 1 FROM smaad_toetsen t WHERE t.argument_id = a.id
                          AND t.door = ?)
          AND (a.status = 'voorgesteld'
               OR (COALESCE(a.smaad_hold, 0) = 1 AND a.status <> 'verworpen')
               OR (a.status = 'verworpen'
                   AND (SELECT l.reason FROM edit_log l WHERE l.table_name = 'arguments'
                          AND l.record_id = a.id AND l.action = 'disputed'
                          AND l.new_value LIKE '%verworpen%' ORDER BY l.id DESC LIMIT 1)
                       LIKE 'automatische beoordeling: na % dagen niet te bevestigen%')){filt}""",
                         params).fetchall()  # noqa: S608 - alleen placeholders
    uit = []
    for a in rijen:
        a1 = nieuwste_a1(conn, a["id"])
        if a1 is None or a1["verdict"] != "klopt" or a1["door"] == a["contributed_by"]:
            continue
        personen, rtype = personen_van(conn, a)
        if not personen:
            continue
        if (a["parent_argument_id"] is None and a["stance"] == "supporting"
                and rtype in STRUCTUURTYPES):
            continue  # neutraal structuurfeit: geen smaadtoets nodig
        uit.append(a)
    return bc.sorteer_op_voorrang(conn, uit)


def toets(arg_id: int) -> dict:
    """→ {verdict, reden, herformulering} of {verdict: None, detail} bij een technische fout."""
    conn = db()
    try:
        arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
        personen, _ = personen_van(conn, arg)
        doel = bc.doel_tekst(conn, arg)
        bronnen = bc.bronnen_van(conn, arg_id)
    finally:
        conn.close()
    delen = []
    for bron in bronnen:
        citaat = (bron.get("quote") or "").strip()
        tekst, toelichting, url = bc.haal_bron(bron, citaat or None)
        regel = (f"Bron: {bron.get('title') or '?'} ({bron.get('publisher') or bc.host_van(url)}, "
                 f"{bron.get('date_published') or 'datum onbekend'}) {bron.get('url') or ''}\n"
                 f"Aangehaald citaat: \"{citaat}\"")
        if tekst:
            _g, _l, pos = bc.zoek_citaat(citaat, tekst) if citaat else (False, False, None)
            regel += f"\nTekst uit de bron:\n<<<\n{bc.fragment(tekst, pos, len(citaat))[:5000]}\n>>>"
        else:
            regel += f"\n(bron zelf niet te lezen: {toelichting})"
        delen.append(regel)
    if not any("Tekst uit de bron" in d for d in delen):
        return {"verdict": None, "detail": "geen bron te lezen"}
    prompt = (f"Bewering: {arg['claim']}\n"
              + (f"Toelichting van de indiener: {arg['reasoning'][:800]}\n"
                 if (arg["reasoning"] or "").strip() else "")
              + f"Geraakte persoon/personen: {', '.join(personen)}\n"
              f"Het argument gaat over {doel}.\n\n" + "\n\n".join(delen) + "\n\n"
              "Vraag: is deze bewering publiceerbaar zonder smaad (feit, gedragen door de bron, "
              "publieke rol)? Geef in 'reden' één of twee korte zinnen. Is het 'niet_feitelijk', "
              "geef dan in 'herformulering' een feitelijke versie die de bron wél draagt (of een "
              "lege tekst als die er niet is); bij 'feitelijk' een lege tekst.")
    antwoord = bc.vraag_model(prompt, SCHEMA, systeem=SYSTEM_PROMPT, model=MODEL)
    if not antwoord or antwoord.get("oordeel") not in ("feitelijk", "niet_feitelijk"):
        return {"verdict": None, "detail": "model gaf geen bruikbaar oordeel"}
    return {"verdict": antwoord["oordeel"], "reden": (antwoord.get("reden") or "").strip(),
            "herformulering": (antwoord.get("herformulering") or "").strip()}


def post_toets(api, token, arg_id, uitkomst) -> tuple[int, dict]:
    body = {"verdict": uitkomst["verdict"], "reden": uitkomst["reden"] or "zonder toelichting"}
    if uitkomst.get("herformulering"):
        body["herformulering"] = uitkomst["herformulering"]
    req = urllib.request.Request(f"{api}/api/arguments/{arg_id}/smaadtoets",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    for poging in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and poging == 1:
                time.sleep(62)
                continue
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except json.JSONDecodeError:
                return e.code, {}
    return 429, {}


def draai(*, api=DEFAULT_API, token_pad=DEFAULT_TOKEN, max_n=20, droog=False, ids=None,
          parallel=2, meld=print) -> dict:
    """Eén ronde. → {bekeken, feitelijk, niet_feitelijk, technisch, geschreven, fouten}."""
    token = None
    if not droog:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad} (scripts/create_user.py "
                             f"{ACCOUNT} --kind agent --provenance ... --new-token --save)")
    conn = db()
    try:
        rijen = kandidaten(conn, ids)[:max_n]
    finally:
        conn.close()
    meld(f"Smaadtoets: {len(rijen)} persoonsclaim(s){' (droog)' if droog else ''}")
    tel = {"bekeken": 0, "feitelijk": 0, "niet_feitelijk": 0, "technisch": 0, "geschreven": 0,
           "fouten": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        toekomst = {pool.submit(toets, a["id"]): a for a in rijen}
        for f in concurrent.futures.as_completed(toekomst):
            arg = toekomst[f]
            try:
                uitkomst = f.result()
            except Exception as exc:  # noqa: BLE001 - één fout stopt de ronde niet
                uitkomst = {"verdict": None, "detail": str(exc)[:200]}
            tel["bekeken"] += 1
            if uitkomst["verdict"] is None:
                tel["technisch"] += 1
                meld(f"  · #{arg['id']}: later opnieuw — {uitkomst.get('detail')}")
                continue
            tel[uitkomst["verdict"]] += 1
            regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                     "argument_id": arg["id"], **uitkomst}
            if not droog:
                status, antwoord = post_toets(api, token, arg["id"], uitkomst)
                regel["http"] = status
                if status in (200, 201):
                    tel["geschreven"] += 1
                else:
                    tel["fouten"] += 1
                    regel["fout"] = antwoord.get("error")
                LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(LOG_PATH, "a", encoding="utf-8") as log:
                    log.write(json.dumps(regel, ensure_ascii=False) + "\n")
            meld(f"  · #{arg['id']}: {uitkomst['verdict']} — {uitkomst['reden'][:120]}")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max", type=int, default=20, help="hooguit zoveel claims per ronde")
    ap.add_argument("--ids", default="", help="alleen deze argument-id's (komma's)")
    ap.add_argument("--parallel", type=int, default=2, help="gelijktijdige modelaanroepen")
    ap.add_argument("--droog", action="store_true", help="toets, maar schrijf niets")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    tel = draai(api=args.api, token_pad=args.token, max_n=args.max, droog=args.droog, ids=ids,
                parallel=args.parallel)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
