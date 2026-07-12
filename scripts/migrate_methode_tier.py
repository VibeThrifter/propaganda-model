#!/usr/bin/env python3
"""Schema/structuur-migratie (A5): voeg de kolom `citations.methode` toe — de
provenance-methode-tier waarmee een volume-scrape zich niet als hard bewijs voordoet.

verbatim_quote (sterk) > officieel_register_scrape (medium) > llm_samenvatting_van_pagina
(zwak) weegt mee in scoring.source_factor; NULL/onbekend = neutraal (factor 1,0), zodat de
bestaande hand-gecureerde citaties onveranderd blijven en de golden snapshot groen blijft.

ALTER TABLE ADD COLUMN met een CHECK die NULL toelaat — bestaande rijen (methode NULL)
passeren. Backup-then-migrate per conventie; idempotent (draait 'ie al, dan niets te doen).
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

METHODE_DDL = ("ALTER TABLE citations ADD COLUMN methode TEXT "
               "CHECK(methode IS NULL OR methode IN "
               "('verbatim_quote', 'officieel_register_scrape', 'llm_samenvatting_van_pagina'))")


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")

    conn = sqlite3.connect(DB)
    kolommen = {r[1] for r in conn.execute("PRAGMA table_info(citations)")}
    if "methode" in kolommen:
        print("Kolom citations.methode bestaat al — niets te doen.")
        conn.close()
        return
    conn.close()

    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.execute(METHODE_DDL)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    conn.close()
    print(f"Kolom citations.methode toegevoegd. {n} bestaande citaties houden methode=NULL "
          "(neutrale factor 1,0).")


if __name__ == "__main__":
    main()
