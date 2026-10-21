#!/usr/bin/env python3
"""Datumzoeker per overheidsorganisatie (eigenaarsbesluit 2026-10-15: "fix alles .. met haiku en op
een efficiënte maar klopende manier").

Een gemeente heeft 6–10 wethouders zonder begin in het model. Per persoon zoeken kost een
web-zoektocht per verband; hier zoekt het model per organisatie één keer (het collegepagina of
het nieuws over de installatie) en geeft per persoon het begin van het ambt met een letterlijk
citaat. Het script controleert elk citaat zelf, net als datumzoeker.py:
  - de bron wordt opgehaald en het citaat staat er letterlijk in (bronzoeker.natrekken);
  - de pagina noemt de organisatie bij naam;
  - het citaat noemt de achternaam van de persoon (registernamen hebben voorletters, de pagina
    de voornaam: de achternaam met tussenvoegsel beslist, nooit de voorletters alleen);
  - het citaat noemt het jaartal van de datum;
  - alleen een leeg begin, geen datum in de toekomst, nooit raden.
Wat klopt wordt een aspect-argument (property active_from) op het verband; daarna beslissen de
bronchecker (A1), de stemtoets en stap 10c van de uurronde zoals bij elke datum. Niets gevonden
→ looptijd_onderzoek 'niets_gevonden' (pas na 30 dagen opnieuw).

Model: Haiku (DATUMZOEKER_MODEL). Account `datumzoeker`.

    python3 scripts/datumzoeker_gemeente.py [--droog] [--max 20] [--ids 123,456] [--type gemeente]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "registers"))
import bronchecker as bc  # noqa: E402
import bronzoeker as bz  # noqa: E402
import common  # noqa: E402
import datumzoeker as dz  # noqa: E402

REGELS = (
    "Je zoekt in een onderzoeksdatabase over het Nederlandse bestuur wanneer bestuurders hun "
    "ambt aanvaardden, zo precies als de bron het zegt (jaar, jaar-maand of datum; nooit "
    "preciezer dan de bron). Een datum telt alleen met een letterlijk citaat van de pagina dat "
    "de datum noemt en over deze persoon in dit ambt bij deze organisatie gaat. Het begin is "
    "de beëdiging of installatie in het ambt waarin de persoon NU zit; een eerdere termijn of "
    "een ander ambt is geen begin, en de verkiezingsdatum of de datum van het coalitieakkoord "
    "ook niet. Raad nooit: geen bron, dan gevonden=false voor die persoon. Antwoord alleen met "
    "het gevraagde JSON."
)
_BRON = dz._BRON
SCHEMA = {
    "type": "object",
    "properties": {"personen": {"type": "array", "items": {
        "type": "object",
        "properties": {"nr": {"type": "integer"}, "gevonden": {"type": "boolean"},
                       "begin": {"type": "string"}, "bron": _BRON},
        "required": ["nr", "gevonden", "begin", "bron"], "additionalProperties": False}},
        "toelichting": {"type": "string"}},
    "required": ["personen", "toelichting"], "additionalProperties": False,
}


def basis_naam(naam: str) -> str:
    m = re.match(r"^([^()]*?)\s*\(.*\)\s*$", naam)
    return (m.group(1) if m else naam).strip()


def achternaam_sleutel(naam: str) -> str | None:
    n = common.ontleed_naam(basis_naam(naam))
    achter = common.sleutel(f"{n.get('tussenvoegsel') or ''} {n.get('achternaam') or ''}")
    return achter or None


def kandidaten_groepen(conn, ids=None, soort=None):
    alle = dz.kandidaten(conn, ids)
    groepen = defaultdict(list)
    for r in alle:
        if r["relation_type"] != "ambt" or r["bron_type"] != "persoon":
            continue
        if soort and not r["doel_naam"].lower().startswith(soort):
            continue
        if not r["doel_naam"].lower().startswith(("gemeente ", "provincie ", "waterschap ")):
            continue
        groepen[r["doel_id"]].append(r)
    return sorted(groepen.values(), key=lambda g: (min(r["voorrang"] for r in g), -len(g)))


def prompt(groep: list[dict]) -> str:
    org = groep[0]["doel_naam"]
    regels = "\n".join(f"  {i}. {basis_naam(r['bron_naam'])} — {r.get('functie') or 'ambt'}"
                       for i, r in enumerate(groep, 1))
    return (f"Organisatie: {org}.\nPersonen met hun huidige ambt:\n{regels}\n\n"
            f"Zoek per persoon wanneer die het ambt bij {org} aanvaardde (de huidige termijn). "
            "Zoek eerst de collegepagina of de bestuurderspagina van de eigen website van de "
            "organisatie en nieuws over de installatie of beëdiging; een nieuwsbericht van de "
            "gemeente, de regionale omroep of een krant mag ook. Open de pagina met WebFetch en "
            "neem het citaat dat de datum geeft teken voor teken over; het citaat moet de "
            "achternaam van de persoon noemen en het jaartal. Wikipedia en sociale media zijn "
            "geen bron. Geen bron voor een persoon: gevonden=false, lege velden.")


def verwerk(groep, antwoord, droog, api, token, meld):
    org = groep[0]["doel_naam"]
    tel = {"ingediend": 0, "niets": 0, "fout": 0}
    per_nr = {p.get("nr"): p for p in (antwoord.get("personen") or [])}
    for i, r in enumerate(groep, 1):
        p = per_nr.get(i)
        reden = None
        datum = bron = None
        if not p or not p.get("gevonden"):
            reden = "model vond geen bron"
        else:
            datum = dz.schone_datum(p.get("begin"))
            bron = p.get("bron") or {}
            achter = achternaam_sleutel(r["bron_naam"])
            if not datum:
                reden = "geen geldige datum"
            elif not dz.noemt_jaar(bron.get("citaat"), datum):
                reden = f"citaat noemt {datum[:4]} niet"
            elif not achter or achter not in bc.normaliseer(bron.get("citaat") or ""):
                reden = "citaat noemt de achternaam niet"
            else:
                goed, why = bz.natrekken(bron, [org], dz._afkortingen(r))
                if not goed:
                    reden = why
                else:
                    bron = goed
        if reden:
            tel["niets"] += 1
            dz.log({"relatie": r["id"], "waar": "gemeente", "uitkomst": "niets", "web": True,
                    "toelichting": reden}, droog)
            if not droog:
                dz.leg_vast(api, token, r["id"], "niets_gevonden", f"organisatiezoektocht: {reden}")
            continue
        if droog:
            meld(f"  (droog) #{r['id']} {r['bron_naam']}: {datum} — {bron['url']} “{bron['citaat'][:100]}”")
            tel["ingediend"] += 1
            continue
        sid = bz.registreer_bron(api, token, bron)
        if not sid:
            tel["fout"] += 1
            continue
        cit = {"source_id": sid, "quote": bron["citaat"], "methode": "verbatim_quote"}
        nieuw, fout = dz.dien_in(api, token, r, "active_from", datum, cit, None, "web (organisatie)")
        tel["ingediend" if nieuw else "fout"] += 1
        dz.log({"relatie": r["id"], "waar": "gemeente", "uitkomst": "gevonden", "web": True,
                "begin": {"datum": datum, "bron": bron}}, False)
        if fout:
            meld(f"  ✗ #{r['id']}: {fout}")
    return tel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=dz.DEFAULT_API)
    ap.add_argument("--max", type=int, default=20, help="organisaties per run")
    ap.add_argument("--ids", help="alleen deze verbanden")
    ap.add_argument("--type", help="gemeente|provincie|waterschap")
    ap.add_argument("--droog", action="store_true")
    a = ap.parse_args()
    conn = dz.db()
    try:
        groepen = kandidaten_groepen(conn, [int(x) for x in a.ids.split(",")] if a.ids else None, a.type)
    finally:
        conn.close()
    token = None if a.droog else dz.DEFAULT_TOKEN.read_text().strip()
    totaal = {"organisaties": 0, "ingediend": 0, "niets": 0, "fout": 0}
    for groep in groepen[: a.max]:
        totaal["organisaties"] += 1
        antwoord = dz.vraag(prompt(groep), SCHEMA, tools=True, regels=REGELS)
        if not antwoord:
            totaal["fout"] += len(groep)
            print(f"{groep[0]['doel_naam']}: geen antwoord")
            continue
        tel = verwerk(groep, antwoord, a.droog, a.api, token, print)
        for k, v in tel.items():
            totaal[k] += v
        print(f"{groep[0]['doel_naam']}: {tel}")
    print(json.dumps(totaal))
    return 0


if __name__ == "__main__":
    sys.exit(main())
