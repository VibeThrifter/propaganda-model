"""Voeg de soort 'herformuleren' toe aan de CHECK-constraints van `voorstellen`
en `lineage`.

Aanleiding: titel/beschrijving van een node/edge moeten — net als op Wikipedia /
in open source — door iedereen *voorgesteld* en via review goedgekeurd kunnen
worden (soort 'herformuleren'), met de maintainer als enige die direct mag
bewerken. SQLite kan een CHECK niet in-place wijzigen, dus beide tabellen worden
herbouwd (de 12-staps-procedure, met foreign_keys uit).

Alleen schema/structuur — geen inhoud. Conform de backup-then-migrate-conventie.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"

NIEUW_VOORSTELLEN = """
CREATE TABLE voorstellen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    soort TEXT NOT NULL CHECK(soort IN (
        'nieuw_theorie_element',
        'splitsen',
        'samenvoegen',
        'hernoemen',
        'herformuleren'          -- titel/beschrijving bewerken via review (Wikipedia/OSS)
    )),
    titel TEXT NOT NULL,
    payload JSON NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN (
        'open', 'geaccepteerd', 'afgewezen', 'ingetrokken'
    )),
    ingediend_door TEXT NOT NULL REFERENCES users(username),
    resultaat JSON,
    besloten_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

NIEUW_LINEAGE = """
CREATE TABLE lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    soort TEXT NOT NULL CHECK(soort IN (
        'splitsen', 'samenvoegen', 'hernoemen', 'herformuleren'
    )),
    element_type TEXT NOT NULL CHECK(element_type IN (
        'rol', 'mechanisme', 'entiteit', 'relatie', 'emergent_effect'
    )),
    oud_id INTEGER NOT NULL,
    nieuw_id INTEGER NOT NULL,
    voorstel_id INTEGER NOT NULL REFERENCES voorstellen(id),
    reden TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

INDEXES = [
    "CREATE INDEX idx_voorstellen_status ON voorstellen(status)",
    "CREATE INDEX idx_lineage_oud ON lineage(element_type, oud_id)",
    "CREATE INDEX idx_lineage_nieuw ON lineage(element_type, nieuw_id)",
]


def kolommen(conn, tabel):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({tabel})")]


def main():
    backup = DB.with_name(f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()
    cur.execute("BEGIN")
    try:
        for tabel, ddl in (("voorstellen", NIEUW_VOORSTELLEN), ("lineage", NIEUW_LINEAGE)):
            kols = ", ".join(kolommen(conn, tabel))
            cur.execute(ddl.replace(f"CREATE TABLE {tabel}", f"CREATE TABLE {tabel}_new"))
            cur.execute(f"INSERT INTO {tabel}_new ({kols}) SELECT {kols} FROM {tabel}")
            cur.execute(f"DROP TABLE {tabel}")
            cur.execute(f"ALTER TABLE {tabel}_new RENAME TO {tabel}")
        for idx in INDEXES:
            cur.execute(idx)
        kapot = conn.execute("PRAGMA foreign_key_check").fetchall()
        if kapot:
            raise RuntimeError(f"foreign_key_check faalt: {kapot}")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")

    soorten = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='voorstellen'").fetchone()[0]
    print("herformuleren in voorstellen-CHECK:", "herformuleren" in soorten)
    print("rijen behouden:",
          conn.execute("SELECT count(*) FROM voorstellen").fetchone()[0], "voorstellen,",
          conn.execute("SELECT count(*) FROM lineage").fetchone()[0], "lineage")
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    main()
