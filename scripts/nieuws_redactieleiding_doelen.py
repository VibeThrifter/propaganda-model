#!/usr/bin/env python3
"""Onderzoeksdoelen: de redactieleiding van de acht hoofdbronnen van de nieuws-app en hun banden
met partijen (eigenaarsbesluit 2026-10-08: "deze info is wel interessant … mag wel meer van dit
soort verbanden laten zien", over Kamran Ullah — VVD-bestuurder, nu hoofdredacteur van De
Telegraaf — en Kees Berghuis — RTL Nieuws, daarna VVD-voorlichting).

Per medium één doel in de bestaande wachtrij `nieuws_doelen` (soort 'organisatie', sleutel
'redactieleiding:<medium>'), voor de missie `nieuws-scout` (zie § "Doelen 'redactieleiding:…'"
in missies/nieuws_scout_brief.md): wie leidt de redactie (hoofdredacteur, adjuncten), wie leidt
de politieke verslaggeving (chef politiek / Haagse redactie) en wie zijn de bekendste politieke
verslaggevers en presentatoren — en welke gedocumenteerde banden hebben zij met partijen
(lidmaatschap, kandidatuur, partij- of fractiefunctie, voorlichter/woordvoerder, denktank) en
overstappen tussen politiek en media. De context noemt wie het model al kent, zodat de scout
aanvult en niet dubbelt.

Standaard droog: toont de doelen. Met --indienen gaan ze via POST /api/nieuws/doelen (account
'nieuws-agent', upsert op de sleutel: opnieuw draaien dubbelt niets). Alles wat de scout daarna
indient, landt 'voorgesteld' en gaat langs de automatische beoordeling.

Elk kwartaal opnieuw (eigenaar 2026-10-09: redacties veranderen, een nieuwe hoofdredacteur of
een verslaggever die naar een partij overstapt): --periodiek zet alleen de doelen opnieuw in de
wachtrij die meer dan --na-dagen (90) dagen geleden afgerond zijn ("opnieuw": true), en een doel
dat er nog niet is. Een doel dat open of bezig is, blijft staan. agent_schedule.py draait dit
dagelijks; meestal is er niets te doen.

Gebruik:
    python3 scripts/nieuws_redactieleiding_doelen.py              # droog: toon de doelen
    python3 scripts/nieuws_redactieleiding_doelen.py --indienen   # zet ze in de wachtrij
    python3 scripts/nieuws_redactieleiding_doelen.py --periodiek [--droog]  # alleen wat aan de beurt is
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sqlite3
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_API = "http://127.0.0.1:5000"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "nieuws-agent.token"
PRIORITEIT = 80.0  # boven de gewone namen uit het nieuws (± 70–75), onder spoed (≥ 90)
NA_DAGEN = 90      # een afgerond doel komt na een kwartaal opnieuw
AFGEROND = ("klaar", "niets_gevonden", "overgeslagen", "twijfel", "fout")

# De acht hoofdbronnen van de nieuws-app (sinds 2026-10-07), met hun onderdelen in het model
MEDIA = (
    ("NOS", ("NOS", "NOS-hoofdredactie")),
    ("RTL Nieuws", ("RTL Nieuws", "Stichting RTL Nieuws")),
    ("NU.nl", ("NU.nl",)),
    ("AD", ("AD (Algemeen Dagblad)",)),
    ("De Telegraaf", ("De Telegraaf",)),
    ("Het Parool", ("Het Parool",)),
    ("de Volkskrant", ("de Volkskrant",)),
    ("Trouw", ("Trouw",)),
)
BAND_TYPES = ("personeel", "dienstverband", "bestuurder", "woordvoerder_van", "adviseur",
              "draaideur", "lidmaatschap")

OPDRACHT = (
    "Redactieleiding en politieke verslaggeving van {medium}: wie zijn (of waren de afgelopen "
    "tien jaar) hoofdredacteur en adjunct-hoofdredacteur, wie leidt de politieke verslaggeving "
    "(chef politiek / Haagse redactie), en wie zijn de drie tot zes bekendste politieke "
    "verslaggevers en presentatoren? Leg per persoon de functie bij {medium} vast (dienstverband "
    "of personeel, gedateerd) en zoek gedocumenteerde banden met partijen en de politiek: "
    "partijlidmaatschap of -bestuur, een kandidatuur (Kiesraad-lijst), een functie bij een "
    "partij, fractie of bewindspersoon (voorlichter, woordvoerder, beleidsmedewerker), een "
    "wetenschappelijk bureau of denktank, en overstappen tussen politiek en media in beide "
    "richtingen (draaideur, gedateerd). Alleen de publieke rol; alleen wat een bron bij naam "
    "zegt; geen afleiding uit stemgedrag of opinies; privézaken nooit. Eén feit per argument, "
    "in neutrale eigen woorden."
)
BRONNEN = ("colofon en eigen aankondigingen van het medium", "persberichten van de uitgever "
           "(DPG Media, Mediahuis, NPO/NOS, RTL)", "Villamedia", "Parlement.com",
           "kandidatenlijsten van de Kiesraad", "sites van partijen en hun wetenschappelijke "
           "bureaus", "LinkedIn alleen achter de snelheidsrem (zie de brief)")


def slug(tekst: str) -> str:
    t = unicodedata.normalize("NFKD", tekst).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def bekend(conn, ids: list[int]) -> list[dict]:
    """Personen die het model al aan dit medium koppelt (goedgekeurd), met functie en periode."""
    if not ids:
        return []
    plek = ",".join("?" * len(ids))
    rijen = conn.execute(f"""
        SELECT p.name AS naam, r.relation_type, r.functie, r.active_from, r.active_until
        FROM relations r
        JOIN entities p ON p.id = CASE WHEN r.source_id IN ({plek}) THEN r.target_id
                                       ELSE r.source_id END
        WHERE (r.source_id IN ({plek}) OR r.target_id IN ({plek}))
          AND p.type = 'persoon' AND r.status = 'goedgekeurd' AND NOT r.vervangen
          AND r.relation_type IN ({",".join("?" * len(BAND_TYPES))})
        ORDER BY COALESCE(r.active_until, '9999') DESC, p.name""",  # noqa: S608
                         [*ids, *ids, *ids, *BAND_TYPES]).fetchall()
    uit, gezien = [], set()
    for r in rijen:
        if r["naam"] in gezien:
            continue
        gezien.add(r["naam"])
        periode = f"{r['active_from'] or '?'}–{r['active_until'] or 'nu'}"
        uit.append({"naam": r["naam"], "band": r["relation_type"],
                    "functie": r["functie"], "periode": periode})
    return uit[:40]


def doelen(conn) -> list[dict]:
    uit = []
    for medium, namen in MEDIA:
        ids = [r["id"] for r in conn.execute(
            f"SELECT id FROM entities WHERE name IN ({','.join('?' * len(namen))}) "  # noqa: S608
            "AND status = 'goedgekeurd' AND NOT vervangen ORDER BY id", namen)]
        if not ids:
            print(f"  ! {medium}: niet in het model — overgeslagen", file=sys.stderr)
            continue
        uit.append({
            "sleutel": f"redactieleiding:{slug(medium)}",
            "naam": f"Redactieleiding {medium}",
            "soort": "organisatie",
            "entity_id": ids[0],
            "rol_categorie": "media",
            "rol_hint": "hoofdredactie, adjuncten, chef politiek, politieke verslaggevers en "
                        "presentatoren — en hun banden met partijen",
            "prioriteit": PRIORITEIT,
            "context": {
                "soort_doel": "redactieleiding",
                "opdracht": OPDRACHT.format(medium=medium),
                "medium_entiteiten": ids,
                "bekend_in_model": bekend(conn, ids),
                "bronnen": list(BRONNEN),
                "aanleiding": "Kamran Ullah (VVD-bestuur Amsterdam-West 2006–2010, nu "
                              "hoofdredactie De Telegraaf) en Kees Berghuis (RTL Nieuws → "
                              "VVD-voorlichting) — de eigenaar wil meer van zulke verbanden "
                              "zien (2026-10-08).",
            },
        })
    return uit


def post(api: str, token: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(f"{api}/api/nieuws/doelen", data=json.dumps(body).encode(),
                                 method="POST", headers={"Authorization": f"Bearer {token}",
                                                         "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except json.JSONDecodeError:
            return e.code, {}


def aan_de_beurt(conn, lijst: list[dict], na_dagen: int = NA_DAGEN,
                 nu: datetime.datetime | None = None) -> list[dict]:
    """De doelen die (opnieuw) in de wachtrij moeten: nog niet aanwezig, of afgerond en ouder
    dan na_dagen. Elk krijgt "opnieuw": True als het al bestond."""
    nu = nu or datetime.datetime.now()
    stand = {r["sleutel"]: r for r in conn.execute(
        "SELECT sleutel, status, bijgewerkt FROM nieuws_doelen WHERE sleutel LIKE 'redactieleiding:%'")}
    uit = []
    for d in lijst:
        r = stand.get(d["sleutel"])
        if r is None:
            uit.append(d)
            continue
        if r["status"] not in AFGEROND:
            continue
        try:
            bijgewerkt = datetime.datetime.fromisoformat(str(r["bijgewerkt"])[:19])
        except ValueError:
            continue
        if (nu - bijgewerkt).days >= na_dagen:
            uit.append({**d, "opnieuw": True})
    return uit


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--indienen", action="store_true", help="echt in de wachtrij zetten")
    ap.add_argument("--periodiek", action="store_true",
                    help=f"alleen wat aan de beurt is (afgerond > --na-dagen geleden, of nieuw)")
    ap.add_argument("--na-dagen", type=int, default=NA_DAGEN)
    ap.add_argument("--droog", action="store_true", help="met --periodiek: niets indienen")
    args = ap.parse_args()
    conn = db()
    try:
        lijst = doelen(conn)
        if args.periodiek:
            lijst = aan_de_beurt(conn, lijst, args.na_dagen)
    finally:
        conn.close()
    if args.periodiek:
        if not lijst:
            print("Redactieleiding: niets aan de beurt.")
            return
        if args.droog:
            for d in lijst:
                print(f"(droog) {d['sleutel']}{' — opnieuw' if d.get('opnieuw') else ''}")
            return
        token = Path(args.token).read_text().strip()
        for d in lijst:
            status, antwoord = post(args.api, token, d)
            print(f"{d['sleutel']}{' (opnieuw)' if d.get('opnieuw') else ''}: {status} "
                  f"{antwoord.get('error') or ''}".rstrip())
        return
    if not args.indienen:
        for d in lijst:
            print(f"{d['sleutel']}: {d['naam']} (entiteit #{d['entity_id']}, "
                  f"{len(d['context']['bekend_in_model'])} persoon/personen al in het model)")
            for p in d["context"]["bekend_in_model"][:8]:
                print(f"    · {p['naam']} — {p['band']}{' (' + p['functie'] + ')' if p['functie'] else ''}"
                      f", {p['periode']}")
        print(f"\nDroog: {len(lijst)} doel(en). Met --indienen gaan ze in de wachtrij.")
        return
    token = Path(args.token).read_text().strip()
    for d in lijst:
        status, antwoord = post(args.api, token, d)
        print(f"{d['sleutel']}: {status} {antwoord.get('error') or ''}".rstrip())


if __name__ == "__main__":
    main()
