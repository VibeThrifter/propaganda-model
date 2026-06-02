"""Migratie: verlaag zekerheid van onbronnde relaties van 0.1 naar 0.05.

Achtergrond:
Relaties zonder een echte (niet-AI) bron stonden op certainty = 0.1 (zie
migrate_remove_ai_source.py). Een onbronnde bewering verdient een nog lagere
zekerheid, dus de baseline voor onbronnde relaties wordt 0.05.

Alleen relaties die nu exact op de oude onbronnde-baseline (0.1) staan én geen
enkele citatie hebben worden aangepast. Relaties met een echte bron (zoals
relatie 20 op 0.85) en relaties met een afwijkende, bewust gekozen score blijven
ongemoeid.

Conform repo-conventie: maakt eerst een backup van de DB.
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

OLD_UNSOURCED_CERTAINTY = 0.1
NEW_UNSOURCED_CERTAINTY = 0.05


def migrate():
    # --- Backup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # --- Relaties met een echte bron (een argument met citatie) blijven ongemoeid ---
    sourced_relations = {row[0] for row in cur.execute(
        """SELECT DISTINCT a.relation_id
           FROM arguments a
           JOIN citations c ON c.argument_id = a.id
           WHERE a.relation_id IS NOT NULL"""
    ).fetchall()}
    print(f"Relaties met bron (ongemoeid): {sorted(sourced_relations)}")

    # --- Verlaag onbronnde relaties van 0.1 naar 0.05 ---
    if sourced_relations:
        keep_ph = ",".join("?" * len(sourced_relations))
        n_rel = cur.execute(
            f"""UPDATE relations SET certainty = ?
                WHERE certainty = ? AND id NOT IN ({keep_ph})""",
            [NEW_UNSOURCED_CERTAINTY, OLD_UNSOURCED_CERTAINTY, *sorted(sourced_relations)],
        ).rowcount
    else:
        n_rel = cur.execute(
            "UPDATE relations SET certainty = ? WHERE certainty = ?",
            [NEW_UNSOURCED_CERTAINTY, OLD_UNSOURCED_CERTAINTY],
        ).rowcount
    print(f"certainty {OLD_UNSOURCED_CERTAINTY} -> {NEW_UNSOURCED_CERTAINTY} "
          f"voor {n_rel} onbronnde relaties.")

    # --- Audit log ---
    summary = {
        "van_certainty": OLD_UNSOURCED_CERTAINTY,
        "naar_certainty": NEW_UNSOURCED_CERTAINTY,
        "aangepaste_relaties": n_rel,
        "relaties_met_bron_ongemoeid": sorted(sourced_relations),
    }
    cur.execute(
        """INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
           VALUES ('relations', 0, 'updated', 'migratie', ?, ?)""",
        (json.dumps(summary),
         f"Onbronnde relaties verlaagd van certainty {OLD_UNSOURCED_CERTAINTY} "
         f"naar {NEW_UNSOURCED_CERTAINTY}."),
    )

    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    migrate()
