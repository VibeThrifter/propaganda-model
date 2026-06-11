#!/usr/bin/env python3
"""
Migratie: datering van de techplatform-rol en zijn resterende edges (juni 2026).

Vervolg op migrate_tijdsdimensie_theorielaag.py: alles wat aan de rol
`techplatform` hangt is technologie-gebonden en dus dateerbaar. Drie van
zijn zeven mechanismen waren al gedateerd (algoritmische_filtering 2006,
platform_advertentie_concentratie 2000, algoritmische_socialisatie 2010,
platform_journalistiekfinanciering 2015); deze migratie dateert de rest:

- rol techplatform           1998  oprichting Google — vanaf dan bestaat
                                   de platform-rol in het nieuwsecosysteem
- platform_verdienmodel_druk 2006  de algoritmische feed (Facebook News
                                   Feed) maakt redactioneel bereik
                                   platform-afhankelijk
- statelijke_inhoudsmoderatie 2015 EU Internet Referral Unit; opkomst van
                                   statelijke verwijderverzoeken aan
                                   platforms
- publieksfragmentatie       2010  versplintering van het nieuwspubliek
                                   vereist smartphone + sociale feeds als
                                   primaire nieuwsbron (~2010)

Geen einddatums: alles werkt nog. NULL blijft "onbegrensd voor zover
bekend". Backup-then-migrate; idempotent; handmatig gewijzigde datums
worden niet overschreven.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# (tabel, naam, active_from, rationale)
DATERINGEN = [
    ("roles", "techplatform", "1998",
     "oprichting Google; vanaf dan bestaat de platform-rol in het nieuwsecosysteem"),
    ("mechanisms", "platform_verdienmodel_druk", "2006",
     "algoritmische feed maakt redactioneel bereik platform-afhankelijk"),
    ("mechanisms", "statelijke_inhoudsmoderatie", "2015",
     "EU Internet Referral Unit; statelijke verwijderverzoeken aan platforms"),
    ("mechanisms", "publieksfragmentatie", "2010",
     "versplintering nieuwspubliek vereist smartphone + sociale feeds (~2010)"),
]


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def main():
    if not DB.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB}")
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    for table, name, van, rationale in DATERINGEN:
        row = cur.execute(
            f"SELECT id, active_from FROM {table} WHERE name=?", (name,)).fetchone()
        if row is None:
            print(f"WAARSCHUWING: niet gevonden in {table}: {name}")
            continue
        rid, huidig = row
        if huidig is None:
            cur.execute(f"UPDATE {table} SET active_from=? WHERE id=?", (van, rid))
            print(f"gedateerd: {table}.{name} [{van} - heden] ({rationale})")
        elif huidig == van:
            print(f"al gedateerd: {table}.{name} [{van} - heden]")
        else:
            print(f"OVERGESLAGEN (handmatig afwijkend): {table}.{name} "
                  f"[{huidig}], migratie wilde [{van}]")

    con.commit()
    con.close()
    print("\nklaar — draai scripts/generate_viz.py om de viz bij te werken")


if __name__ == "__main__":
    main()
