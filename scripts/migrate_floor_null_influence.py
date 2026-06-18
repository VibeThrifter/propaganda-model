#!/usr/bin/env python3
"""Structuurintegriteit: relaties met influence = NULL krijgen de 'magnitude-onbekend'-
vloer (0.05), net als de via POST aangemaakte relaties sinds de servervloer-fix. NULL gaf
derived_influence 0 → gewicht 0 in scoring én de tijdbewuste kleur. Boven de vloer komen
blijft evidence-gated (property='influence'-argument; INVLOED-PRIOR-validator).

Volgt het backup-then-migrate-patroon. Idempotent.
"""
import sqlite3, shutil
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data/propaganda_model.db"
backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
shutil.copy(DB, backup)
print(f"Backup: {backup}")

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")
rijen = conn.execute("SELECT id FROM relations WHERE influence IS NULL").fetchall()
# Geen edit_log-schrijf: dit is een structuurmigratie (kolom mag geen NULL zijn), de
# backup hierboven is het audit-spoor — consistent met de overige migrate_*-scripts.
conn.execute("UPDATE relations SET influence = 0.05 WHERE influence IS NULL")
conn.commit()
print(f"influence NULL → 0.05 voor {len(rijen)} relaties: {[r[0] for r in rijen]}")
conn.close()
