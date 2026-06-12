#!/usr/bin/env python3
"""
Migratie: structuur voor fase 3 — voorspellingsregister (verbeterplan M3.4, juni 2026).

Eén structuurmigratie (inhoud blijft onaangeraakt — dogfood-regel): de tabel
`predictions` + index, met DDL gelezen uit schema.sql (single source of truth).
Voorspellingen zelf worden daarna uitsluitend via de API vastgelegd
(POST /api/predictions), zodat attributie en edit_log vanzelf kloppen.

Conventie: backup-then-migrate.
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


def lees_ddl(tabel):
    sql = SCHEMA_PATH.read_text()
    m = re.search(rf"CREATE TABLE {tabel} \(.*?\n\);", sql, re.S)
    if not m:
        sys.exit(f"FOUT: kan CREATE TABLE {tabel} niet vinden in schema.sql")
    return m.group(0)


def main():
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")

    backup = DB_PATH.with_name(
        f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    bestaat = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                           "AND name = 'predictions'").fetchone()
    if bestaat:
        print("predictions-tabel bestaat al; niets te doen.")
        conn.close()
        return

    conn.execute(lees_ddl("predictions"))
    conn.execute("CREATE INDEX idx_predictions_status ON predictions(status)")
    conn.commit()
    conn.close()
    print("predictions-tabel + index aangemaakt (M3.4).")
    print("Voorspellingen vastleggen gaat via POST /api/predictions (dogfood-regel).")


if __name__ == "__main__":
    main()
