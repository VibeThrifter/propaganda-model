#!/usr/bin/env python3
"""Stemtoets — de eigen stem van het model blijft neutraal (eigenaarsbesluit 2026-10-08:
"'ondermijnt zo het vertrouwen in de journalistiek' slaat nergens op … het is inderdaad een
aanval, maar deze taal moeten we niet overnemen, dit is duidelijk een politiek spelletje … dat
is niet aan ons om zomaar over te nemen in onze eigen retoriek … waak hier streng voor").

De eigen stem zegt wat er gebeurde: wie deed of zei wat, wanneer, waar, in welke functie. Een
oordeel over gevolgen of motieven ("ondermijnt het vertrouwen", "bedreigt de persvrijheid"),
een etiket ("rechts-populistisch", "neoliberale consensus", "linkse media", "NAVO-gezind") of de
retoriek van één kant staat er alleen als citaat, met naam toegeschreven aan wie het uitsprak.

Kandidaten, in deze volgorde (per ronde begrensd):
1. elk voorstel in de praktijklaag (argument 'voorgesteld', niet van dit account, geen
   letterlijke registerregel) zonder oordeel over zijn huidige tekst — A7 merget het pas na
   'neutraal';
2. de veegronde over wat er al staat: gemergede argument-claims en de beschrijvingen van
   goedgekeurde relaties en entiteiten — eerst wat het strenge lexicon aanwijst
   (validation.EIGEN_STEM_STRENG), dan het ruime, dan wat het nieuws toont (nieuws_voorrang,
   nieuws_doelen), dan de rest.
Claude Sonnet (via de `claude`-CLI, zonder tools) leest per tekst waar ze over gaat en de
citaten van haar bronnen (zodat een oordeel aan wie het uitsprak kan worden toegeschreven) en
zegt 'neutraal' of 'niet_neutraal', met reden en een neutrale herformulering: dezelfde feiten,
het oordeel weggelaten of als citaat toegeschreven, niets erbij. Meerdere teksten per aanroep.

Het oordeel gaat naar POST /api/stemtoets (account 'stemtoets', nooit de auteur) en geldt voor
precies de tekst die het zag (tekst_hash). Wat ermee gebeurt, beslist
scripts/automatische_beoordeling.py: A7 merget geen niet-neutraal voorstel, een niet-neutraal
voorstel komt neutraal opnieuw binnen, gemerged werk krijgt een stemrevisie, een beschrijving
wordt herschreven (werk van een mens herschrijft niemand automatisch).

Gebruik:
    python3 scripts/stemtoets.py --droog --max-veeg 8        # oordelen tonen, niets schrijven
    python3 scripts/stemtoets.py --json                       # echt (voorstellen + veegronde)
    python3 scripts/stemtoets.py --droog --ids argument:2189,entiteit:55
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import hashlib
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
import validation  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "stemtoets"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "stemtoets_log.jsonl"
MODEL = "sonnet"
BATCH = 8
MAX_CITATEN = 3
SOORTEN = ("argument", "relatie", "entiteit")

SYSTEM_PROMPT = (
    "Je bent de stemtoets van een onderzoeksdatabase over het Nederlandse media- en "
    "bestuurssysteem. De database zegt in haar EIGEN STEM alleen wat er gebeurde: wie deed of "
    "zei wat, wanneer, waar, in welke functie, met welke aantallen of documenten. Je toetst of "
    "een tekst die regel volgt.\n"
    "NIET in de eigen stem (dus 'niet_neutraal'):\n"
    "1. een oordeel over gevolgen of effecten ('ondermijnt het vertrouwen in de journalistiek', "
    "'bedreigt de persvrijheid', 'directe bedreiging', 'polariseert', 'schadelijk', 'bevestigt "
    "het narratief');\n"
    "2. een oordeel over motieven of bedoelingen ('om journalisten te intimideren', 'bewust', "
    "'probeert de berichtgeving te sturen') dat de tekst niet aan iemand toeschrijft;\n"
    "3. een etiket of kwalificatie van een partij, persoon, organisatie of medium "
    "('rechts-populistisch', 'extreemrechts', 'radicaal', 'linkse media', 'mainstream', "
    "'NAVO-gezind', 'onderdeel van de neoliberale consensus', 'omstreden', 'complotdenker', "
    "'elite' of 'establishment' als oordeel over een genoemde partij);\n"
    "4. de retoriek of het frame van één kant in eigen woorden ('linkse kerk', 'nepnieuws', "
    "'tuig van de richel' zonder aanhalingstekens of zonder te zeggen wie het zei);\n"
    "5. een versterker zonder feit ('zeer invloedrijk', 'kernpositie', 'machtig', 'berucht', "
    "'kritiekloos').\n"
    "WEL toegestaan: zo'n oordeel als citaat of samenvatting die met naam is toegeschreven aan "
    "wie het uitsprak ('De NVJ noemde de uitspraak ...', 'Volgens de AIVD ...', 'X noemt zich "
    "...'); hoe een partij of organisatie zichzelf noemt of formeel is ingedeeld, als feit "
    "(de VVD noemt zich liberaal en is lid van Liberal International: 'liberale partij' mag; "
    "een etiket dat anderen haar geven niet); neutrale vaktermen voor wat er gebeurde "
    "(eigenaar, adverteerder, woordvoerder, bron, draaideur in de zin van overstappen tussen "
    "functies); jaartallen, functies, aantallen. Een kritisch of onwelgevallig FEIT is neutraal (bijvoorbeeld: 'PVV-leider "
    "Wilders noemde journalisten in 2021 \"tuig van de richel\"').\n"
    "Bij 'niet_neutraal' geef je een herformulering: dezelfde feiten, met de partijen bij naam, "
    "het oordeel weggelaten of — alleen als een meegegeven bron-citaat laat zien wie het "
    "uitsprak — als citaat aan die persoon of organisatie toegeschreven. Voeg geen feiten toe "
    "die niet in de tekst of de citaten staan, en laat geen feit weg dat neutraal is. Blijft er "
    "geen feit over, geef dan een lege herformulering. Kort, zakelijk Nederlands, één tot drie "
    "zinnen. Bij 'neutraal' is de herformulering leeg. Antwoord alleen met het gevraagde JSON."
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
                    "oordeel": {"type": "string", "enum": ["neutraal", "niet_neutraal"]},
                    "reden": {"type": "string"},
                    "herformulering": {"type": "string"},
                },
                "required": ["nr", "oordeel", "reden", "herformulering"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["oordelen"],
    "additionalProperties": False,
}


def tekst_hash(tekst: str | None) -> str:
    """Spiegelt server.stem_hash: sha256 van de tekst met samengevouwen witruimte."""
    return hashlib.sha256(" ".join((tekst or "").split()).encode("utf-8")).hexdigest()


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def heeft_tabel(conn, naam: str) -> bool:
    return bc.heeft_tabel(conn, naam)


def oordeel_voor(conn, soort: str, doel_id: int, tekst: str | None, auteur: str | None):
    """Spiegelt server._stemtoets: het nieuwste oordeel van een ander account dan de auteur
    over precies deze tekst, of None."""
    if not heeft_tabel(conn, "stem_toetsen"):
        return None
    return conn.execute("""
        SELECT verdict, reden, herformulering, door, created_at FROM stem_toetsen
        WHERE soort = ? AND doel_id = ? AND tekst_hash = ?
          AND COALESCE(door, '') <> COALESCE(?, '')
        ORDER BY created_at DESC, id DESC LIMIT 1""",
                        (soort, doel_id, tekst_hash(tekst), auteur)).fetchone()


def _eigen_hashes(conn, soort: str) -> dict[int, str]:
    """{doel_id: tekst_hash} van de oordelen van dit account (om al getoetste teksten over te
    slaan zonder per stuk te zoeken)."""
    if not heeft_tabel(conn, "stem_toetsen"):
        return {}
    return {r[0]: r[1] for r in conn.execute(
        "SELECT doel_id, tekst_hash FROM stem_toetsen WHERE soort = ? AND door = ?",
        (soort, ACCOUNT))}


# ------------------------------------------------------------------ kandidaten
_REGISTER = """EXISTS (SELECT 1 FROM citations c JOIN sources s ON s.id = c.source_id
                       WHERE c.argument_id = a.id AND c.methode = 'officieel_register_scrape'
                         AND s.cluster_key LIKE 'register:%')
               AND NOT EXISTS (SELECT 1 FROM citations c JOIN sources s ON s.id = c.source_id
                       WHERE c.argument_id = a.id AND (c.methode IS NOT 'officieel_register_scrape'
                         OR s.cluster_key NOT LIKE 'register:%'))"""


def _wortel_praktijk(conn, arg) -> tuple[int | None, int | None]:
    """(relation_id, entity_id) van de root van de boom; (None, None) bij een theorie-doel."""
    gezien = set()
    while arg["parent_argument_id"] is not None and arg["id"] not in gezien:
        gezien.add(arg["id"])
        ouder = conn.execute("SELECT * FROM arguments WHERE id = ?",
                             (arg["parent_argument_id"],)).fetchone()
        if ouder is None:
            break
        arg = ouder
    return arg["relation_id"], arg["entity_id"]


def _argumenten(conn, statussen: tuple[str, ...]) -> list[dict]:
    """Argumenten in de praktijklaag met deze statussen, zonder letterlijke registerregels."""
    eigen = _eigen_hashes(conn, "argument")
    rijen = conn.execute(f"""
        SELECT a.* FROM arguments a
        WHERE NOT a.vervangen AND a.status IN ({','.join('?' * len(statussen))})
          AND COALESCE(a.contributed_by, '') <> ?
          AND TRIM(COALESCE(a.claim, '')) <> ''
          AND NOT ({_REGISTER})""", (*statussen, ACCOUNT)).fetchall()  # noqa: S608
    uit = []
    for a in rijen:
        if eigen.get(a["id"]) == tekst_hash(a["claim"]):
            continue  # deze tekst toetste ik al
        rel, ent = _wortel_praktijk(conn, a)
        if not rel and not ent:
            continue  # theorie-argument: de analyse van het model is daar de inhoud
        uit.append({"soort": "argument", "doel_id": a["id"], "tekst": a["claim"],
                    "auteur": a["contributed_by"], "relation_id": rel, "entity_id": ent,
                    "stance": a["stance"], "property": a["property"],
                    "reply": a["parent_argument_id"] is not None})
    return uit


def _beschrijvingen(conn) -> list[dict]:
    """Beschrijvingen van goedgekeurde relaties en entiteiten die nog niet getoetst zijn
    (geen registerknopen: hun tekst komt uit het register)."""
    uit = []
    for soort, tabel in (("relatie", "relations"), ("entiteit", "entities")):
        eigen = _eigen_hashes(conn, soort)
        extra = ("AND NOT EXISTS (SELECT 1 FROM externe_ids x WHERE x.entity_id = t.id)"
                 if tabel == "entities" and heeft_tabel(conn, "externe_ids") else "")
        for r in conn.execute(f"""
                SELECT t.id, t.description,
                       (SELECT changed_by FROM edit_log l WHERE l.table_name = ?
                          AND l.record_id = t.id AND l.action = 'created'
                        ORDER BY l.id LIMIT 1) AS auteur
                FROM {tabel} t WHERE t.status = 'goedgekeurd' AND NOT t.vervangen
                  AND TRIM(COALESCE(t.description, '')) <> '' {extra}""",  # noqa: S608
                              (tabel,)):
            if eigen.get(r["id"]) == tekst_hash(r["description"]):
                continue
            if r["auteur"] == ACCOUNT:
                continue
            uit.append({"soort": soort, "doel_id": r["id"], "tekst": r["description"],
                        "auteur": r["auteur"],
                        "relation_id": r["id"] if soort == "relatie" else None,
                        "entity_id": r["id"] if soort == "entiteit" else None})
    return uit


def _voorrang(conn, items: list[dict]) -> list[dict]:
    """Strenge lexicon-treffers eerst, dan ruime, dan wat het nieuws toont, dan de rest
    (nieuwste eerst binnen elke groep)."""
    relaties, entiteiten = bc.nieuws_voorrang(conn)

    def groep(item):
        if validation.eigen_stem_treffers(item["tekst"]):
            return 0
        if validation.eigen_stem_treffers(item["tekst"], streng=False):
            return 1
        if item.get("relation_id") in relaties or item.get("entity_id") in entiteiten:
            return 2
        return 3

    items = sorted(items, key=lambda i: -i["doel_id"])
    return sorted(items, key=groep)


def kandidaten(conn, max_nieuw=200, max_veeg=40, ids=None) -> list[dict]:
    """Voorstellen eerst (alle, tot ``max_nieuw``), dan de veegronde (``max_veeg``)."""
    if ids:
        uit = []
        for soort, doel_id in ids:
            tabel, kolom = {"argument": ("arguments", "claim"), "relatie": ("relations", "description"),
                            "entiteit": ("entities", "description")}[soort]
            r = conn.execute(f"SELECT {kolom} AS tekst FROM {tabel} WHERE id = ?",  # noqa: S608
                             (doel_id,)).fetchone()
            if r is None or not (r["tekst"] or "").strip():
                continue
            if soort == "argument":
                a = conn.execute("SELECT * FROM arguments WHERE id = ?", (doel_id,)).fetchone()
                rel, ent = _wortel_praktijk(conn, a)
                uit.append({"soort": soort, "doel_id": doel_id, "tekst": r["tekst"],
                            "auteur": a["contributed_by"], "relation_id": rel, "entity_id": ent,
                            "stance": a["stance"], "property": a["property"],
                            "reply": a["parent_argument_id"] is not None})
            else:
                uit.append({"soort": soort, "doel_id": doel_id, "tekst": r["tekst"],
                            "auteur": None,
                            "relation_id": doel_id if soort == "relatie" else None,
                            "entity_id": doel_id if soort == "entiteit" else None})
        return uit
    nieuw = _argumenten(conn, ("voorgesteld",))
    nieuw.sort(key=lambda i: -i["doel_id"])
    veeg = _argumenten(conn, ("ongecontroleerd", "geverifieerd", "betwist",
                              "bronvermelding_nodig")) + _beschrijvingen(conn)
    return nieuw[:max_nieuw] + _voorrang(conn, veeg)[:max_veeg]


# ------------------------------------------------------------------ context
def context_van(conn, item: dict) -> str:
    """Waar de tekst over gaat, in één regel, plus de citaten van haar bronnen."""
    regels = []
    if item["relation_id"]:
        r = conn.execute("""SELECT s.name AS bron, s.type AS st, t.name AS doel, t.type AS tt,
                                   r.relation_type, m.name AS mech
                            FROM relations r JOIN entities s ON s.id = r.source_id
                            JOIN entities t ON t.id = r.target_id
                            LEFT JOIN mechanisms m ON m.id = r.mechanism_id
                            WHERE r.id = ?""", (item["relation_id"],)).fetchone()
        if r:
            verband = (f"het verband '{r['bron']}' ({r['st']}) → '{r['doel']}' ({r['tt']}), "
                       f"relatietype {r['relation_type']}"
                       + (f", mechanisme {r['mech'].replace('_', ' ')}" if r["mech"] else ""))
            if item["soort"] == "relatie":
                regels.append(f"Soort: beschrijving van {verband}")
            else:
                rol = {"supporting": "steunt", "contradicting": "spreekt tegen"}.get(
                    item.get("stance"), "nuanceert")
                wat = "een reactie in de discussie over" if item.get("reply") else f"{rol}"
                regels.append(f"Soort: argument dat {wat} {verband}")
    elif item["entity_id"]:
        e = conn.execute("SELECT name, type FROM entities WHERE id = ?",
                         (item["entity_id"],)).fetchone()
        if e:
            if item["soort"] == "entiteit":
                regels.append(f"Soort: beschrijving van de entiteit '{e['name']}' ({e['type']})")
            else:
                over = (f" (aspect: {item['property'].replace('_', ' ')})"
                        if item.get("property") else "")
                regels.append(f"Soort: argument over de entiteit '{e['name']}' ({e['type']}){over}")
    if item["soort"] == "argument":
        citaten = conn.execute("""
            SELECT c.quote, s.publisher, s.author, s.title, s.date_published
            FROM citations c JOIN sources s ON s.id = c.source_id
            WHERE c.argument_id = ? ORDER BY c.id LIMIT ?""",
                               (item["doel_id"], MAX_CITATEN)).fetchall()
        for c in citaten:
            wie = c["publisher"] or c["author"] or c["title"] or "bron"
            if (c["quote"] or "").strip():
                regels.append(f"Citaat uit de bron ({wie}, {c['date_published'] or 'datum onbekend'}): "
                              f"\"{c['quote'].strip()[:400]}\"")
            else:
                regels.append(f"Bron zonder citaat: {wie} — {(c['title'] or '')[:120]}")
    return "\n".join(regels)


def prompt_voor(conn, groep: list[dict]) -> str:
    delen = ["Toets elk van deze teksten. Geef per tekst één oordeel met hetzelfde nr."]
    for nr, item in enumerate(groep, 1):
        delen.append(f"\n[{nr}] {context_van(conn, item)}\nTekst: \"{item['tekst'].strip()}\"")
    return "\n".join(delen)


def toets_groep(groep: list[dict]) -> dict[int, dict]:
    """→ {index in de groep: {verdict, reden, herformulering}} (ontbreekt = technisch)."""
    conn = db()
    try:
        prompt = prompt_voor(conn, groep)
    finally:
        conn.close()
    antwoord = bc.vraag_model(prompt, SCHEMA, systeem=SYSTEM_PROMPT, model=MODEL)
    uit = {}
    for o in (antwoord or {}).get("oordelen") or []:
        try:
            i = int(o.get("nr")) - 1
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(groep) and o.get("oordeel") in ("neutraal", "niet_neutraal"):
            uit[i] = {"verdict": o["oordeel"], "reden": (o.get("reden") or "").strip(),
                      "herformulering": (o.get("herformulering") or "").strip()
                      if o["oordeel"] == "niet_neutraal" else ""}
    return uit


# ------------------------------------------------------------------ schrijven
def toets_body(item, uitkomst) -> dict:
    """De body voor POST /api/stemtoets: het oordeel over precies deze tekst (tekst_hash);
    "herzien" zodat een oordeel over een gewijzigde tekst het eigen oude oordeel bijwerkt."""
    body = {"soort": item["soort"], "doel_id": item["doel_id"],
            "tekst_hash": tekst_hash(item["tekst"]), "verdict": uitkomst["verdict"],
            "reden": uitkomst["reden"] or "zonder toelichting", "herzien": True}
    if uitkomst.get("herformulering"):
        body["herformulering"] = uitkomst["herformulering"]
    return body


def post_toets(api, token, item, uitkomst) -> tuple[int, dict]:
    body = toets_body(item, uitkomst)
    req = urllib.request.Request(f"{api}/api/stemtoets", data=json.dumps(body).encode(),
                                 method="POST",
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


def draai(*, api=DEFAULT_API, token_pad=DEFAULT_TOKEN, max_nieuw=200, max_veeg=40, droog=False,
          ids=None, batch=BATCH, parallel=2, meld=print) -> dict:
    """Eén ronde. → {bekeken, neutraal, niet_neutraal, technisch, geschreven, fouten}."""
    token = None
    if not droog:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad} (scripts/create_user.py "
                             f"{ACCOUNT} --kind agent --provenance ... --new-token --save)")
    conn = db()
    try:
        items = kandidaten(conn, max_nieuw=max_nieuw, max_veeg=max_veeg, ids=ids)
    finally:
        conn.close()
    meld(f"Stemtoets: {len(items)} tekst(en){' (droog)' if droog else ''}")
    tel = {"bekeken": 0, "neutraal": 0, "niet_neutraal": 0, "technisch": 0, "geschreven": 0,
           "fouten": 0}
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
            for i, item in enumerate(groep):
                tel["bekeken"] += 1
                uitkomst = oordelen.get(i)
                wat = f"{item['soort']} #{item['doel_id']}"
                if uitkomst is None:
                    tel["technisch"] += 1
                    meld(f"  · {wat}: later opnieuw (geen bruikbaar oordeel)")
                    continue
                tel[uitkomst["verdict"]] += 1
                regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                         "soort": item["soort"], "doel_id": item["doel_id"],
                         "tekst": item["tekst"][:600], **uitkomst}
                if not droog:
                    status, antwoord = post_toets(api, token, item, uitkomst)
                    regel["http"] = status
                    if status in (200, 201):
                        tel["geschreven"] += 1
                    else:
                        tel["fouten"] += 1
                        regel["fout"] = antwoord.get("error")
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with open(LOG_PATH, "a", encoding="utf-8") as log:
                        log.write(json.dumps(regel, ensure_ascii=False) + "\n")
                meld(f"  · {wat}: {uitkomst['verdict']} — {uitkomst['reden'][:110]}"
                     + (f"\n      → {uitkomst['herformulering'][:200]}"
                        if uitkomst.get("herformulering") else ""))
    return tel


def parse_ids(spec: str) -> list[tuple[str, int]]:
    uit = []
    for deel in (spec or "").split(","):
        soort, _, nummer = deel.strip().partition(":")
        if soort in SOORTEN and nummer.strip().isdigit():
            uit.append((soort, int(nummer)))
    return uit


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max-nieuw", type=int, default=200, help="hooguit zoveel voorstellen")
    ap.add_argument("--max-veeg", type=int, default=40,
                    help="hooguit zoveel bestaande teksten in de veegronde")
    ap.add_argument("--ids", default="", help="alleen deze: argument:12,relatie:34,entiteit:56")
    ap.add_argument("--batch", type=int, default=BATCH, help="teksten per modelaanroep")
    ap.add_argument("--parallel", type=int, default=2, help="gelijktijdige modelaanroepen")
    ap.add_argument("--droog", action="store_true", help="toets, maar schrijf niets")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    tel = draai(api=args.api, token_pad=args.token, max_nieuw=args.max_nieuw,
                max_veeg=args.max_veeg, droog=args.droog, ids=parse_ids(args.ids) or None,
                batch=args.batch, parallel=args.parallel)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
