#!/usr/bin/env python3
"""Schema-migratie: de tabel `nieuws_voorrang` (eigenaarsbesluit 2026-10-06: agents doen
alles in het propagandamodel).

Waarom: de nieuws-aggregator meldt welke verbanden lezers onder "Wie zit erachter?" te
zien krijgen (POST /api/nieuws/voorrang, account `nieuws-agent`). Die gaan voor bij de
automatische controle (scripts/bronchecker.py) en de bronzoeker (scripts/bronzoeker.py),
zodat wat lezers zien als eerste gecontroleerd en zo nodig van een bron voorzien wordt.
Procesmetadata, géén inhoud: de tabel telt in niets mee.

De definitie is exact die van schema.sql. Idempotent: bestaat de tabel al, dan gebeurt er
niets. Backup-then-migrate per conventie.

Gebruik: python3 scripts/migrate_add_nieuws_voorrang.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NIEUWS_VOORRANG_DDL = """
CREATE TABLE nieuws_voorrang (
    relation_id INTEGER PRIMARY KEY,      -- bewust geen FK (zie nieuws_doelen)
    gevraagd_op TEXT NOT NULL,            -- laatste melding, lokale ISO-tekst
    aantal INTEGER NOT NULL DEFAULT 1     -- hoe vaak gemeld
)"""


def nodig(conn) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                        "AND name = 'nieuws_voorrang'").fetchone() is None


def migreer(db: Path) -> bool:
    """Leg de tabel aan als ze er nog niet is. → True als er iets veranderde."""
    conn = sqlite3.connect(db)
    try:
        if not nodig(conn):
            print("nieuws_voorrang bestaat al — overslaan.")
            return False
        conn.execute(NIEUWS_VOORRANG_DDL)
        conn.commit()
        return True
    finally:
        conn.close()


def main():
    if not DB.exists():
        sys.exit(f"Database niet gevonden: {DB}")
    conn = sqlite3.connect(DB)
    try:
        if not nodig(conn):
            print("nieuws_voorrang bestaat al — niets te doen.")
            return
    finally:
        conn.close()
    kopie = backup(DB)
    print(f"Backup: {kopie}")
    if migreer(DB):
        print("Tabel nieuws_voorrang aangelegd.")


if __name__ == "__main__":
    main()
