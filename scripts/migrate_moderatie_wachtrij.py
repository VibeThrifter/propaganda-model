"""Moderatiewachtrij voor de praktijklaag: entiteiten en relaties krijgen een
`status`-kolom.

Regel (juni 2026): een admin (globale maintainer) maakt een node/edge die meteen
zichtbaar is; ieder ander dient in als 'voorgesteld' en die is onzichtbaar in viz
en scores tot een reviewer hem goedkeurt. Zo komt spam/onzin nooit zomaar live.
De geloofwaardigheid/score blijft los hiervan — die komt alleen uit de
discussieboom en kan niemand zetten.

Alleen schema/structuur. Bestaande rijen → 'goedgekeurd' (ze stonden al live).
De live-DB krijgt geen CHECK (net als bij `aard`); de CHECK leeft in schema.sql
voor verse builds.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"


def kolommen(conn, tabel):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({tabel})")]


def main():
    backup = DB.with_name(f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    for tabel in ("entities", "relations"):
        if "status" in kolommen(conn, tabel):
            print(f"{tabel}: status bestaat al, overslaan")
            continue
        conn.execute(
            f"ALTER TABLE {tabel} ADD COLUMN status TEXT NOT NULL DEFAULT 'goedgekeurd'")
        n = conn.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
        print(f"{tabel}: status toegevoegd, {n} bestaande rijen op 'goedgekeurd'")
    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    main()
