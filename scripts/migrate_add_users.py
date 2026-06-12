#!/usr/bin/env python3
"""
Migratie: users-tabel voor identiteit-licht (verbeterplan M0.6, juni 2026).

Mensen én agents krijgen een account; schrijf-endpoints vereisen er vanaf nu één
(zie server.py). Het wachtwoord (alleen mensen) staat als scrypt-hash, het
API-token als sha256-hash — het token zelf wordt nooit opgeslagen en één keer
getoond (scripts/create_user.py). Agents dragen verplicht provenance (model+versie).

De DDL wordt uit schema.sql gelezen (single source of truth, zelfde aanpak als
migrate_schema_pariteit.py). Idempotent; conventie: backup-then-migrate.
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


def users_ddl_uit_schema():
    tekst = SCHEMA_PATH.read_text()
    match = re.search(r"CREATE TABLE users \(.*?\n\);", tekst, re.S)
    if not match:
        sys.exit("CREATE TABLE users niet gevonden in schema.sql — eerst schema.sql bijwerken")
    return match.group(0)


def main():
    if not DB_PATH.exists():
        sys.exit(f"Database niet gevonden: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    bestaat = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
    if bestaat:
        print("users-tabel bestaat al — niets te doen.")
        conn.close()
        return

    conn.close()
    backup = DB_PATH.with_name(
        f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute(users_ddl_uit_schema())
    conn.commit()
    conn.close()
    print("users-tabel aangemaakt. Maak accounts met scripts/create_user.py.")


if __name__ == "__main__":
    main()
