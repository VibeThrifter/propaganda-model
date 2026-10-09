#!/usr/bin/env python3
"""Schema-migratie: de tabel `stem_toetsen` (eigenaarsbesluit 2026-10-08: "'ondermijnt het
vertrouwen in de journalistiek' … deze taal moeten we niet overnemen, dit is duidelijk een
politiek spelletje … waak hier streng voor in het propagandamodel").

Waarom: de eigen stem van het model zegt wat er gebeurde (wie deed of zei wat, wanneer), nooit
een oordeel over gevolgen of motieven, een etiket of de retoriek van één kant. Een agent
(scripts/stemtoets.py, account `stemtoets`, nooit de auteur) toetst daarop elke argument-claim
en elke beschrijving van een relatie of entiteit: 'neutraal' of 'niet_neutraal' met een
neutrale herformulering. Procesmetadata, géén inhoud: de tabel telt in niets mee.

De definitie is exact die van schema.sql. Idempotent: bestaat de tabel al, dan gebeurt er
niets. Backup-then-migrate per conventie.

Gebruik: python3 scripts/migrate_add_stem_toetsen.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

STEM_TOETSEN_DDL = """
CREATE TABLE stem_toetsen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    soort TEXT NOT NULL CHECK(soort IN ('argument', 'relatie', 'entiteit')),
    doel_id INTEGER NOT NULL,             -- argument-, relatie- of entiteit-id (naar soort)
    tekst_hash TEXT NOT NULL,             -- sha256 van de getoetste tekst
    verdict TEXT NOT NULL CHECK(verdict IN ('neutraal', 'niet_neutraal')),
    reden TEXT NOT NULL,
    herformulering TEXT,                  -- dezelfde feiten, oordeel weg of toegeschreven
    door TEXT REFERENCES users(username),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(soort, doel_id, door)
)"""
INDEX_DDL = "CREATE INDEX idx_stem_toetsen_doel ON stem_toetsen(soort, doel_id)"


def nodig(conn) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                        "AND name = 'stem_toetsen'").fetchone() is None


def migreer(db: Path) -> bool:
    """Leg de tabel en haar index aan als ze er nog niet zijn. → True als er iets veranderde."""
    conn = sqlite3.connect(db)
    try:
        if not nodig(conn):
            print("stem_toetsen bestaat al — overslaan.")
            return False
        conn.execute(STEM_TOETSEN_DDL)
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
            print("stem_toetsen bestaat al — niets te doen.")
            return
    finally:
        conn.close()
    kopie = backup(DB)
    print(f"Backup: {kopie}")
    if migreer(DB):
        print("Tabel stem_toetsen aangelegd.")


if __name__ == "__main__":
    main()
