#!/usr/bin/env python3
"""Schema/structuur-migratie (Epic 12 "Wie is dit?", eigenaarsbesluit 2026-09-30):

Legt de tabel `nieuws_doelen` aan — de onderzoekswachtrij tussen de nieuws-aggregator
(account `nieuws-agent` zet doelen in de rij) en de missie-agent `nieuws-scout` (claimt
en werkt ze af). Procesmetadata, géén inhoud: de tabel telt in niets mee (scoring,
influence en viz lezen haar niet). Wat de scout vindt, gaat via het gewone
bijdragepad (alles `voorgesteld`); `resultaat` wijst alleen naar die ids.

Puur additief (CREATE TABLE + CREATE INDEX, beide IF NOT EXISTS) → idempotent, geen
tabel-rebuild. Backup-then-migrate per conventie: eerst een kopie naar
data/propaganda_model_backup_<timestamp>.db (via de SQLite-backup-API, zodat ook de
WAL-inhoud meegaat). De DDL is identiek aan schema.sql (check_schema_pariteit).

Gebruik: python3 scripts/migrate_add_nieuws_doelen.py
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NIEUWS_DOELEN_DDL = """
CREATE TABLE IF NOT EXISTS nieuws_doelen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sleutel TEXT NOT NULL UNIQUE,
    naam TEXT NOT NULL,
    soort TEXT NOT NULL CHECK(soort IN ('persoon', 'organisatie')),
    rol_categorie TEXT,
    rol_hint TEXT,
    context TEXT,
    prioriteit REAL NOT NULL DEFAULT 0,
    entity_id INTEGER,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN (
        'open', 'bezig', 'klaar', 'niets_gevonden', 'overgeslagen', 'twijfel', 'fout')),
    vervolg TEXT CHECK(vervolg IS NULL OR vervolg IN ('linkedin')),
    verslag TEXT,
    resultaat TEXT,
    aangevraagd_door TEXT REFERENCES users(username),
    geclaimd_door TEXT REFERENCES users(username),
    geclaimd_op TEXT,
    pogingen INTEGER NOT NULL DEFAULT 0,
    aangemaakt TEXT NOT NULL,
    bijgewerkt TEXT NOT NULL
)
"""

INDEX_DDL = ("CREATE INDEX IF NOT EXISTS idx_nieuws_doelen_status "
             "ON nieuws_doelen(status, prioriteit)")


def _bestaat(conn, soort, naam):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?",
                        (soort, naam)).fetchone() is not None


def backup(db: Path) -> Path:
    """Consistente kopie (incl. WAL) naar data/propaganda_model_backup_<timestamp>.db."""
    stempel = f"{datetime.now():%Y%m%d_%H%M%S}"
    doel = db.parent / f"propaganda_model_backup_{stempel}.db"
    volgnr = 1
    while doel.exists():  # twee runs binnen dezelfde seconde: nooit een backup overschrijven
        doel = db.parent / f"propaganda_model_backup_{stempel}_{volgnr}.db"
        volgnr += 1
    bron = sqlite3.connect(db)
    kopie = sqlite3.connect(doel)
    try:
        bron.backup(kopie)
    finally:
        kopie.close()
        bron.close()
    return doel


def migreer(db: Path) -> list:
    """Voer de migratie uit op `db`; geeft de lijst van toegevoegde onderdelen terug."""
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    gedaan = []
    try:
        if _bestaat(conn, "table", "nieuws_doelen"):
            print("Tabel 'nieuws_doelen' bestaat al — overslaan.")
        else:
            conn.execute(NIEUWS_DOELEN_DDL)
            gedaan.append("tabel nieuws_doelen")
        if _bestaat(conn, "index", "idx_nieuws_doelen_status"):
            print("Index 'idx_nieuws_doelen_status' bestaat al — overslaan.")
        else:
            conn.execute(INDEX_DDL)
            gedaan.append("index idx_nieuws_doelen_status")
        conn.commit()
    finally:
        conn.close()
    return gedaan


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")
    print(f"Backup: {backup(DB).name}")
    gedaan = migreer(DB)
    if gedaan:
        print("Toegevoegd:", ", ".join(gedaan))
    else:
        print("Niets te doen — migratie was al toegepast.")
    print("Klaar.")


if __name__ == "__main__":
    main()
