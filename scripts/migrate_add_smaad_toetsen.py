#!/usr/bin/env python3
"""Schema-migratie: de tabel `smaad_toetsen` (eigenaarsbesluit 2026-10-06: "laat de
smaad-firewall checken of het feitelijk is; als het niet feitelijk is koppel het terug").

Waarom: een claim die een natuurlijk persoon raakt en geen neutraal structuurfeit is, merget
niet meer "nooit automatisch" maar na een smaadtoets door een agent (scripts/smaadtoets.py,
account `smaadtoets`): een feit, gedragen door de bron, over de publieke rol → 'feitelijk';
anders 'niet_feitelijk' en teruggekoppeld. Procesmetadata, géén inhoud: de tabel telt in
niets mee.

De definitie is exact die van schema.sql. Idempotent: bestaat de tabel al, dan gebeurt er
niets. Backup-then-migrate per conventie.

Gebruik: python3 scripts/migrate_add_smaad_toetsen.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

SMAAD_TOETSEN_DDL = """
CREATE TABLE smaad_toetsen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    argument_id INTEGER NOT NULL REFERENCES arguments(id),
    verdict TEXT NOT NULL CHECK(verdict IN ('feitelijk', 'niet_feitelijk')),
    reden TEXT NOT NULL,
    herformulering TEXT,                  -- feitelijke formulering die de bron wél draagt
    door TEXT REFERENCES users(username),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(argument_id, door)
)"""
INDEX_DDL = "CREATE INDEX idx_smaad_toetsen_argument ON smaad_toetsen(argument_id)"


def nodig(conn) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                        "AND name = 'smaad_toetsen'").fetchone() is None


def migreer(db: Path) -> bool:
    """Leg de tabel en haar index aan als ze er nog niet zijn. → True als er iets veranderde."""
    conn = sqlite3.connect(db)
    try:
        if not nodig(conn):
            print("smaad_toetsen bestaat al — overslaan.")
            return False
        conn.execute(SMAAD_TOETSEN_DDL)
        conn.execute(INDEX_DDL)
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
            print("smaad_toetsen bestaat al — niets te doen.")
            return
    finally:
        conn.close()
    kopie = backup(DB)
    print(f"Backup: {kopie}")
    if migreer(DB):
        print("Tabel smaad_toetsen aangelegd.")


if __name__ == "__main__":
    main()
