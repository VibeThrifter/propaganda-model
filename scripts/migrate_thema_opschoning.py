"""
Thema-audit (modelreview juni 2026): systemisch-thema weg, drie tagging-gaten dicht.

1. Het thema 'systemisch' vervalt. Systemisch-zijn wordt sinds de aard-taxonomie
   structureel gecodeerd: een staande systeemtoestand is een veld_eigenschap (halo),
   een groepseigenschap een emergent_effects-hyperedge. Een thema-as ernaast was
   dubbelop en willekeurig gevuld (2 van de 7 halo's, plus eigendomsconcentratie).
   De enum-waarde blijft in schema.sql staan (deprecated) voor migratie-replay,
   zoals bij de deprecated aard-waarden.

2. Drie gaten gedicht:
   - academische_socialisatie_hoofdredacteur -> kennis_expertise (zijn vijf
     zusjes-mechanismen dragen het allemaal; vergeten bij een latere migratie);
   - preselectie_hoofdredacteur en hoofdredacteur_als_filter -> benoemingsketen
     (de ideologische voorselectie ín, resp. het doorgeefluik ná de benoeming —
     het dwarsverband stopte net vóór de hoofdredacteur).

Idempotent; backup-then-migrate. Daarna: python3 scripts/generate_viz.py
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

TOEVOEGEN = [
    ("academische_socialisatie_hoofdredacteur", "kennis_expertise"),
    ("preselectie_hoofdredacteur", "benoemingsketen"),
    ("hoofdredacteur_als_filter", "benoemingsketen"),
]


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    n = cur.execute("DELETE FROM mechanism_themes WHERE theme='systemisch'").rowcount
    print(f"- thema systemisch verwijderd ({n} koppelingen)")

    for mech, thema in TOEVOEGEN:
        row = cur.execute("SELECT id FROM mechanisms WHERE name=?", (mech,)).fetchone()
        if row is None:
            raise SystemExit(f"FOUT: mechanisme '{mech}' niet gevonden.")
        nieuw = cur.execute(
            "INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (?,?)",
            (row[0], thema)).rowcount
        print(f"{'+' if nieuw else '='} {mech} -> {thema}")

    con.commit()
    for thema, aantal in cur.execute(
            "SELECT theme, COUNT(*) FROM mechanism_themes GROUP BY theme ORDER BY theme"):
        print(f"  {thema:18s}: {aantal}")
    con.close()
    print("klaar. Vergeet niet: python3 scripts/generate_viz.py")


if __name__ == "__main__":
    main()
