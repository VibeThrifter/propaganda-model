#!/usr/bin/env python3
"""Schema/structuur-migratie (B5): leg de tabel `afgeleide_prose` aan.

Gecachete, LLM-gegenereerde leesbare NL-samenvatting per model-element
(entiteit/mechanisme) voor de programmatic-SEO-pagina's (paginas.py). AFGELEIDE
COPY, GÉÉN ARGUMENT — telt nergens in de score mee (net als de meter-JSON's) en is
volledig regenereerbaar uit de DB via scripts/genereer_prose.py.

De verse build krijgt de tabel uit schema.sql; deze migratie voegt 'm toe aan een
bestaande DB. Backup-then-migrate per repo-conventie, idempotent (CREATE TABLE IF
NOT EXISTS — draai 'm gerust twee keer).

Gebruik: python3 scripts/migrate_prose.py
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

DDL = """
CREATE TABLE IF NOT EXISTS afgeleide_prose (
    element_type TEXT NOT NULL,           -- 'entiteit' | 'mechanisme'
    element_id INTEGER NOT NULL,
    prose TEXT NOT NULL,                  -- de gecachete NL-samenvatting (2-5 zinnen)
    invoer_hash TEXT NOT NULL,            -- fingerprint van de prose-inputs (staleness)
    model TEXT,                           -- welk model de prose genereerde
    gegenereerd_at TEXT,                  -- ISO-timestamp van generatie
    PRIMARY KEY (element_type, element_id)
);
"""


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")

    conn = sqlite3.connect(DB)
    bestaat = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='afgeleide_prose'"
    ).fetchone()
    if bestaat:
        print("Tabel 'afgeleide_prose' bestaat al — niets te doen (idempotent).")
        conn.close()
        return

    conn.close()
    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.executescript(DDL)
    conn.commit()
    conn.close()
    print("Tabel 'afgeleide_prose' aangelegd.")


if __name__ == "__main__":
    main()
