"""Migratie: AI-analyse telt niet als academische bron.

Achtergrond:
De database is grotendeels gevuld vanuit één AI-analyse (sources.author
'AI-analyse (Claude)'). AI-gegenereerde tekst is geen verifieerbare bron in de
zin van het discussieboom-model, dus die "bron" en alle bijbehorende citaties
worden verwijderd. Vervolgens krijgt elke relatie die daarna geen enkele echte
(niet-AI) bron meer onderbouwt een lage zekerheid (certainty = 0.05), omdat de
bewering feitelijk onbronnd is.

Relaties die wél een echte bron behouden (een argument met een citatie naar een
niet-AI bron, zoals Chomsky, Bergman, WRR of ACM) houden hun bestaande
certainty.

Conform repo-conventie: maakt eerst een backup van de DB.
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

UNSOURCED_CERTAINTY = 0.05


def migrate():
    # --- Backup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # --- 1. Identificeer de AI-bron(nen) ---
    ai_ids = [row[0] for row in cur.execute(
        "SELECT id FROM sources WHERE author LIKE '%AI-analyse%' OR author LIKE '%AI %' OR author LIKE '%(Claude)%'"
    ).fetchall()]
    if not ai_ids:
        print("Geen AI-bron gevonden — niets te doen.")
        conn.close()
        return
    placeholders = ",".join("?" * len(ai_ids))
    print(f"AI-bron(nen): {ai_ids}")

    # --- 2. Bepaal welke relaties een echte (niet-AI) bron behouden ---
    sourced_relations = {row[0] for row in cur.execute(
        f"""SELECT DISTINCT a.relation_id
            FROM arguments a
            JOIN citations c ON c.argument_id = a.id
            WHERE a.relation_id IS NOT NULL
              AND c.source_id NOT IN ({placeholders})""",
        ai_ids,
    ).fetchall()}
    print(f"Relaties met echte bron (behouden certainty): {sorted(sourced_relations)}")

    # --- 3. Verwijder AI-citaties, -mentions, -locaties en de bron zelf ---
    n_cit = cur.execute(
        f"DELETE FROM citations WHERE source_id IN ({placeholders})", ai_ids
    ).rowcount
    n_mentions = cur.execute(
        f"DELETE FROM source_mentions WHERE source_id IN ({placeholders})", ai_ids
    ).rowcount
    n_loc = cur.execute(
        f"DELETE FROM source_locations WHERE source_id IN ({placeholders})", ai_ids
    ).rowcount
    n_src = cur.execute(
        f"DELETE FROM sources WHERE id IN ({placeholders})", ai_ids
    ).rowcount
    print(f"Verwijderd: {n_cit} citaties, {n_mentions} mentions, "
          f"{n_loc} locaties, {n_src} bron(nen).")

    # --- 4. Zet certainty = 0.05 op alle relaties zonder echte bron ---
    if sourced_relations:
        keep_ph = ",".join("?" * len(sourced_relations))
        n_rel = cur.execute(
            f"UPDATE relations SET certainty = ? WHERE id NOT IN ({keep_ph})",
            [UNSOURCED_CERTAINTY, *sorted(sourced_relations)],
        ).rowcount
    else:
        n_rel = cur.execute(
            "UPDATE relations SET certainty = ?", [UNSOURCED_CERTAINTY]
        ).rowcount
    print(f"certainty -> {UNSOURCED_CERTAINTY} voor {n_rel} onbronnde relaties.")

    # --- 5. Audit log ---
    now_summary = {
        "verwijderde_bron_ids": ai_ids,
        "verwijderde_citaties": n_cit,
        "verwijderde_mentions": n_mentions,
        "onbronnde_relaties_op_0.05": n_rel,
        "relaties_met_echte_bron": sorted(sourced_relations),
    }
    cur.execute(
        """INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
           VALUES ('sources', ?, 'deleted', 'migratie', ?, ?)""",
        (ai_ids[0], json.dumps(now_summary),
         "AI-analyse telt niet als academische bron; bron en citaties verwijderd, "
         "onbronnde relaties op certainty 0.05 gezet."),
    )

    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    migrate()
