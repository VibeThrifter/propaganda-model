#!/usr/bin/env python3
"""Schema-migratie: de tabel `richting_toetsen` (eigenaarsbesluit 2026-10-15: "alleen
directioneel als a ook echt invloed heeft op b en niet echt andersom, zoals a financiert b of a
is eigenaar van b … ga het hele propagandamodel af … en zorg ook dat de agents ze in de toekomst
niet meer maken").

Waarom: een verband van een gericht type (financiering, eigendom, flak, …) wijst van wie de
invloed uitoefent naar wie haar ondergaat. Een agent (scripts/richtingtoets.py, account
`richtingtoets`, nooit de auteur) toetst per verband of dat klopt: 'juist', 'omgekeerd',
'richtingloos' of 'twijfel'. De automatische beoordeling past het toe. Procesmetadata, géén
inhoud: de tabel telt in niets mee.

De definitie is exact die van schema.sql. Idempotent: bestaat de tabel al, dan gebeurt er
niets. Backup-then-migrate per conventie.

Gebruik: python3 scripts/migrate_add_richting_toetsen.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

RICHTING_TOETSEN_DDL = """
CREATE TABLE richting_toetsen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_id INTEGER NOT NULL REFERENCES relations(id),
    relatie_hash TEXT NOT NULL,           -- sha256 van bron|doel|type|mechanisme|bidirectional
    verdict TEXT NOT NULL CHECK(verdict IN ('juist', 'omgekeerd', 'richtingloos', 'twijfel')),
    reden TEXT NOT NULL,
    model TEXT,                           -- welk model oordeelde ('haiku', 'haiku+sonnet')
    door TEXT REFERENCES users(username),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(relation_id, door)
)"""
INDEX_DDL = "CREATE INDEX idx_richting_toetsen_relatie ON richting_toetsen(relation_id)"


def nodig(conn) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                        "AND name = 'richting_toetsen'").fetchone() is None


def migreer(db: Path) -> bool:
    """Leg de tabel en haar index aan als ze er nog niet zijn. → True als er iets veranderde."""
    conn = sqlite3.connect(db)
    try:
        if not nodig(conn):
            print("richting_toetsen bestaat al — overslaan.")
            return False
        conn.execute(RICHTING_TOETSEN_DDL)
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
            print("richting_toetsen bestaat al — niets te doen.")
            return
    finally:
        conn.close()
    kopie = backup(DB)
    print(f"Backup: {kopie}")
    if migreer(DB):
        print("Tabel richting_toetsen aangelegd.")


if __name__ == "__main__":
    main()
