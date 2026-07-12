#!/usr/bin/env python3
"""Schema/structuur-migratie: laat de CHECK-enum op arguments.objection_type vallen —
het ondergraving-categorieveld wordt een VRIJ tekstveld (juli 2026).

Waarom: elke sluitende categorielijst bleek te kort en een volledige eindeloos; de
indiener benoemt de categorie voortaan zelf in de UI (vrij invulveld). De oude
drogreden-taxonomie (cirkelredenering, stroman, …, overig) blijft geldig als waarde
en is het aanbevolen vocabulaire voor agents (missies/monitor_brief.md) — er wijzigt
geen enkele rij, alleen de constraint verdwijnt.

SQLite kan een CHECK niet ALTER-en, dus de arguments-tabel wordt één keer herbouwd —
exact zoals migrate_doelgroepklasse_property.py. De rebuild hergebruikt de opgeslagen
tabel-definitie (sqlite_master) en verwijdert alleen de CHECK-clausule achter
objection_type, zodat kolomvolgorde/typen/overige CHECKs identiek blijven.
Backup-then-migrate per conventie.
"""
import re
import sqlite3, shutil, sys
from pathlib import Path
from datetime import datetime

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# De CHECK-clausule achter de kolom: CHECK(objection_type IN ('…', …)) — de binnenste
# haakjes van de IN-lijst bevatten zelf geen ')', dus [^)]* dekt de hele lijst.
CHECK_RE = re.compile(r"CHECK\s*\(\s*objection_type\s+IN\s*\([^)]*\)\s*\)", re.IGNORECASE)


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

    treffers = CHECK_RE.findall(create_sql)
    if not treffers:
        print("Geen CHECK op objection_type gevonden — niets te doen.")
        conn.close()
        return
    if len(treffers) != 1:
        conn.close()
        sys.exit("Onverwacht aantal objection_type-CHECKs; afgebroken voor veiligheid.")

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
    new_table_sql = CHECK_RE.sub("", new_table_sql, count=1)

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
    nieuw_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'"
    ).fetchone()["sql"]
    check_weg = not CHECK_RE.search(nieuw_sql)
    conn.close()

    print(f"Rijen: {n_before} -> {n_after}")
    print(f"FK-check: {'OK' if not fk else fk}")
    print(f"CHECK op objection_type verwijderd: {check_weg}")
    if n_before != n_after or fk or not check_weg:
        sys.exit("VERIFICATIE GEFAALD — herstel via backup.")
    print("Klaar.")


if __name__ == "__main__":
    main()
