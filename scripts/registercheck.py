#!/usr/bin/env python3
"""Registercheck — het onafhankelijke A1-oordeel voor registerfeiten (Uitbreiding C, 2026-10-07).

Een registerfeit (tools/registers/naar_model.py, account `register-import`) draagt als citaat de
letterlijke recordregel uit een bewaarde registeruitgave (methode `officieel_register_scrape`,
bron met cluster_key 'register:<bron>', page '<bron>/<uitgave>', section = recordsleutel). Deze
check doet zonder LLM wat de bronchecker met een LLM doet, maar dan precies:

  1. de uitgave staat lokaal (data/registers/<bron>/) en haar sha256 klopt nog;
  2. het record bestaat in die uitgave en de recordregel is letterlijk het citaat;
  3. de eindpunten van het verband horen bij dat record (per register: <module>.controleer):
     - register van overheidsorganisaties (oo.py): de organisatie (externe id 'oo'), de
       ambtsdrager (externe id 'oo' = 'm:<medewerker>', en de achternaam staat in de naam) of de
       partij (dezelfde partijtabel als de import);
     - Tweede Kamer (tk.py): het Kamerlid (externe id 'tk_persoon', achternaam en voorletter
       passen), de Tweede Kamer (oo:19432) of de fractiepartij (een fractie die geen landelijke
       partij is: de partijknoop onder de fractienaam), een commissiezetel: de commissie onder
       tk.commissie_naam, en bij nevenfuncties, loopbaan, reizen en geschenken: de organisatie
       staat in de recordregel;
     - Europees Parlement (ep.py): de Europarlementariër (externe id 'ep_mep'), het Europees
       Parlement (wikidata:Q8889) of de nationale partij;
     - lobbyistenregister (lobby.py, de pdf zelf is de uitgave): 'lobbyt' met de Tweede Kamer
       als doel, en de organisatie staat in de recordregel;
     - SER-samenstelling (ser.py, de pagina van ser.nl is de uitgave): 'lidmaatschap' met de SER
       (oo:28455002) als doel, en de organisatie is die uit het record;
     - gemeentelijke indeling (cbs.py, CBS 'Gebieden in Nederland'): 'controle' van de provincie
       uit het record (haar oo-id) naar de gemeente uit het record (haar tooi-code, of de oo-id die
       koppelingen.json vastlegt);
     - openbare agenda's van bewindspersonen (agenda.py): 'lobbyt' met het ministerie van de
       bewindspersoon (zijn oo-id) als doel, en de organisatie staat in de afspraak;
     - nevenfunctieregister Rechtspraak (rechtspraak.py, via Open Rechtspraak): de rechter
       (externe id 'rechtspraak', achternaam in de naam) en de instantie, functie of soort uit het
       record; types bestuurder/adviseur/lidmaatschap/personeel/eigendom/ambt;
     - inspraak bij Kamercommissies (tk_inspraak.py, gegevensmagazijn): 'lobbyt'/'adviseur' van een
       organisatie naar de voortouwcommissie (tk.commissie_naam); de organisatie staat in het
       indiener-, genodigde- of tegenpartijdeel; geen privépersoon en niet op eigen titel;
     - benoemingen in de Staatscourant (staatscourant.py, SRU van repository.overheid.nl): de
       benoemde persoon en de organisatie uit het besluit; types ambt/bestuurder;
     - giften aan politieke partijen (giften.py, Wfpp-overzichten van BZK; de ods is de
       uitgave): 'donor'/'financiering' naar de partij uit het record; de gever staat in de
       recordregel (rechtsvorm-ongevoelig, giften.zelfde_gever); een natuurlijk persoon alleen met
       passende achternaam en voorletter, nooit een persoon als eindpunt van een organisatierecord;
     - netwerk van Nederlandse Europarlementariërs (ep_netwerk.py: EP Open Data, verklaringen en
       vergaderingen op europarl.europa.eu, transparantieregister): het lid via 'ep_mep' + naam; de
       organisatie uit de recordtekst of het transparantieregister; commissieknoop
       '<commissie> (Europees Parlement)';
     - AFM-meldingenregisters (afm.py; export.aspx van afm.nl, XML): substantiële deelnemingen →
       eigendom/zeggenschap/investering van de meldingsplichtige (bron) naar de uitgevende
       instelling (doel); 5:48 Wft en MAR 19 (alleen bestuur of toezicht bij de instelling zelf)
       → 'bestuurder' tussen persoon (achternaam + voorletters) en instelling (kvk/lei,
       afm_koppelingen.json of naam + rechtsvorm).

Klopt alles → 'klopt'; klopt het record of een eindpunt niet → 'klopt-niet' met de reden.
Ontbreekt de uitgave, dan geen oordeel (wordt gemeld). Het oordeel gaat via
POST /api/arguments/<id>/herverificatie onder het eigen account `registercheck` (bijdrager,
nooit de auteur): de A7-poort telt het als onafhankelijke A1, en een registerfeit volgt het
structuurpad (server.py: _alleen_registercitaties). De bronchecker en de bronzoeker slaan
registerargumenten over (REGISTER_ARG_SQL), zodat hun latere oordeel dit niet overschrijft.

Draait als stap 2b van scripts/automatische_beoordeling.py; los:
    python3 scripts/registercheck.py [--droog] [--max N]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "registers"))
import afm  # noqa: E402
import agenda  # noqa: E402
import cbs  # noqa: E402
import ep  # noqa: E402
import ep_netwerk  # noqa: E402
import giften  # noqa: E402
import lobby  # noqa: E402
import oo  # noqa: E402
import rechtspraak  # noqa: E402
import ser  # noqa: E402
import staatscourant  # noqa: E402
import tk  # noqa: E402
import tk_inspraak  # noqa: E402
from common import schoon  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
TOKEN = ROOT / "data" / "tokens" / "registercheck.token"
API = "http://127.0.0.1:5000"
ACCOUNT = "registercheck"
BRONNEN = {"oo": oo, "tk": tk, "ep": ep, "lobby": lobby, "ser": ser, "cbs": cbs, "agenda": agenda, "rechtspraak": rechtspraak,
            "tk_inspraak": tk_inspraak, "staatscourant": staatscourant, "giften": giften,
            "ep_netwerk": ep_netwerk, "afm": afm}

# Een argument waarvan ELKE citatie een registerregel is (alias a = arguments). Gedeeld met
# scripts/bronchecker.py en scripts/bronzoeker.py: die slaan zulke argumenten over.
REGISTER_ARG_SQL = """(
    EXISTS (SELECT 1 FROM citations rc WHERE rc.argument_id = a.id)
    AND NOT EXISTS (
        SELECT 1 FROM citations rc JOIN sources rs ON rs.id = rc.source_id
        WHERE rc.argument_id = a.id
          AND NOT (COALESCE(rc.methode, '') = 'officieel_register_scrape'
                   AND TRIM(COALESCE(rc.quote, '')) <> ''
                   AND COALESCE(rs.cluster_key, '') LIKE 'register:%')))"""
# NB COALESCE: zonder werd NULL (citatie zonder methode, de meeste) als 'register' gelezen.


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def kandidaten(conn, max_n: int | None = None) -> list[sqlite3.Row]:
    rijen = conn.execute(f"""
        SELECT a.* FROM arguments a
        WHERE a.status = 'voorgesteld' AND NOT a.vervangen AND {REGISTER_ARG_SQL}
          AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'herverificatie' AND o.door = ?)
        ORDER BY a.id""", (ACCOUNT,)).fetchall()  # noqa: S608 - vaste SQL
    return rijen[:max_n] if max_n else rijen


def _externe_ids(conn, entity_id: int) -> set[tuple[str, str]]:
    return {(r[0], r[1]) for r in conn.execute(
        "SELECT stelsel, waarde FROM externe_ids WHERE entity_id = ?", (entity_id,))}


def beoordeel(conn, arg: sqlite3.Row) -> tuple[str | None, str, str | None, int | None]:
    """→ (verdict | None, detail, verbatim_span, bron_id). None = geen oordeel mogelijk."""
    citaties = conn.execute("""
        SELECT c.*, s.cluster_key FROM citations c JOIN sources s ON s.id = c.source_id
        WHERE c.argument_id = ?""", (arg["id"],)).fetchall()
    rel = conn.execute("SELECT * FROM relations WHERE id = ?", (arg["relation_id"],)).fetchone() \
        if arg["relation_id"] else None
    if rel is None:
        return ("klopt-niet", "registercheck: registerargument zonder verband", None, None)
    eindpunten = []
    for eid in (rel["source_id"], rel["target_id"]):
        rij = conn.execute("SELECT id, name, type FROM entities WHERE id = ?", (eid,)).fetchone()
        eindpunten.append({"id": eid, "name": rij["name"], "type": rij["type"],
                           "ids": _externe_ids(conn, eid)})
    for c in citaties:
        bron, _, uitgave = (c["page"] or "").partition("/")
        module = BRONNEN.get(bron)
        if module is None or c["cluster_key"] != f"register:{bron}":
            return ("klopt-niet", f"registercheck: onbekende registerbron '{c['page']}'", None, None)
        try:
            data = module.lees_uitgave(uitgave)
        except module.FormaatFout as e:
            return ("klopt-niet", f"registercheck: uitgave {uitgave} is gewijzigd ({e})", None, None)
        if data is None:
            return (None, f"registercheck: uitgave {bron}/{uitgave} staat niet lokaal", None, None)
        sleutel_r = c["section"] or ""
        rec = module.record(uitgave, sleutel_r)
        if rec is None:
            return ("klopt-niet", f"registercheck: record {sleutel_r} bestaat niet in uitgave {uitgave}",
                    None, None)
        if schoon(rec["regel"]) != schoon(c["quote"]):
            return ("klopt-niet", f"registercheck: recordregel van {sleutel_r} in uitgave {uitgave} "
                                  f"wijkt af van het citaat", None, None)
        reden = module.controleer(data, sleutel_r, rec, rel["relation_type"], eindpunten)
        if reden:
            return ("klopt-niet", f"registercheck: {reden}", None, None)
    if not citaties:
        return ("klopt-niet", "registercheck: geen citaties", None, None)
    c0 = citaties[0]
    return ("klopt", f"registercheck: record {c0['section']} in uitgave {c0['page']} bevestigt de "
                     f"regel letterlijk; eindpunten gecontroleerd", c0["quote"], c0["source_id"])


def post(token: str, arg_id: int, body: dict, api: str = API) -> tuple[int, dict]:
    req = urllib.request.Request(f"{api}/api/arguments/{arg_id}/herverificatie",
                                 data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def draai(*, droog: bool = False, max_n: int | None = None, meld=print, api: str = API) -> dict:
    conn = db()
    try:
        rijen = kandidaten(conn, max_n)
        oordelen = [(r["id"], *beoordeel(conn, r)) for r in rijen]
    finally:
        conn.close()
    tel = {"klopt": 0, "klopt-niet": 0, "geen_oordeel": 0, "fout": 0}
    if not oordelen:
        meld("Registercheck: niets te doen")
        return tel
    token = None if droog else TOKEN.read_text().strip()
    for arg_id, verdict, detail, span, bron_id in oordelen:
        if verdict is None:
            tel["geen_oordeel"] += 1
            continue
        if droog:
            tel[verdict] += 1
            continue
        status, res = post(token, arg_id, {"verdict": verdict, "detail": detail,
                                           "verbatim_span": span, "bron_id": bron_id}, api)
        if status in (200, 201):
            tel[verdict] += 1
        else:
            tel["fout"] += 1
            meld(f"  ✗ argument #{arg_id}: {status} {res.get('error')}")
    meld(f"Registercheck: {tel['klopt']} klopt, {tel['klopt-niet']} klopt niet, "
         f"{tel['geen_oordeel']} zonder uitgave{', ' + str(tel['fout']) + ' fout' if tel['fout'] else ''}")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--droog", action="store_true")
    ap.add_argument("--max", type=int, default=None)
    a = ap.parse_args()
    draai(droog=a.droog, max_n=a.max)


if __name__ == "__main__":
    main()
