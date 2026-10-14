#!/usr/bin/env python3
"""Schema-migratie (eigenaar 2026-10-14, "gebruikers kunnen suggesties doen voor relaties en AI
pakt het op … hoe maak je dit veilig voor spam en onzin?"): de publieke tip wordt gestructureerd.

Voegt aan `leads` toe:
  partij_a, partij_b   de twee partijen van het aangedragen verband (vrije tekst, ge-escaped)
  soort_verband        sleutel uit server.LEAD_SOORTEN_VERBAND ('anders' als het niet past)
  jaar                 het jaartal dat de inzender noemt (JJJJ), of NULL
  triage_reden         '<categorie>: <tekst>' — waarom scripts/lead_triage.py de lead afwees of
                       doorzette; de categorie voedt de reputatie per IP-hash
  doel_id              het doel in nieuws_doelen ('tip:<lead_id>') dat de nieuws-scout afwerkt

Puur additief (ALTER TABLE … ADD COLUMN) → idempotent. Backup-then-migrate per conventie.
De kolommen staan in schema.sql aan het eind van de tabel (check_schema_pariteit).

Gebruik: python3 scripts/migrate_leads_gestructureerd.py
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

KOLOMMEN = (("partij_a", "TEXT"), ("partij_b", "TEXT"), ("soort_verband", "TEXT"),
            ("jaar", "TEXT"), ("triage_reden", "TEXT"), ("doel_id", "INTEGER"))


def backup(db: Path) -> Path:
    """Consistente kopie (incl. WAL) naar data/propaganda_model_backup_<timestamp>.db."""
    stempel = f"{datetime.now():%Y%m%d_%H%M%S}"
    doel = db.parent / f"propaganda_model_backup_{stempel}.db"
    volgnr = 1
    while doel.exists():
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
    """Voer de migratie uit op `db`; geeft de toegevoegde kolommen terug."""
    conn = sqlite3.connect(db)
    try:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='leads'"
                            ).fetchone():
            return []
        bestaand = {r[1] for r in conn.execute("PRAGMA table_info(leads)")}
        toegevoegd = []
        for naam, soort in KOLOMMEN:
            if naam not in bestaand:
                conn.execute(f"ALTER TABLE leads ADD COLUMN {naam} {soort}")
                toegevoegd.append(f"leads.{naam}")
        conn.commit()
        return toegevoegd
    finally:
        conn.close()


def main():
    if not DB.exists():
        sys.exit(f"Database niet gevonden: {DB}")
    print(f"Backup: {backup(DB)}")
    toegevoegd = migreer(DB)
    print("Toegevoegd: " + ", ".join(toegevoegd) if toegevoegd else "Niets te doen (al gemigreerd).")


if __name__ == "__main__":
    main()
