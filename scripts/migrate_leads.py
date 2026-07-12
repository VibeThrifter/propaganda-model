#!/usr/bin/env python3
"""Schema/structuur-migratie (D2.1/D2.3, Fase 5 — publieke intake):

1. Legt de `leads`-tabel aan — de aparte, lager-vertrouwde publieke-intake-baan. Een
   publieke inzending is een TIP/LEAD, geen claim: aparte tabel = structurele isolatie,
   telt in NIETS mee (geen scoring/influence/viz leest 'm), auto-merget nooit.
2. Voegt de kolom `arguments.smaad_hold INTEGER DEFAULT 0` toe (smaad-firewall D2.3):
   een nieuw 'voorgesteld' argument met een negatieve feitelijke persoonsclaim wordt
   uit elke publieke render gehouden tot de eigenaar het vrijgeeft. GEEN retroactieve
   markering — bestaande argumenten blijven 0 zodat de golden snapshot groen blijft.
3. Legt de leads-indexen aan (idx_leads_status, idx_leads_ip).

Beide zijn puur additief (CREATE TABLE + ALTER TABLE ADD COLUMN + CREATE INDEX), dus
geen tabel-rebuild nodig. Backup-then-migrate per conventie; idempotent (herhalen is
veilig). Draai tegen de live DB zodat schema.sql == migratie (check_schema_pariteit).

Gebruik: python3 scripts/migrate_leads.py
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

LEADS_DDL = """
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    herkomst TEXT NOT NULL DEFAULT 'publiek',
    soort TEXT NOT NULL DEFAULT 'tip' CHECK(soort IN ('rectificatie', 'tip')),
    claim TEXT NOT NULL,
    bron_url TEXT,
    quote TEXT,
    betreft TEXT,
    ingezonden_ip_hash TEXT,
    render_ts TEXT,
    status TEXT NOT NULL DEFAULT 'binnengekomen' CHECK(status IN (
        'binnengekomen',
        'in_corroboratie',
        'gecorroboreerd',
        'afgewezen',
        'duplicaat',
        'smaad_hold'
    )),
    agent_arg_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def _tabel_bestaat(conn, naam):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (naam,)).fetchone() is not None


def _kolom_bestaat(conn, tabel, kolom):
    return any(c["name"] == kolom for c in conn.execute(f"PRAGMA table_info({tabel})"))


def _index_bestaat(conn, naam):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (naam,)).fetchone() is not None


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")
    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    gedaan = []

    # 1. leads-tabel
    if _tabel_bestaat(conn, "leads"):
        print("Tabel 'leads' bestaat al — overslaan.")
    else:
        conn.execute(LEADS_DDL)
        gedaan.append("tabel leads")

    # 2. arguments.smaad_hold
    if _kolom_bestaat(conn, "arguments", "smaad_hold"):
        print("Kolom 'arguments.smaad_hold' bestaat al — overslaan.")
    else:
        conn.execute("ALTER TABLE arguments ADD COLUMN smaad_hold INTEGER DEFAULT 0")
        gedaan.append("kolom arguments.smaad_hold")

    # 3. indexen
    for naam, ddl in (
        ("idx_leads_status", "CREATE INDEX idx_leads_status ON leads(status)"),
        ("idx_leads_ip", "CREATE INDEX idx_leads_ip ON leads(ingezonden_ip_hash)"),
    ):
        if _index_bestaat(conn, naam):
            print(f"Index '{naam}' bestaat al — overslaan.")
        else:
            conn.execute(ddl)
            gedaan.append(f"index {naam}")

    conn.commit()

    # Controle: geen retroactieve smaad_hold gezet.
    n_hold = conn.execute("SELECT COUNT(*) FROM arguments WHERE smaad_hold = 1").fetchone()[0]
    conn.close()

    if gedaan:
        print("Toegevoegd:", ", ".join(gedaan))
    else:
        print("Niets te doen — migratie was al toegepast.")
    print(f"Argumenten met smaad_hold=1 (moet 0 zijn na verse migratie): {n_hold}")
    print("Klaar.")


if __name__ == "__main__":
    main()
