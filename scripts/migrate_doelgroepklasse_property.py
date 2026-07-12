#!/usr/bin/env python3
"""Schema/structuur-migratie: voeg de property-waarde 'doelgroepklasse' toe aan
arguments.property (CHECK-enum), zodat een outlet-entiteit een gesourcet marketing-/
welstandsklasse-signaal kan dragen (zie doelgroep.py — de welstandsmeter, zusje van de
politieke kleurmeter).

Aspect, telt NIET in de zekerheidsbalans (scoring.py ASPECT_PROPERTIES); bron VERPLICHT
(gated als 'influence'/'politieke_positie'). property_value = 'welstand:<klasse A/B1/B2/C/D>'
of 'welstand:meting:<-1..1>' (NOM/NMO-bereikindex).

SQLite kan een CHECK niet ALTER-en, dus de arguments-tabel wordt één keer herbouwd — exact
zoals migrate_machtsvalentie_property.py. De rebuild hergebruikt de opgeslagen tabel-definitie
(sqlite_master) en injecteert alleen de nieuwe enum-waarde na 'machtsvalentie', zodat
kolomvolgorde/typen/overige CHECKs identiek blijven. Backup-then-migrate per conventie.
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

    if "'doelgroepklasse'" in create_sql:
        print("Property 'doelgroepklasse' staat al in de CHECK — niets te doen.")
        conn.close()
        return

    # Veiligheidscheck: 'machtsvalentie' (gequote enum-waarde) moet exact 1x voorkomen.
    if create_sql.count("'machtsvalentie'") != 1:
        conn.close()
        sys.exit("Onverwacht aantal 'machtsvalentie'-voorkomens; afgebroken voor veiligheid.")

    # De tabelnaam kan gequote in sqlite_master staan (na een eerdere RENAME).
    if 'CREATE TABLE "arguments"' in create_sql:
        new_table_sql = create_sql.replace(
            'CREATE TABLE "arguments"', 'CREATE TABLE "arguments_new"', 1)
    elif "CREATE TABLE arguments" in create_sql:
        new_table_sql = create_sql.replace(
            "CREATE TABLE arguments", "CREATE TABLE arguments_new", 1)
    else:
        conn.close()
        sys.exit("Kon 'CREATE TABLE arguments' niet vinden in de opgeslagen definitie.")
    new_table_sql = new_table_sql.replace(
        "'machtsvalentie'", "'machtsvalentie',\n        'doelgroepklasse'", 1)

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
    ok_check = "'doelgroepklasse'" in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'"
    ).fetchone()["sql"]
    conn.close()

    print(f"Rijen: {n_before} -> {n_after}")
    print(f"FK-check: {'OK' if not fk else fk}")
    print(f"CHECK bevat 'doelgroepklasse': {ok_check}")
    if n_before != n_after or fk or not ok_check:
        sys.exit("VERIFICATIE GEFAALD — herstel via backup.")
    print("Klaar.")


if __name__ == "__main__":
    main()
