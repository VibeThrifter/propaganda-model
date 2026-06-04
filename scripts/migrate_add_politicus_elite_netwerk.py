"""
Modelreview — ontbrekende relatie toevoegen: politicus -> elite_forum.

De participatie-as van de elite-fora was incompleet: het model had wél
`mediaeigenaar_elite_netwerk` (mediaeigenaar -> elite_forum) en `belang_elite_netwerk`
(belanghebbende -> elite_forum), maar de POLITICUS als deelnemer ontbrak — terwijl dat
een kernroute is. Politici nemen deel aan besloten elite-fora (Bilderberg, WEF/Davos,
Trilaterale Commissie) en aan talent-/wervingsprogramma's als het WEF Young Global
Leaders-programma, dat opkomende politici selecteert en vormt. Daar wordt hun wereldbeeld
gesynchroniseerd met de transnationale kapitaalklasse.

Dit staat los van het in ronde C geschrapte `elite_forum_flak` (dat was elite_forum ->
journalist als 'flak' — een miscategorie). Dit is de legitieme participatie/co-optatie-as.

Laag 1 blijft generiek (geen namen); concrete deelnemers horen in de instantielaag met
bronvermelding. Geen schemawijziging; idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECH = {
    "name": "politicus_elite_netwerk",
    "filter": "cross_filter",
    "mechanism_type": "structureel",
    "source_role": "politicus",
    "target_role": "elite_forum",
    "description": (
        "Politici nemen deel aan besloten elite-fora (Bilderberg, WEF/Davos, Trilaterale "
        "Commissie) en aan talent-/wervingsprogramma's als het WEF Young Global Leaders-programma, "
        "dat opkomende politici selecteert en vormt. Spiegelt `mediaeigenaar_elite_netwerk` en "
        "`belang_elite_netwerk`: dezelfde fora binden eigenaar, belanghebbende én politicus."
    ),
    "effect": (
        "Het wereldbeeld van de transnationale kapitaalklasse (vrijemarkt, pro-Atlantisch, "
        "'stakeholder capitalism') wordt buiten het democratische proces met de politiek "
        "afgestemd; via een gedeeld referentiekader en old-boys-netwerk vervaagt de scheiding "
        "tussen gekozen bestuur en private elite. De socialisatie/co-optatie maakt politici "
        "dragers van de elite-consensus."
    ),
}


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{timestamp}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return row[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    sid, tid = role_id(conn, MECH["source_role"]), role_id(conn, MECH["target_role"])
    exists = conn.execute("SELECT 1 FROM mechanisms WHERE name = ?", (MECH["name"],)).fetchone()
    if exists:
        conn.execute(
            """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
               source_role_id=?, target_role_id=? WHERE name=?""",
            (MECH["filter"], MECH["mechanism_type"], MECH["description"], MECH["effect"],
             sid, tid, MECH["name"]),
        )
        print(f"  bijgewerkt (bestond al): {MECH['name']}")
    else:
        conn.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (MECH["name"], MECH["filter"], MECH["mechanism_type"], MECH["description"],
             MECH["effect"], sid, tid),
        )
        print(f"  toegevoegd: {MECH['name']} ({MECH['filter']}) {MECH['source_role']} → {MECH['target_role']}")

    conn.commit()

    # verificatie
    row = conn.execute(
        """SELECT m.filter, sr.name, tr.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
           WHERE m.name=?""", (MECH["name"],)
    ).fetchone()
    print(f"  verificatie: {MECH['name']} — filter={row[0]}, {row[1]} → {row[2]}")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    print("\n  elite-forum participatie-as nu compleet:")
    for nm in ("mediaeigenaar_elite_netwerk", "belang_elite_netwerk", "politicus_elite_netwerk"):
        r = conn.execute(
            """SELECT sr.name, tr.name FROM mechanisms m
               JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
               WHERE m.name=?""", (nm,)
        ).fetchone()
        print(f"    {nm}: {r[0]} → {r[1]}")
    conn.close()
    print(f"\nKlaar. Mechanismen: {n}.")


if __name__ == "__main__":
    main()
