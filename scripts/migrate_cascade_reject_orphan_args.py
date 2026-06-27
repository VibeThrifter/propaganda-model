"""Migratie: reject wees-argumenten onder een al-afgewezen element.

Achtergrond (eigenaarsbesluit juni 2026):
Argumenten *bouwen* het element — een relatie/entiteit is niets zonder de
onderbouwende discussieboom. Voortaan rejecteert het afwijzen van een
entiteit/relatie ook haar argument(sub)boom mee (`_modereer` in server.py):
geen wees-argumenten die als 'voorgesteld' in de wachtrij blijven hangen voor
een element dat er niet meer is, en die — verworpen — netjes in de
Afgewezen-flow verschijnen waar je ze kunt verbeteren & heropenen.

Deze migratie maakt de bestaande data consistent met die nieuwe invariant:
elk niet-verworpen, niet-vervangen argument (root of reactie) dat hangt onder
een entiteit/relatie met status 'afgewezen' wordt 'verworpen'. Voor de
cascade nieuw was, zijn zulke argumenten al-afgewezen blijven staan als
'voorgesteld' (ze vervuilden zelfs de Argumenten-wachtrij).

Geen score-effect: scoring.py telt alleen goedgekeurde elementen, en een
verworpen argument weegt sowieso 0. Het is dus structuur/consistentie, geen
inhoud — en valt daarmee buiten de dogfood-regel (M0.6). De oude statussen
gaan in het edit_log zodat heropenen (verworpen → voorgesteld) mogelijk blijft.

Conform repo-conventie: maakt eerst een backup van de DB.
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def migrate():
    # --- Backup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Wees-argumenten: niet-verworpen, niet-vervangen argumenten in de (sub)boom van een
    # afgewezen element. De recursieve CTE pakt de root-argumenten die op het element wijzen
    # plus al hun reacties (replies dragen geen eigen doel, M1.1).
    sql = """
        WITH RECURSIVE boom(id) AS (
          SELECT a.id FROM arguments a
          WHERE a.parent_argument_id IS NULL AND (
                a.relation_id IN (SELECT id FROM relations WHERE status = 'afgewezen')
             OR a.entity_id   IN (SELECT id FROM entities  WHERE status = 'afgewezen'))
          UNION ALL
          SELECT a.id FROM arguments a JOIN boom b ON a.parent_argument_id = b.id
        )
        SELECT a.id, a.status, a.relation_id, a.entity_id FROM arguments a
        WHERE a.id IN (SELECT id FROM boom) AND a.status <> 'verworpen' AND NOT a.vervangen
        ORDER BY a.id
    """
    rijen = cur.execute(sql).fetchall()
    if not rijen:
        print("Niets te reconciliëren: geen wees-argumenten onder afgewezen elementen.")
        conn.commit()
        conn.close()
        return

    for ar in rijen:
        doel = (f"relations #{ar['relation_id']}" if ar["relation_id"]
                else f"entities #{ar['entity_id']}")
        cur.execute("UPDATE arguments SET status = 'verworpen' WHERE id = ?", (ar["id"],))
        cur.execute(
            """INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
               VALUES ('arguments', ?, 'updated', 'migratie', ?, ?, ?)""",
            (ar["id"], json.dumps({"status": ar["status"]}),
             json.dumps({"status": "verworpen"}),
             f"mee-afgewezen met {doel} (reconciliatie cascade-invariant)"))
        print(f"  argument #{ar['id']}: {ar['status']} → verworpen ({doel})")

    print(f"{len(rijen)} wees-argument(en) ge-rejecteerd onder afgewezen elementen.")
    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    migrate()
