#!/usr/bin/env python3
"""
Migratie: classificatiekeuzes discutabel maken (juni 2026).

Maakt twee classificatie-edges bespreekbaar via de discussieboom, naast de al
bestaande `property='role'` (entiteit→rol):

  property='mechanism'  praktijk→theorie: bij welk MECHANISME hoort deze relatie?
                        (property_value = mechanisme-ID, rename-vast).
  property='filter'     theorie: bij welke PROPAGANDAFILTER hoort dit mechanisme/
                        deze rol? (property_value = filter-enum).

Beide zijn ASPECT-argumenten: ze leggen het *debat* vast, ze herschrijven NIET
zelf `mechanisms.filter` / `relations.mechanism_id` (ik stel voor, jij beslist).
In `scoring.py` staan ze in ASPECT_PROPERTIES, zodat een classificatiedebat de
zekerheids-/bestaansscore niet raakt (bestaan staat los van classificatie).

Enige verandering aan de tabel is de property-CHECK; kolommen blijven gelijk.
Daarom kopiëren we de doorsnede van de huidige kolommen met de nieuwe DDL —
resilient tegen latere kolomtoevoegingen (merged_by, objection_type, …).
Conventie: backup-then-migrate; DDL + indexen uit schema.sql (single source of truth).
"""
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
SCHEMA_PATH = ROOT / "schema.sql"

NIEUWE_PROPERTIES = ("mechanism", "filter")


def lees_ddl(tabel):
    sql = SCHEMA_PATH.read_text()
    m = re.search(rf"CREATE TABLE {tabel} \(.*?\n\);", sql, re.S)
    if not m:
        sys.exit(f"FOUT: kan CREATE TABLE {tabel} niet vinden in schema.sql")
    return m.group(0)


def lees_indexen(tabel):
    sql = SCHEMA_PATH.read_text()
    return re.findall(rf"CREATE (?:UNIQUE )?INDEX [^\n;]*\bON {tabel}\b[^\n;]*;", sql)


def kolommen(conn, tabel):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({tabel})")]


def main():
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")

    ddl = lees_ddl("arguments")
    for p in NIEUWE_PROPERTIES:
        if f"'{p}'" not in ddl:
            sys.exit(f"FOUT: schema.sql mist property '{p}' in de arguments-CHECK; "
                     "pas eerst schema.sql aan")

    backup = DB_PATH.with_name(
        f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")

    n_arg = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    oude_kolommen = kolommen(conn, "arguments")

    # Nieuwe tabel uit de DDL maken en de doorsnede van de kolommen overzetten.
    conn.execute("ALTER TABLE arguments RENAME TO arguments_oud")
    conn.execute(ddl)
    nieuwe_kolommen = kolommen(conn, "arguments")
    gedeeld = [k for k in oude_kolommen if k in nieuwe_kolommen]
    verloren = [k for k in oude_kolommen if k not in nieuwe_kolommen]
    if verloren:
        sys.exit(f"FOUT: kolom(men) {verloren} zit(ten) niet in de nieuwe DDL; "
                 "geen kolomwijziging verwacht — afgebroken, niet gecommit")
    kols = ", ".join(gedeeld)
    conn.execute(f"INSERT INTO arguments ({kols}) SELECT {kols} FROM arguments_oud")
    conn.execute("DROP TABLE arguments_oud")

    for idx in lees_indexen("arguments"):
        conn.execute(idx)

    # Nacontrole: geen rij verloren, FKs heel, nieuwe CHECK accepteert de waardes.
    assert conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0] == n_arg, \
        "rijaantal veranderd na herbouw"
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        sys.exit(f"FOUT: foreign_key_check meldt {len(fk)} problemen — niet gecommit")

    conn.commit()
    print(f"Klaar: arguments herbouwd ({n_arg} rijen), property-CHECK kent nu "
          f"{', '.join(NIEUWE_PROPERTIES)}; indexen hersteld.")
    conn.close()


if __name__ == "__main__":
    main()
