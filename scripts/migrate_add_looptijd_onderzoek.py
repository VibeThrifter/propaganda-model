#!/usr/bin/env python3
"""Schema-migratie: de tabel `looptijd_onderzoek` (eigenaarsbesluit 2026-10-09: "vul bij alles
de goede jaartallen in … het model kijkt per tijdsvak wat de relaties zijn … zorg dat dit overal
wordt gehandhaafd").

Waarom: elk verband draagt zijn looptijd (active_from, en active_until als het voorbij is). Wat
een register niet geeft, zoekt de datumzoeker (scripts/datumzoeker.py, account `datumzoeker`).
Deze tabel houdt per verband bij of hij zocht en wat de uitkomst was. 'niets_gevonden' is de
enige reden waarom een verband zonder begin goedgekeurd mag worden (server: looptijd_besluit;
validatie: RELATIE-ZONDER-JAAR). Procesmetadata, géén inhoud: de tabel telt in niets mee.

De definitie is exact die van schema.sql. Idempotent; backup-then-migrate per conventie.

Gebruik: python3 scripts/migrate_add_looptijd_onderzoek.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

DDL = """CREATE TABLE looptijd_onderzoek (
    relation_id INTEGER PRIMARY KEY,      -- bewust geen FK (zoals nieuws_voorrang)
    status TEXT NOT NULL CHECK(status IN ('gezocht', 'gevonden', 'niets_gevonden', 'fout',
                                     'register_zonder_datum')),
    pogingen INTEGER NOT NULL DEFAULT 0,
    laatste_poging TEXT NOT NULL,         -- lokale ISO-tekst
    detail TEXT,                          -- wat er gezocht/gevonden is (kort)
    door TEXT REFERENCES users(username)
)"""


def nodig(conn) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                        "AND name = 'looptijd_onderzoek'").fetchone() is None


def migreer(db: Path) -> bool:
    conn = sqlite3.connect(db)
    try:
        if not nodig(conn):
            print("looptijd_onderzoek bestaat al — overslaan.")
            return False
        conn.execute(DDL)
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
            print("looptijd_onderzoek bestaat al — niets te doen.")
            return
    finally:
        conn.close()
    print(f"Backup: {backup(DB)}")
    if migreer(DB):
        print("Tabel looptijd_onderzoek aangelegd.")


if __name__ == "__main__":
    main()
