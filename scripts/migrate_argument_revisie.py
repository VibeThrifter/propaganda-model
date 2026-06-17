"""Migratie: argument-revisie (supersede via self-pointer).

Achtergrond (eigenaarsbesluit juni 2026):
Argumenten waren tot nu toe onveranderlijk — je kon er alleen op reageren.
De gebruiker wil een verbeter-lus: een nog-`voorgesteld` argument mag de auteur
in-place bijschaven (het telt nog nergens in mee), en een al gemerged argument
verbeter je via een REVISIE die het oude vervangt en opnieuw door de poort moet.

De bestaande `lineage`-tabel is hiervoor niet bruikbaar: `lineage.voorstel_id`
is NOT NULL en verwijst naar `voorstellen`, terwijl argument-merges juist NIET
via een voorstel lopen (de lichte mergeweg, M2.2). Daarom krijgt `arguments`
twee eigen kolommen — symmetrisch met de `vervangen`-vlag op de theorie-/
praktijktabellen (M2.6), maar met een self-pointer i.p.v. de lineage-tabel:

  - vervangen     BOOLEAN  — het oude argument is door een revisie opgevolgd;
                             scoring.py/influence.py/viz slaan het over (factor 0,
                             net als bij vervangen elementen).
  - reviseert_id  INTEGER  — een nog-voorgestelde revisie wijst naar het argument
                             dat het vervangt; bij merge zet de mergeweg het oude
                             argument op status 'verouderd' + vervangen = 1.

Conform repo-conventie: maakt eerst een backup. Dit is structuur (twee nieuwe
kolommen), geen inhoud, en valt buiten de dogfood-regel (M0.6).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def _heeft_kolom(cur, tabel, kolom) -> bool:
    return any(r[1] == kolom for r in cur.execute(f"PRAGMA table_info({tabel})"))


def migrate():
    if not DB_PATH.exists():
        raise SystemExit(f"DB niet gevonden: {DB_PATH} — bouw eerst (scripts/init_db.py …).")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    toegevoegd = []
    if not _heeft_kolom(cur, "arguments", "vervangen"):
        # NOT NULL met DEFAULT FALSE mag bij ADD COLUMN.
        cur.execute("ALTER TABLE arguments ADD COLUMN "
                    "vervangen BOOLEAN NOT NULL DEFAULT FALSE")
        toegevoegd.append("vervangen")
    if not _heeft_kolom(cur, "arguments", "reviseert_id"):
        # Nullable FK naar arguments(id); default NULL → ADD COLUMN met REFERENCES mag.
        cur.execute("ALTER TABLE arguments ADD COLUMN "
                    "reviseert_id INTEGER REFERENCES arguments(id)")
        toegevoegd.append("reviseert_id")

    conn.commit()
    conn.close()
    if toegevoegd:
        print(f"Kolommen toegevoegd aan arguments: {', '.join(toegevoegd)}")
    else:
        print("Niets te doen — beide kolommen bestonden al (idempotent).")


if __name__ == "__main__":
    migrate()
