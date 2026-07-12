#!/usr/bin/env python3
"""Schema/structuur-migratie (A1/A2): leg de tabel `immuun_oordelen` aan — de aparte
PROCES-tabel van het epistemische immuunsysteem.

Een her-verificatie-verdict (A1: reproductietest tegen de echte bron) of een
tegenspraak-certificaat (A2: gedecorreleerde aanklager) landt hier — GEEN boomnode,
GEEN τ/σ-gewicht, telt nergens in de score. Puur procesmetadata voor de auto-merge-poort
(A7) + het menselijke vangnet. De oordelen zélf lopen via de REST-API (dogfood); deze
migratie legt alleen de structuur aan.

Backup-then-migrate per conventie; idempotent (CREATE TABLE/INDEX IF NOT EXISTS).
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

TABEL_DDL = """
CREATE TABLE IF NOT EXISTS immuun_oordelen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    argument_id INTEGER NOT NULL REFERENCES arguments(id),
    fase TEXT NOT NULL CHECK(fase IN ('herverificatie', 'tegenspraak')),
    verdict TEXT,
    verbatim_span TEXT,
    bron_id INTEGER,
    detail TEXT,
    door TEXT,
    model_familie TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(argument_id, fase, door)
)
"""
INDEX_DDL = "CREATE INDEX IF NOT EXISTS idx_immuun_argument ON immuun_oordelen(argument_id, fase)"


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")

    conn = sqlite3.connect(DB)
    bestaat = conn.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name='immuun_oordelen'").fetchone()
    conn.close()
    if bestaat:
        print("Tabel immuun_oordelen bestaat al — niets te doen.")
        return

    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.execute(TABEL_DDL)
    conn.execute(INDEX_DDL)
    conn.commit()
    conn.close()
    print("Tabel immuun_oordelen + index idx_immuun_argument aangelegd.")


if __name__ == "__main__":
    main()
