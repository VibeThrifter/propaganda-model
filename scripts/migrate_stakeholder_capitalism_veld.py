"""
Modelreview — `stakeholder_capitalism_frame` herzien van direct kanaal naar emergent veld.

Reden: het was elite_forum -> mediaorganisatie (aard 'direct'), wat een gericht kanaal
suggereert dat er niet is. Het frame bereikt media niet rechtstreeks; het loopt via de
eigenaar, gelegitimeerde experts/denktanks, columnisten en YGL-politici (zie
migrate_add_elite_netwerk_routes.py) en landt als emergente 'common sense' bij het publiek.

Daarom:
  • aard:   direct            -> veld_instantiatie  (diffuse veld-regelmaat, geen dyade)
  • doel:   mediaorganisatie  -> publiek            (de normalisatie landt bij het publiek)
  • bron:   elite_forum (ongewijzigd — het frame komt uit de elite-club)
  • beschrijving bijgewerkt; effect ongewijzigd.

Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NEW_DESC = (
    "Het 'stakeholder capitalism'-frame van het elite-forum (WEF, Davos Manifesto 2020) wordt "
    "diffuus de publieke vanzelfsprekendheid: kapitalisme zelf als oplossing voor de problemen "
    "die het veroorzaakt. Géén direct kanaal naar de media — het frame loopt via de eigenaar "
    "(ideologische_synchronisatie), gelegitimeerde experts/denktanks (elite_kennisnetwerk -> "
    "expert_framing), columnisten (elite_media_netwerk) en YGL-politici (young_global_leaders), "
    "en landt als 'common sense' bij het publiek. Eindpunten zijn substitueerbaar: een "
    "veld-regelmaat, geen dyadisch verband."
)


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
    conn.execute("PRAGMA foreign_keys = ON")

    row = conn.execute("SELECT id FROM mechanisms WHERE name='stakeholder_capitalism_frame'").fetchone()
    if not row:
        raise SystemExit("FOUT: mechanisme 'stakeholder_capitalism_frame' niet gevonden.")
    mid = row[0]
    publiek = conn.execute("SELECT id FROM roles WHERE name='publiek'").fetchone()
    if not publiek:
        raise SystemExit("FOUT: rol 'publiek' niet gevonden.")
    publiek_id = publiek[0]

    conn.execute(
        "UPDATE mechanisms SET aard='veld_instantiatie', target_role_id=?, description=? WHERE id=?",
        (publiek_id, NEW_DESC, mid),
    )
    conn.commit()

    bron, doel, aard = conn.execute(
        "SELECT (SELECT name FROM roles WHERE id=source_role_id), "
        "(SELECT name FROM roles WHERE id=target_role_id), aard "
        "FROM mechanisms WHERE id=?", (mid,)
    ).fetchone()
    conn.close()
    print(f"stakeholder_capitalism_frame: {bron} -> {doel} [aard={aard}]")
    print("Klaar.")


if __name__ == "__main__":
    main()
