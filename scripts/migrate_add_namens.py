#!/usr/bin/env python3
"""Schema-migratie: kolom relations.namens_id (de hoedanigheid van een persoon).

Eigenaarsbesluit 2026-10-19 ("instituut of persoon"): een expert die eigen duiding geeft, staat
op het verband persoon → medium, met de organisatie waarvan de bron hem aankondigt in
`namens_id` ("Clingendael-onderzoeker Bob Deen" → Clingendael). De route instituut ⇢ medium via
zijn mensen leidt via_medewerkers.py daaruit af; zo staat hetzelfde optreden nooit op twee
verbanden. Zie DOCUMENTATIE.md § "Instituut of persoon".

SQLite voegt een kolom met REFERENCES en standaard NULL toe zonder de tabel te herbouwen. Plus
de index idx_relations_namens (schema.sql heeft hem ook, SCHEMA-INDEX bewaakt de pariteit).

Werkwijze: eerst een backup, dan de lock van de automatische beoordeling (geen ronde halverwege),
dan één transactie. Idempotent.

Gebruik: python3 scripts/migrate_add_namens.py [--db pad]
"""
import argparse
import fcntl
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"
LOCK_PATH = ROOT / "data" / "locks" / "automatische-beoordeling.lock"


def migreer(db: Path, backup: bool = True) -> str:
    conn = sqlite3.connect(db, timeout=60)
    kolommen = {r[1] for r in conn.execute("PRAGMA table_info(relations)")}
    index = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' "
                         "AND name = 'idx_relations_namens'").fetchone()
    if "namens_id" in kolommen and index:
        conn.close()
        return "relations.namens_id en idx_relations_namens bestaan al — niets te doen"
    if backup:
        doel = db.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        kopie = sqlite3.connect(doel)
        conn.backup(kopie)          # consistente kopie, ook in WAL-modus
        kopie.close()
        print(f"Backup: {doel.name}")
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    try:
        if "namens_id" not in kolommen:
            conn.execute("ALTER TABLE relations ADD COLUMN namens_id INTEGER REFERENCES entities(id)")
        if not index:
            conn.execute("CREATE INDEX idx_relations_namens ON relations(namens_id)")
        conn.execute("COMMIT")
    except Exception as e:  # noqa: BLE001
        conn.execute("ROLLBACK")
        conn.close()
        sys.exit(f"Migratie mislukt, teruggedraaid: {e}")
    ok = "namens_id" in {r[1] for r in conn.execute("PRAGMA table_info(relations)")}
    conn.close()
    if not ok:
        sys.exit("VERIFICATIE GEFAALD — herstel via de backup.")
    return "klaar: relations.namens_id + idx_relations_namens"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db", type=Path, default=DB)
    args = p.parse_args()
    if not args.db.exists():
        sys.exit(f"DB niet gevonden: {args.db}")
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit("De automatische beoordeling draait nu; probeer het zo opnieuw.")
        print(migreer(args.db))


if __name__ == "__main__":
    main()
