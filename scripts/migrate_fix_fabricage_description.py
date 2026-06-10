"""
Viz-review — beschrijving van het emergente veld `fabricage_van_consensus` klopte niet.

De tekst zei "het samenspel van de vijf filters (eigendom, advertentie, sourcing, ideologie)"
— vijf aangekondigd, vier opgesomd (flak ontbrak). Opsomming compleet gemaakt.

Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NAME = "fabricage_van_consensus"
OLD_FRAGMENT = "(eigendom, advertentie, sourcing, ideologie)"
NEW_FRAGMENT = "(eigendom, advertentie, sourcing, flak, ideologie)"


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, description FROM emergent_effects WHERE name=?", (NAME,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: emergent effect '{NAME}' niet gevonden.")
    eid, desc = row
    if NEW_FRAGMENT in (desc or ""):
        print(f"{NAME}: al gefixt, overslaan.")
    elif OLD_FRAGMENT in (desc or ""):
        conn.execute("UPDATE emergent_effects SET description=? WHERE id=?",
                     (desc.replace(OLD_FRAGMENT, NEW_FRAGMENT), eid))
        conn.commit()
        print(f"{NAME}: opsomming compleet gemaakt (flak toegevoegd).")
    else:
        raise SystemExit(f"FOUT: verwacht fragment niet gevonden in description van '{NAME}'.")
    conn.close()
    print("Klaar. Vergeet niet: python3 scripts/generate_viz.py")


if __name__ == "__main__":
    main()
