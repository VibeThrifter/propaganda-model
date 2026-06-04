"""
Modelreview — expertise-keten: denktank -> persbureau toevoegen.

Sluitstuk op de denktank-routing. Naast de twee al bestaande routes naar de media —
institutioneel (`expert_framing`: denktank -> mediaorganisatie) en via de persoon
(`denktank_levert_expert` -> `expert_legitimatie`: denktank -> gezagsexpert -> journalist) —
loopt er een derde route via de BOVENKANT van de keten: denktank-rapporten en persberichten
worden door het persbureau (ANP) als kant-en-klare, 'gezaghebbende' kopij opgepikt en via
`pakketjournalistiek` landelijk uniform doorgegeven.

Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECH = {
    "name": "denktank_naar_persbureau",
    "filter": "sourcing",
    "mechanism_type": "procedureel",
    "source_role": "denktank",
    "target_role": "persbureau",
    "description": (
        "Denktank-rapporten en persberichten worden door het persbureau (ANP) opgepikt als "
        "kant-en-klare, 'gezaghebbende' kopij en grotendeels ongecontroleerd doorgegeven. Derde route "
        "naast `expert_framing` (rechtstreeks naar de titels) en `denktank_levert_expert` → "
        "`expert_legitimatie` (via de persoon): hier loopt de denktank-agenda via de bovenkant van de "
        "nieuwsketen."
    ),
    "effect": (
        "Via `pakketjournalistiek` plant de denktank-framing zich vrijwel gelijktijdig door alle titels "
        "voort; de belangengebonden oorsprong blijft onzichtbaar achter het neutrale persbureau-stempel. "
        "Sluit aan op `persbureau_brongebondenheid`."
    ),
}


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bp = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, bp)
    print(f"Backup gemaakt: {bp.name}")


def role_id(conn, name):
    r = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not r:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return r[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    sid, tid = role_id(conn, MECH["source_role"]), role_id(conn, MECH["target_role"])
    if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (MECH["name"],)).fetchone():
        conn.execute(
            "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, source_role_id=?, target_role_id=? WHERE name=?",
            (MECH["filter"], MECH["mechanism_type"], MECH["description"], MECH["effect"], sid, tid, MECH["name"]),
        )
        print(f"  bijgewerkt (bestond al): {MECH['name']}")
    else:
        conn.execute(
            "INSERT INTO mechanisms (name, filter, mechanism_type, description, effect, source_role_id, target_role_id) VALUES (?,?,?,?,?,?,?)",
            (MECH["name"], MECH["filter"], MECH["mechanism_type"], MECH["description"], MECH["effect"], sid, tid),
        )
        print(f"  toegevoegd: {MECH['name']} ({MECH['filter']}) {MECH['source_role']} → {MECH['target_role']}")

    conn.commit()
    row = conn.execute(
        """SELECT m.filter, sr.name, tr.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
           WHERE m.name=?""", (MECH["name"],)
    ).fetchone()
    print(f"  verificatie: {MECH['name']} — filter={row[0]}, {row[1]} → {row[2]}")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n}.")


if __name__ == "__main__":
    main()
