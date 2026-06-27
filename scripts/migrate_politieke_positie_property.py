#!/usr/bin/env python3
"""Schema/structuur-migratie: voeg de property-waarde 'politieke_positie' toe aan
arguments.property (CHECK-enum), zodat een ideologisch/politiek positie-signaal als
een gewoon, GESOURCET en BETWISTBAAR argument in de discussieboom kan landen.

Spiegelt 'influence': het is GATED (een ondersteunend/weerleggend root-argument met
deze property vereist een echte bron — geregeld in server.py) maar telt NIET in de
zekerheidsbalans (scoring.py ASPECT_PROPERTIES). property_value codeert de as + waarde,
conventie '<as>:<signed float -1..1>' met as ∈ {economisch, cultureel} en teken
negatief = links/progressief, positief = rechts/conservatief.

SQLite kan een CHECK niet ALTER-en, dus de arguments-tabel wordt één keer herbouwd.
De rebuild hergebruikt de exact opgeslagen tabeldefinitie (sqlite_master) en injecteert
alleen de nieuwe enum-waarde, zodat kolomvolgorde/typen/overige CHECKs identiek blijven.
Backup-then-migrate per repo-conventie.
"""
import sqlite3, shutil, sys
from pathlib import Path
from datetime import datetime

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")
    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    create_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'"
    ).fetchone()["sql"]

    if "'politieke_positie'" in create_sql:
        print("Property 'politieke_positie' staat al in de CHECK — niets te doen.")
        conn.close()
        return

    # Veiligheidscheck: 'compositie' (gequote enum-waarde) moet exact 1x voorkomen.
    if create_sql.count("'compositie'") != 1:
        conn.close()
        sys.exit("Onverwacht aantal 'compositie'-voorkomens; afgebroken voor veiligheid.")

    new_table_sql = (create_sql
        .replace("CREATE TABLE arguments", "CREATE TABLE arguments_new", 1)
        .replace("'compositie'", "'compositie',\n        'politieke_positie'", 1))

    index_sqls = [r["sql"] for r in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='arguments' "
        "AND sql IS NOT NULL")]

    n_before = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript("BEGIN;")
    try:
        conn.execute(new_table_sql)
        conn.execute("INSERT INTO arguments_new SELECT * FROM arguments")
        conn.execute("DROP TABLE arguments")
        conn.execute("ALTER TABLE arguments_new RENAME TO arguments")
        for isql in index_sqls:
            conn.execute(isql)
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        conn.close()
        sys.exit(f"Migratie mislukt, teruggedraaid: {e}")
    conn.execute("PRAGMA foreign_keys = ON")

    n_after = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    ok_check = "'politieke_positie'" in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'"
    ).fetchone()["sql"]
    conn.close()

    print(f"Rijen: {n_before} -> {n_after}")
    print(f"FK-check: {'OK' if not fk else fk}")
    print(f"CHECK bevat 'politieke_positie': {ok_check}")
    if n_before != n_after or fk or not ok_check:
        sys.exit("VERIFICATIE GEFAALD — herstel via backup.")
    print("Klaar.")

if __name__ == "__main__":
    main()
