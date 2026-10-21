#!/usr/bin/env python3
"""Richtingtoets — een gericht verband wijst van wie de invloed uitoefent naar wie haar ondergaat
(eigenaarsbesluit 2026-10-15: "frits wester werkt voor rtl nieuws is een niet directioneel …
verband dat klopt, maar werkt voor cda staat erin als frits wester directioneel naar CDA maar dat
klopt niet echt … alleen directioneel als a ook echt invloed heeft op b en niet echt andersom,
zoals a financiert b of a is eigenaar van b … ga het hele propagandamodel af met een haiku agent
… en zorg ook dat de agents ze in de toekomst niet meer maken").

Twee lagen:
1. Het TYPE beslist bij de richtingloze typen (vocab.RICHTINGLOZE_TYPES: lidmaatschap, personeel,
   dienstverband, bestuurder, adviseur, woordvoerder_van, draaideur, ambt, alliantie): geen
   richting, niets te toetsen. De viz tekent ze zonder enkele pijl, influence.py telt ze in beide
   richtingen.
2. Elk verband van een GERICHT type (financiering, eigendom, flak, beinvloeding, …) toetst dit
   script: Claude Haiku (via de `claude`-CLI, zonder tools) leest bron, doel, type, mechanisme,
   functie, beschrijving en de steunende bewering en zegt 'juist', 'omgekeerd' (bron en doel
   staan verkeerd om) of 'richtingloos' (geen eenzijdige invloed: de een hoort bij de ander, of
   ze beïnvloeden elkaar evenzeer). Wil Haiku iets veranderen, dan oordeelt Sonnet onafhankelijk
   (zonder het oordeel van Haiku te zien); alleen als ze het eens zijn telt de wijziging, anders
   'twijfel' (er verandert niets).

Kandidaten: voorgestelde en goedgekeurde verbanden van een gericht type, niet al richtingloos,
geen registerfeit (dat heeft zijn richting uit het record), zonder oordeel van dit account over
het verband zoals het nu is (relatie_hash); voorstellen eerst. Het oordeel gaat naar
POST /api/richtingtoets (account 'richtingtoets', nooit de auteur). Wat ermee gebeurt, beslist
scripts/automatische_beoordeling.py (stap 7b): 'omgekeerd' → bron en doel wisselen,
'richtingloos' → bidirectional = 1 (POST /api/beoordeling/richting/<id>, edit_log, één keer per
verband, alleen seed- en agentwerk).

Gebruik:
    python3 scripts/richtingtoets.py --droog --max 25        # oordelen tonen, niets schrijven
    python3 scripts/richtingtoets.py --json                   # echt
    python3 scripts/richtingtoets.py --droog --ids 1078,1326
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402
import vocab  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "richtingtoets"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "richtingtoets_log.jsonl"
MODEL = "haiku"
MODEL_BEVESTIGING = "sonnet"
BATCH = 20
WIJZIGINGEN = ("omgekeerd", "richtingloos")

SYSTEM_PROMPT = (
    "Je toetst de RICHTING van verbanden in een onderzoeksdatabase over het Nederlandse media- "
    "en bestuurssysteem. Een verband 'bron → doel' betekent: de bron oefent invloed uit op het "
    "doel, op de manier die het type zegt (bij elk verband staat wat bron → doel bij dat type "
    "betekent). Per verband kies je:\n"
    "- 'juist': de bron oefent die invloed uit op het doel, en niet in gelijke mate andersom "
    "(de financier financiert de ontvanger, de eigenaar bezit het bedrijf, de expert of het "
    "instituut voedt het medium, de toezichthouder houdt toezicht, de aanvaller valt aan, de "
    "gever geeft het geschenk, de hogere organisatie stuurt de lagere).\n"
    "- 'omgekeerd': het type klopt, maar bron en doel staan verkeerd om (de ontvanger staat als "
    "financier, het bedrijf als eigenaar van zijn eigenaar, het medium als bron van zijn "
    "expert, het doelwit als aanvaller).\n"
    "- 'richtingloos': er is geen eenzijdige invloed — de een hoort bij de ander (werkt voor, is "
    "lid van, zit in het bestuur, spreekt namens), of beide beïnvloeden elkaar evenzeer. Een "
    "gast of columnist die in een programma of krant optreedt is NIET richtingloos: die voedt "
    "het medium (juist, bron = de gast).\n"
    "- 'twijfel': de gegevens zeggen niet genoeg.\n"
    "Oordeel op de feiten van het verband (namen, beschrijving, bewering), niet op het "
    "mechanisme alleen: de theorierichting van het mechanisme is context. Wees terughoudend: "
    "kies 'omgekeerd' of 'richtingloos' alleen als het duidelijk is. Reden: één korte zin in "
    "het Nederlands. Antwoord alleen met het gevraagde JSON."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "oordelen": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nr": {"type": "integer"},
                    "oordeel": {"type": "string",
                                "enum": ["juist", "omgekeerd", "richtingloos", "twijfel"]},
                    "reden": {"type": "string"},
                },
                "required": ["nr", "oordeel", "reden"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["oordelen"],
    "additionalProperties": False,
}


def richting_hash(rel) -> str:
    """Spiegelt server.richting_hash: bron|doel|type|mechanisme|bidirectional."""
    import hashlib
    sleutel = "|".join(str(rel[k] if rel[k] is not None else "") for k in
                       ("source_id", "target_id", "relation_type", "mechanism_id"))
    return hashlib.sha256(f"{sleutel}|{int(bool(rel['bidirectional']))}".encode()).hexdigest()


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def oordeel_voor(conn, rel) -> sqlite3.Row | None:
    """Het oordeel van dit account over het verband zoals het nu is, of None."""
    if not bc.heeft_tabel(conn, "richting_toetsen"):
        return None
    return conn.execute("""SELECT verdict, reden, model FROM richting_toetsen
                           WHERE relation_id = ? AND door = ? AND relatie_hash = ?""",
                        (rel["id"], ACCOUNT, richting_hash(rel))).fetchone()


def kandidaten(conn, max_n=200, ids=None) -> list[sqlite3.Row]:
    richtingloos = sorted(vocab.RICHTINGLOZE_TYPES)
    plek = ",".join("?" * len(richtingloos))
    filter_ids = f"AND r.id IN ({','.join('?' * len(ids))})" if ids else ""
    rijen = conn.execute(f"""
        SELECT r.* FROM relations r
        WHERE NOT r.vervangen AND r.status IN ('voorgesteld', 'goedgekeurd')
          AND r.relation_type NOT IN ({plek}) AND COALESCE(r.bidirectional, 0) = 0
          AND NOT EXISTS (SELECT 1 FROM arguments a JOIN citations c ON c.argument_id = a.id
                          WHERE a.relation_id = r.id AND c.methode = 'officieel_register_scrape')
          AND COALESCE((SELECT l.changed_by FROM edit_log l WHERE l.table_name = 'relations'
                          AND l.record_id = r.id AND l.action = 'created'
                        ORDER BY l.id LIMIT 1), '') <> ?
          {filter_ids}
        ORDER BY (r.status = 'voorgesteld') DESC, r.id""",  # noqa: S608
                         (*richtingloos, ACCOUNT, *(ids or []))).fetchall()
    uit = []
    for r in rijen:
        if oordeel_voor(conn, r) is None:
            uit.append(r)
        if len(uit) >= max_n:
            break
    return uit


def _knoop(conn, eid) -> str:
    e = conn.execute("""SELECT e.name, e.type, ro.name AS rol FROM entities e
                        LEFT JOIN roles ro ON ro.id = e.primary_role_id WHERE e.id = ?""",
                     (eid,)).fetchone()
    if e is None:
        return f"#{eid}"
    extra = ", ".join(x for x in (e["type"], vocab.weergave_naam(e["rol"]) if e["rol"] else None) if x)
    return f"{e['name']} ({extra})" if extra else e["name"]


def _kort(tekst, n=280) -> str:
    tekst = " ".join((tekst or "").split())
    return tekst if len(tekst) <= n else tekst[:n - 1] + "…"


def context_van(conn, rel) -> str:
    rt = rel["relation_type"]
    regels = [f"Verband: {_knoop(conn, rel['source_id'])} → {_knoop(conn, rel['target_id'])}",
              f"Type: {vocab.relatie_label(rt)} — {vocab.RICHTING_PER_TYPE.get(rt, 'bron beïnvloedt doel')}"]
    if rel["functie"]:
        regels.append(f"Functie: {rel['functie']}")
    if rel["mechanism_id"]:
        m = conn.execute("""SELECT m.name, m.description, sr.name AS van, tr.name AS naar
                            FROM mechanisms m LEFT JOIN roles sr ON sr.id = m.source_role_id
                            LEFT JOIN roles tr ON tr.id = m.target_role_id WHERE m.id = ?""",
                         (rel["mechanism_id"],)).fetchone()
        if m:
            richting = (f"; theorierichting {vocab.weergave_naam(m['van']) or '?'} → "
                        f"{vocab.weergave_naam(m['naar']) or '?'}") if (m["van"] or m["naar"]) else ""
            regels.append(f"Mechanisme: {vocab.weergave_naam(m['name'])}{richting} — "
                          f"{_kort(m['description'], 200)}")
    if rel["description"]:
        regels.append(f"Beschrijving: {_kort(rel['description'])}")
    claim = conn.execute("""SELECT claim FROM arguments WHERE relation_id = ? AND NOT vervangen
                            AND parent_argument_id IS NULL AND stance = 'supporting'
                            AND COALESCE(property, 'existence') = 'existence'
                            AND status NOT IN ('verworpen', 'verouderd')
                            ORDER BY (status = 'geverifieerd') DESC, id LIMIT 1""",
                         (rel["id"],)).fetchone()
    if claim:
        regels.append(f"Bewering: {_kort(claim['claim'])}")
    return "\n".join(regels)


def prompt_voor(conn, groep) -> str:
    delen = ["Toets de richting van elk van deze verbanden. Geef per verband één oordeel met "
             "hetzelfde nr."]
    for nr, rel in enumerate(groep, 1):
        delen.append(f"\n[{nr}] {context_van(conn, rel)}")
    return "\n".join(delen)


def _vraag(groep, model) -> dict[int, dict]:
    conn = db()
    try:
        prompt = prompt_voor(conn, groep)
    finally:
        conn.close()
    antwoord = bc.vraag_model(prompt, SCHEMA, systeem=SYSTEM_PROMPT, model=model)
    uit = {}
    for o in (antwoord or {}).get("oordelen") or []:
        try:
            i = int(o.get("nr")) - 1
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(groep) and o.get("oordeel") in ("juist", "omgekeerd", "richtingloos",
                                                         "twijfel"):
            uit[i] = {"verdict": o["oordeel"], "reden": (o.get("reden") or "").strip()}
    return uit


def toets_groep(groep) -> dict[int, dict]:
    """Haiku over de hele groep; wat Haiku wil veranderen, beoordeelt Sonnet blind opnieuw.
    → {index: {verdict, reden, model}} (ontbreekt = technisch, later opnieuw)."""
    eerste = _vraag(groep, MODEL)
    uit, bevestig = {}, []
    for i, o in eerste.items():
        if o["verdict"] in WIJZIGINGEN:
            bevestig.append(i)
        else:
            uit[i] = dict(o, model=MODEL)
    if bevestig:
        tweede = _vraag([groep[i] for i in bevestig], MODEL_BEVESTIGING)
        for j, i in enumerate(bevestig):
            o2 = tweede.get(j)
            if o2 is None:
                continue  # geen bevestiging: later opnieuw, niets vastleggen
            o1 = eerste[i]
            model = f"{MODEL}+{MODEL_BEVESTIGING}"
            if o2["verdict"] == o1["verdict"]:
                uit[i] = {"verdict": o1["verdict"], "reden": o2["reden"] or o1["reden"],
                          "model": model}
            else:
                uit[i] = {"verdict": "twijfel", "model": model,
                          "reden": f"oneens — {MODEL}: {o1['verdict']} ({o1['reden']}); "
                                   f"{MODEL_BEVESTIGING}: {o2['verdict']} ({o2['reden']})"}
    return uit


def toets_body(rel, uitkomst) -> dict:
    """De body voor POST /api/richtingtoets: het oordeel over het verband zoals het nu is."""
    return {"relation_id": rel["id"], "relatie_hash": richting_hash(rel),
            "verdict": uitkomst["verdict"], "reden": uitkomst["reden"] or "zonder toelichting",
            "model": uitkomst.get("model")}


def post_toets(api, token, rel, uitkomst) -> tuple[int, dict]:
    body = toets_body(rel, uitkomst)
    req = urllib.request.Request(f"{api}/api/richtingtoets", data=json.dumps(body).encode(),
                                 method="POST", headers={"Authorization": f"Bearer {token}",
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


def draai(*, api=DEFAULT_API, token_pad=DEFAULT_TOKEN, max_n=200, droog=False, ids=None,
          batch=BATCH, parallel=2, meld=print) -> dict:
    """Eén ronde. → {bekeken, juist, omgekeerd, richtingloos, twijfel, technisch, geschreven,
    fouten}."""
    token = None
    if not droog:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad} (scripts/create_user.py "
                             f"{ACCOUNT} --kind agent --provenance ... --new-token --save)")
    conn = db()
    try:
        if not bc.heeft_tabel(conn, "richting_toetsen"):
            return {"gestart": False, "reden": "tabel richting_toetsen ontbreekt "
                                               "(scripts/migrate_add_richting_toetsen.py)"}
        items = kandidaten(conn, max_n=max_n, ids=ids)
    finally:
        conn.close()
    meld(f"Richtingtoets: {len(items)} verband(en){' (droog)' if droog else ''}")
    tel = {"bekeken": 0, "juist": 0, "omgekeerd": 0, "richtingloos": 0, "twijfel": 0,
           "technisch": 0, "geschreven": 0, "fouten": 0}
    groepen = [items[i:i + max(1, batch)] for i in range(0, len(items), max(1, batch))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        toekomst = {pool.submit(toets_groep, g): g for g in groepen}
        for f in concurrent.futures.as_completed(toekomst):
            groep = toekomst[f]
            try:
                oordelen = f.result()
            except Exception as exc:  # noqa: BLE001 - één fout stopt de ronde niet
                meld(f"  · groep van {len(groep)}: later opnieuw — {str(exc)[:160]}")
                oordelen = {}
            for i, rel in enumerate(groep):
                tel["bekeken"] += 1
                uitkomst = oordelen.get(i)
                if uitkomst is None:
                    tel["technisch"] += 1
                    continue
                tel[uitkomst["verdict"]] += 1
                regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                         "relation_id": rel["id"], "type": rel["relation_type"], **uitkomst}
                if not droog:
                    status, antwoord = post_toets(api, token, rel, uitkomst)
                    regel["http"] = status
                    if status in (200, 201):
                        tel["geschreven"] += 1
                    else:
                        tel["fouten"] += 1
                        regel["fout"] = antwoord.get("error")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with open(LOG_PATH, "a", encoding="utf-8") as log:
                        log.write(json.dumps(regel, ensure_ascii=False) + "\n")
                if uitkomst["verdict"] != "juist":
                    c2 = db()
                    try:
                        wat = context_van(c2, rel).splitlines()[0]
                    finally:
                        c2.close()
                    meld(f"  · #{rel['id']} {wat[9:]}: {uitkomst['verdict']} "
                         f"[{uitkomst.get('model')}] — {uitkomst['reden'][:160]}")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max", type=int, default=200, help="hooguit zoveel verbanden")
    ap.add_argument("--ids", default="", help="alleen deze relatie-id's: 12,34")
    ap.add_argument("--batch", type=int, default=BATCH, help="verbanden per modelaanroep")
    ap.add_argument("--parallel", type=int, default=2, help="gelijktijdige modelaanroepen")
    ap.add_argument("--droog", action="store_true", help="toets, maar schrijf niets")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    tel = draai(api=args.api, token_pad=args.token, max_n=args.max, droog=args.droog, ids=ids,
                batch=args.batch, parallel=args.parallel)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
