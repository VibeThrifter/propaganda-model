#!/usr/bin/env python3
"""Migratie: voorgestelde bron-classificatie (agent stelt voor, reviewer bevestigt).

Voegt aan `sources` drie kolommen toe waarin een bijdrager (mens of agent) een
*voorstel* voor de classificatie kan achterlaten:

  - reliability_voorgesteld   : voorgestelde betrouwbaarheidsklasse
  - onderwerp_voorgesteld     : voorgesteld onderwerp (relevantie-as)
  - classificatie_voorgesteld_door : gebruikersnaam die het voorstel deed

Dit voorstel telt NIET in de score (scoring.py leest alleen de gezaghebbende
`reliability`/`onderwerp`, die op 'onbeoordeeld'/'onbepaald' blijven tot een
reviewer ze via PATCH /api/sources/<id>/classificatie bevestigt). Zo blijft de
kerninvariant intact: geen score-input is zelf-gerapporteerd. Spiegelt de
voorgesteld→merged-lus van argumenten.

Live ALTER TABLE krijgt geen CHECK (consistent met de rest van de DB); de CHECK
staat in schema.sql voor verse builds.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NIEUWE_KOLOMMEN = [
    ("reliability_voorgesteld", "TEXT"),
    ("onderwerp_voorgesteld", "TEXT"),
    ("classificatie_voorgesteld_door", "TEXT"),
]


def main():
    if not DB.exists():
        raise SystemExit(f"DB niet gevonden: {DB}")
    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy(DB, backup)
    print(f"Back-up: {backup.name}")

    conn = sqlite3.connect(DB)
    bestaand = {r[1] for r in conn.execute("PRAGMA table_info(sources)")}
    toegevoegd = []
    for naam, typ in NIEUWE_KOLOMMEN:
        if naam in bestaand:
            print(f"  · {naam} bestaat al, overslaan")
            continue
        conn.execute(f"ALTER TABLE sources ADD COLUMN {naam} {typ}")
        toegevoegd.append(naam)
        print(f"  + kolom {naam} {typ}")
    conn.commit()
    conn.close()
    print(f"Klaar — {len(toegevoegd)} kolom(men) toegevoegd.")


if __name__ == "__main__":
    main()
