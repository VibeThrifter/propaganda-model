"""
Modelreview — `eigenaar_directiekeuze` prozafix: het IS een directe pijl.

De schakel mediaeigenaar → directie staat nu (terecht) op aard='direct'
(migrate_reclassify_indirect_to_direct.py: een edge tussen twee nodes is direct). De
beschrijving sprak echter nog van "gemedieerd, niet rechtstreeks" — dat botst met de
directe aard. Deze migratie trekt de tekst recht: de eigenaar kíést de directie (het *wat*,
direct), terwijl het juridische *hoe* (de keten STAK → RvC → directie, of bij de eenlaagse
Belgische eigenaren de algemene vergadering rechtstreeks) in de keten-mechanismen blijft
staan (stak_stemzeggenschap → commissarisbenoeming → directiebenoeming).

Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECH = "eigenaar_directiekeuze"
DESCRIPTION = (
    "De keuze van de directie door de eigenaar — de directe uitdrukking van eigenaarsmacht "
    "over wie de mediaorganisatie leidt. Dit is het *wat*: ongeacht de juridische vorm bepaalt "
    "de eigenaar de directie. Het *hoe* staat in de keten: bij een STAK-/tweelaags bestel via "
    "eigenaar → STAK → Raad van Commissarissen → directie (de eigenaar benoemt de RvC en zit er "
    "vaak zelf in); bij de feitelijke (Belgische, vaak eenlaagse) eigenaren benoemt de algemene "
    "vergadering het bestuur rechtstreeks. Detail: stak_stemzeggenschap → commissarisbenoeming "
    "→ directiebenoeming."
)
EFFECT = (
    "Het dagelijks bestuur dat de krant leidt is door de eigenaar geselecteerd op passendheid "
    "bij het eigenaarsbelang; die eigenaarsvoorkeur bepaalt zo de directie en daarmee — via "
    "benoemingspolitiek — de benoeming van de hoofdredacteur."
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

    row = conn.execute("SELECT id, aard FROM mechanisms WHERE name=?", (MECH,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: mechanisme '{MECH}' niet gevonden.")
    mid, aard = row
    if aard != "direct":
        print(f"WAARSCHUWING: aard is '{aard}', verwacht 'direct'. Zet 'm op direct.")
        conn.execute("UPDATE mechanisms SET aard='direct' WHERE id=?", (mid,))

    conn.execute("UPDATE mechanisms SET description=?, effect=? WHERE id=?",
                 (DESCRIPTION, EFFECT, mid))
    conn.commit()

    name, aard, desc = conn.execute(
        "SELECT name, aard, description FROM mechanisms WHERE id=?", (mid,)).fetchone()
    print(f"\n{name} [{aard}] bijgewerkt:")
    print(" ", desc)
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
