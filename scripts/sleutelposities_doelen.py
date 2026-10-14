#!/usr/bin/env python3
"""Onderzoeksdoelen: de gaten in de benoemde topfuncties (eigenaar 2026-10-14, "ga verder" op het
voorstel om de dekking uit /partijen → Benoemde topfuncties in de wachtrij te zetten).

partijen.py (`_sleutelposities`) laat zien wie de benoemde topfuncties bekleedt en welke
instituties van belang ontbreken. Dit script zet de gaten per organisatie als één doel in de
bestaande wachtrij `nieuws_doelen` (soort 'organisatie', `context.soort_doel = "sleutelpositie"`)
voor de missie `nieuws-scout` (zie § "Doelen 'leiding:…' en 'instituut:…'" in
missies/nieuws_scout_brief.md). Vier soorten gaten, per organisatie samengevoegd:

  - ontbreekt            een institutie van belang staat niet in het model (Lareb, Raad voor de
                         rechtspraak …) → sleutel 'instituut:<naam>': de organisatie en haar leiding;
  - zonder_leiding       ze staat erin, maar zonder lopende leidinggevende functie (CPB, SER,
                         NOS …) → 'leiding:<id>': wie leidt haar nu en de afgelopen tien jaar;
  - meerdere_houders     een enkelvoudige functie met meer dan één lopende houder (drie SG's bij
                         Defensie) → 'leiding:<id>': wie is de huidige, en het einde van de anderen;
  - politieke_achtergrond  elk ministerie → 'leiding:<id>': gedocumenteerde banden met partijen en
                         de politiek van de secretaris-generaal (nu en de afgelopen tien jaar).

Standaard droog: toont de doelen. Met --indienen gaan ze via POST /api/nieuws/doelen (account
'nieuws-agent', upsert op de sleutel: opnieuw draaien dubbelt niets; een afgerond doel blijft
afgerond, 409). Alles wat de scout daarna indient, landt 'voorgesteld' en gaat langs de
automatische beoordeling. Een gedicht gat verdwijnt vanzelf uit de volgende run.

Gebruik:
    python3 scripts/sleutelposities_doelen.py              # droog: toon de doelen
    python3 scripts/sleutelposities_doelen.py --indienen   # zet ze in de wachtrij
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import partijen  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_API = "http://127.0.0.1:5000"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "nieuws-agent.token"
PRIORITEIT = 80.0  # gelijk aan de redactieleiding: boven niets, onder de namen uit het nieuws

OPDRACHT = {
    "ontbreekt": (
        "{naam} staat nog niet in het model. Leg de organisatie vast (type, bestuurslaag, "
        "oprichting; bij een rijksorganisatie met het register van overheidsorganisaties als bron) "
        "en haar leiding: wie leidt haar nu (de titel zoals de organisatie die noemt, en sinds "
        "wanneer) en wie leidde haar de afgelopen tien jaar (begin en einde)."),
    "zonder_leiding": (
        "{naam} staat in het model, maar zonder lopende leidinggevende functie. Wie leidt de "
        "organisatie nu (titel, sinds wanneer), en wie leidde haar de afgelopen tien jaar (begin "
        "en einde)?"),
    "meerdere_houders": (
        "Het model noemt meer dan één lopende houder van '{functie}' bij {naam}: {houders}. Wie "
        "is de huidige, en wanneer eindigde de functie van de anderen? Leg een einde vast als "
        "aspect-argument 'active_until' op die relatie (relation_id in bekend_in_model), met een "
        "bron die de datum noemt."),
    "politieke_achtergrond": (
        "Heeft de ambtelijke leiding van {naam} (de secretaris-generaal nu en de afgelopen tien "
        "jaar) gedocumenteerde banden met partijen of de politiek: een partijlidmaatschap of "
        "-functie, een kandidatuur, een eerdere functie als bewindspersoon, Kamerlid, politiek "
        "assistent, fractiemedewerker of partijbestuurder, of een overstap tussen politiek en "
        "ambtenarij (draaideur, gedateerd)?"),
}
GRENZEN = (
    "Alleen de publieke rol; alleen wat een bron bij naam zegt. Leg bij elke persoon die je vindt "
    "ook gedocumenteerde banden met partijen vast, maar leid nooit een partijvoorkeur af uit "
    "opinies, stemgedrag of wie iemand benoemde; geen privézaken. Eén feit per argument, in "
    "neutrale eigen woorden. Niets gevonden over partijbanden is een geldige uitkomst.")
BRONNEN = ("de organisatie zelf (organisatie- en jaarverslag, persberichten)",
           "Rijksoverheid.nl en het register van overheidsorganisaties",
           "benoemingsbesluiten in de Staatscourant en ministerraadsberichten",
           "Parlement.com", "kandidatenlijsten van de Kiesraad", "sites van partijen",
           "LinkedIn alleen achter de snelheidsrem (zie de brief)")


def slug(tekst: str) -> str:
    t = unicodedata.normalize("NFKD", tekst).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _houders(f):
    return [{"persoon": h["persoon"]["naam"], "functie": f["functie"], "looptijd": h["looptijd"],
             "afgelopen": h["afgelopen"], "relation_id": h["relation_id"],
             "partijen": [p["naam"] for p in h["partijen"]]} for h in f["houders"]]


def _heeft_tabel(conn, naam):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                        (naam,)).fetchone() is not None


def zonder_titel(conn, entity_id) -> list[dict]:
    """Lopende banden van personen met deze organisatie zonder titel (bestuurder, ambt, in
    dienst): misschien de leiding, maar het model zegt niet in welke functie."""
    if entity_id is None:
        return []
    rijen = conn.execute("""
        SELECT r.id, r.relation_type, r.active_from, p.name
        FROM relations r JOIN entities p
          ON p.id = CASE WHEN r.source_id = ? THEN r.target_id ELSE r.source_id END
        WHERE ? IN (r.source_id, r.target_id) AND p.type = 'persoon'
          AND r.status = 'goedgekeurd' AND NOT r.vervangen
          AND r.relation_type IN ('ambt', 'bestuurder', 'dienstverband', 'personeel')
          AND COALESCE(TRIM(r.functie), '') = ''
          AND (r.active_until IS NULL OR r.active_until >= date('now'))
        ORDER BY COALESCE(r.active_from, '') DESC, p.name LIMIT 15""",
                         (entity_id, entity_id)).fetchall()
    return [{"persoon": r[3], "band": r[1], "sinds": r[2], "relation_id": r[0]} for r in rijen]


def doelen(conn) -> list[dict]:
    """De gaten als doelen, één per organisatie (de gaten van één organisatie samengevoegd)."""
    sp = partijen.compute_overzicht(conn)["sleutelposities"]
    labels = {k: lab for k, lab, _ in partijen.KLASSEN}
    per_org = {}   # sleutel -> doel in opbouw

    def doel(sleutel, naam, klasse, entity_id):
        return per_org.setdefault(sleutel, {
            "sleutel": sleutel, "naam": naam, "soort": "organisatie", "entity_id": entity_id,
            "klasse": klasse, "gaten": [], "opdrachten": [], "bekend": []})

    for i in sp["instituten"]:
        if i["id"] is None:
            d = doel(f"instituut:{slug(i['naam'])}", i["naam"], i["klasse"], None)
            d["gaten"].append("ontbreekt")
            d["opdrachten"].append(OPDRACHT["ontbreekt"].format(naam=i["naam"]))
        elif not i["met_functie"][1]:
            d = doel(f"leiding:{i['id']}", i["naam"], i["klasse"], i["id"])
            d["gaten"].append("zonder_leiding")
            d["opdrachten"].append(OPDRACHT["zonder_leiding"].format(naam=i["naam"]))

    for f in sp["functies"]:
        lopend = [h for h in f["houders"] if not h["afgelopen"]]
        org = f["org"]
        if len(lopend) > 1:
            d = doel(f"leiding:{org['id']}", org["naam"], f["klasse"], org["id"])
            d["gaten"].append("meerdere_houders")
            d["opdrachten"].append(OPDRACHT["meerdere_houders"].format(
                naam=org["naam"], functie=f["functie"],
                houders=", ".join(f"{h['persoon']['naam']} ({h['looptijd'] or 'zonder datum'})"
                                  for h in lopend)))

    ministeries = [(i, naam) for i, naam, meta in conn.execute(
        "SELECT id, name, metadata FROM entities WHERE status = 'goedgekeurd' AND NOT vervangen "
        "AND type = 'overheidsinstelling'")
        if partijen._oo_type({"metadata": meta}) == "Ministerie" or naam.startswith("Ministerie van ")]
    for i, naam in ministeries:
        d = doel(f"leiding:{i}", naam, "ambtelijke_top", i)
        d["gaten"].append("politieke_achtergrond")
        d["opdrachten"].append(OPDRACHT["politieke_achtergrond"].format(naam=naam))

    # Wat het model al over de leiding van elke organisatie weet (aanvullen, niet dubbelen).
    per_id = {}
    for f in sp["functies"]:
        per_id.setdefault(f["org"]["id"], []).extend(_houders(f))
    # Een medium met een redactieleiding-doel (NOS): de hoofdredactie zit daar al in, dit doel
    # gaat over de directie en het bestuur.
    redactie = {r[0]: r[1] for r in conn.execute(
        "SELECT entity_id, sleutel FROM nieuws_doelen WHERE sleutel LIKE 'redactieleiding:%' "
        "AND entity_id IS NOT NULL")} if _heeft_tabel(conn, "nieuws_doelen") else {}
    uit = []
    for d in sorted(per_org.values(), key=lambda d: (partijen.RANG[d["klasse"]], d["naam"].lower())):
        if d["entity_id"] in redactie:
            d["opdrachten"].append(
                f"De hoofdredactie en de politieke verslaggeving vallen onder het doel "
                f"'{redactie[d['entity_id']]}': dit doel gaat over de directie en het bestuur "
                f"(directeur, raad van bestuur, raad van toezicht).")
        rol = "media" if partijen.RANG_GROEP[d["klasse"]] == "media" else "organisatie"
        uit.append({
            "sleutel": d["sleutel"], "naam": f"Leiding {d['naam']}", "soort": "organisatie",
            "entity_id": d["entity_id"], "rol_categorie": rol,
            "rol_hint": f"{labels[d['klasse']]}: leiding nu en de afgelopen tien jaar — en hun "
                        "banden met partijen",
            "prioriteit": PRIORITEIT,
            "context": {
                "soort_doel": "sleutelpositie",
                "gaten": d["gaten"],
                "categorie": labels[d["klasse"]],
                "organisatie": d["naam"],
                "opdracht": " ".join(d["opdrachten"]) + " " + GRENZEN,
                "bekend_in_model": per_id.get(d["entity_id"], [])[:20],
                "banden_zonder_titel": zonder_titel(conn, d["entity_id"]),
                "precedent": "Bij een overheidsorganisatie: relatietype 'ambt' van persoon naar "
                             "organisatie met 'functie' zoals de organisatie of het register hem noemt "
                             "(bv. 'Secretaris-generaal', 'Voorzitter'), mechanisme 'ambtelijke_leiding' "
                             "(#207). Bij een stichting, vereniging, omroep of bedrijf: 'bestuurder' "
                             "(bestuur, directie, raad van toezicht) of 'dienstverband' (bv. "
                             "hoofdredactie) met 'functie', en het mechanisme van vergelijkbare banden. "
                             "Altijd gedateerd; een overstap tussen politiek en ambt of medium als "
                             "'draaideur' (draaideurconstructie, #18). Staat iemand al zonder titel in "
                             "banden_zonder_titel, dien dan geen tweede kale band in.",
                "bronnen": list(BRONNEN),
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--indienen", action="store_true", help="echt in de wachtrij zetten")
    args = ap.parse_args()
    conn = db()
    try:
        lijst = doelen(conn)
    finally:
        conn.close()
    if not args.indienen:
        for d in lijst:
            c = d["context"]
            print(f"{d['sleutel']}: {c['organisatie']} [{c['categorie']}] — {', '.join(c['gaten'])}"
                  f" ({len(c['bekend_in_model'])} houder(s) in het model)")
        print(f"\nDroog: {len(lijst)} doel(en). Met --indienen gaan ze in de wachtrij.")
        return
    token = Path(args.token).read_text().strip()
    tel = {}
    for d in lijst:
        status, antwoord = post(args.api, token, d)
        tel[status] = tel.get(status, 0) + 1
        print(f"{d['sleutel']}: {status} {antwoord.get('error') or ''}".rstrip())
    print(f"\nKlaar: {', '.join(f'{v}× {k}' for k, v in sorted(tel.items()))}.")


if __name__ == "__main__":
    main()
