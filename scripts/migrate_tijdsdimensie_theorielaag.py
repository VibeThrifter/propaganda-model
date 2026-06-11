#!/usr/bin/env python3
"""
Migratie: tijdsdimensie voor de theorielaag (juni 2026).

Aanleiding: de praktijklaag (entities/relations) draagt al
active_from/active_until, maar de theorielaag (roles/mechanisms/
emergent_effects) is tijdloos. Mechanismen zijn echter historisch
contingent: kijkcijferdisciplinering kan pas bestaan sinds er een
kijkmeterpanel is (1987), algoritmische filtering pas sinds de
algoritmische feed (2006), en het verzuilde bestel werkte vóór de
ontzuiling wezenlijk anders. Zonder tijdsvelden beweert de theorielaag
impliciet dat elk mechanisme altijd heeft gegolden.

Wat deze migratie doet:

1. SCHEMA: voegt active_from/active_until (TEXT, vrij formaat zoals bij
   relations: 'YYYY' of 'YYYY-MM-DD') toe aan roles, mechanisms en
   emergent_effects. NULL = onbegrensd voor zover bekend (default).
   Kolomcheck vooraf -> replay-safe op verse builds waarin schema.sql
   de kolommen al aanmaakt (reconstructie = seed -> enrich -> migrate).

2. DATEERT zes evident technologie- of bestelgebonden mechanismen
   (alleen waar het mechanisme vóór die datum technisch/institutioneel
   onmogelijk was; geen einddatums, ze werken alle zes nog):
   - kijkcijferdisciplinering  1987  continue elektronische kijkmeting
                                     (kijkmeterpanel, nu NMO) bestaat
                                     in NL sinds 1987; minutenanalyse
                                     kan daarvoor niet
   - algoritmische_filtering   2006  engagement-gestuurde feedselectie
                                     bestaat sinds de algoritmische
                                     feed (Facebook News Feed, 2006)
   - algoritmische_socialisatie 2010 opgroeien met algoritmische feeds
                                     als primaire nieuwsbron vereist
                                     smartphone + sociale platforms
                                     (~2010)
   - platform_advertentie_concentratie 2000  online advertentie-
                                     platforms sinds Google AdWords
                                     (2000)
   - platform_journalistiekfinanciering 2015  eerste grote fonds:
                                     Google Digital News Initiative
                                     (2015); de description noemt de
                                     fondsen zelf
   - omroepverzuiling          1930  Zendtijdenbesluit 1930 verdeelt
                                     de zendtijd over de zuilomroepen;
                                     het bestel bestaat nog, dus geen
                                     einddatum

3. RAAKT NIETS ANDERS AAN. scoring.py, influence.py en de viz negeren
   de velden vooralsnog: bewijs telt tijdloos mee in de scores. Een
   tijdsweging van argumenten (ouder bewijs telt lichter) is een aparte
   modelkeuze, net als een tijdslider in de viz. Rollen en emergente
   effecten krijgen wel de kolommen maar nog geen datering (kandidaten:
   rol techplatform ~2000s; omroepsignatuur ~1925 — eerst bron zoeken).

Backup-then-migrate; idempotent; tweemaal draaien verandert niets.
Handmatig gewijzigde datums worden niet overschreven (alleen NULL
wordt gevuld; afwijkende waarden geven een waarschuwing).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

TABLES = ("roles", "mechanisms", "emergent_effects")

# (mechanisme, active_from, active_until, rationale)
DATERINGEN = [
    ("kijkcijferdisciplinering", "1987", None,
     "kijkmeterpanel (nu NMO) bestaat in NL sinds 1987"),
    ("algoritmische_filtering", "2006", None,
     "algoritmische feed bestaat sinds Facebook News Feed (2006)"),
    ("algoritmische_socialisatie", "2010", None,
     "opgroeien met algoritmische feeds vereist smartphone-era (~2010)"),
    ("platform_advertentie_concentratie", "2000", None,
     "online advertentieplatforms sinds Google AdWords (2000)"),
    ("platform_journalistiekfinanciering", "2015", None,
     "eerste grote fonds: Google Digital News Initiative (2015)"),
    ("omroepverzuiling", "1930", None,
     "Zendtijdenbesluit 1930 verdeelt zendtijd over de zuilomroepen"),
]


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def has_column(cur, table, column):
    return any(row[1] == column
               for row in cur.execute(f"PRAGMA table_info({table})"))


def main():
    if not DB.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB}")
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # ---- 1. SCHEMA: kolommen toevoegen ---------------------------------------
    for table in TABLES:
        for column in ("active_from", "active_until"):
            if has_column(cur, table, column):
                print(f"kolom bestaat al: {table}.{column}")
            else:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
                print(f"kolom toegevoegd: {table}.{column}")

    # ---- 2. DATERINGEN -------------------------------------------------------
    for name, van, tot, rationale in DATERINGEN:
        row = cur.execute(
            "SELECT id, active_from, active_until FROM mechanisms WHERE name=?",
            (name,)).fetchone()
        if row is None:
            print(f"WAARSCHUWING: mechanisme niet gevonden: {name}")
            continue
        mid, huidig_van, huidig_tot = row
        if huidig_van is None and huidig_tot is None:
            cur.execute(
                "UPDATE mechanisms SET active_from=?, active_until=? WHERE id=?",
                (van, tot, mid))
            print(f"gedateerd: {name} [{van} - {tot or 'heden'}] ({rationale})")
        elif (huidig_van, huidig_tot) == (van, tot):
            print(f"al gedateerd: {name} [{van} - {tot or 'heden'}]")
        else:
            print(f"OVERGESLAGEN (handmatig afwijkend): {name} "
                  f"[{huidig_van} - {huidig_tot or 'heden'}], "
                  f"migratie wilde [{van} - {tot or 'heden'}]")

    con.commit()

    # ---- 3. SAMENVATTING -----------------------------------------------------
    n = cur.execute("SELECT COUNT(*) FROM mechanisms "
                    "WHERE active_from IS NOT NULL "
                    "OR active_until IS NOT NULL").fetchone()[0]
    print(f"\nklaar: {n} van de "
          f"{cur.execute('SELECT COUNT(*) FROM mechanisms').fetchone()[0]} "
          f"mechanismen gedateerd; overige NULL = onbegrensd voor zover bekend")
    con.close()


if __name__ == "__main__":
    main()
