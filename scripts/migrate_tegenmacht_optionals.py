"""
Modelreview — tegenmacht: de twee optionals afmaken.

1. continuiteitsborging  : borgingsstichting -> mediaorganisatie
   De borgingsstichting beschermt niet alleen de redactionele onafhankelijkheid maar ook
   de CONTINUITEIT van de titel: met haar prioriteitsaandeel/vetorecht kan ze verkoop,
   opheffing of opsplitsing van de mediaorganisatie blokkeren.

2. afgedwongen_borging   : toezichthouder -> borgingsstichting
   De causale lijn die uit `toezichthouder_interventie` bleek: bij goedkeuring van een
   mediaconcentratie kan de ACM een onafhankelijke borgingsstichting met vetorecht
   afdwingen (DPG-RTL-voorwaarden). Een deel van de tegenmacht is dus een product van
   het toezicht, niet vrijwillig.

Geen schemawijziging. Idempotent. Backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NEW_MECHANISMS = [
    {
        "name": "continuiteitsborging",
        "filter": "tegenmacht",
        "mechanism_type": "juridisch",
        "description": (
            "De borgingsstichting gebruikt haar prioriteitsaandeel/vetorecht om de continuïteit en "
            "het zelfstandig voortbestaan van de titel te beschermen: ze kan verkoop, opheffing of "
            "opsplitsing van de mediaorganisatie blokkeren."
        ),
        "effect": (
            "Een titel kan niet zonder meer worden afgestoten of opgeheven door de winstgedreven "
            "eigenaar; structurele bescherming van het bestaansrecht, geen ijzeren garantie."
        ),
        "source_role": "borgingsstichting",
        "target_role": "mediaorganisatie",
    },
    {
        "name": "afgedwongen_borging",
        "filter": "tegenmacht",
        "mechanism_type": "juridisch",
        "description": (
            "Bij goedkeuring van een mediaconcentratie kan de toezichthouder (ACM) als structurele "
            "voorwaarde een onafhankelijke borgingsstichting met vetorecht over de hoofdredacteur "
            "afdwingen (zoals bij DPG-RTL). De interventie op concentratie creëert zo de tegenmacht "
            "die de redactionele onafhankelijkheid bewaakt."
        ),
        "effect": (
            "Een deel van de borgingsstichtingen ontstaat niet vrijwillig maar als opgelegde "
            "overnamevoorwaarde; de tegenmacht is dan een product van het toezicht."
        ),
        "source_role": "toezichthouder",
        "target_role": "borgingsstichting",
    },
]


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

    print("\n-- nieuwe tegenmacht-mechanismen --")
    for m in NEW_MECHANISMS:
        sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
        exists = conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone()
        if exists:
            conn.execute(
                """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
                   source_role_id=?, target_role_id=? WHERE name=?""",
                (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]),
            )
            print(f"  bijgewerkt: {m['name']} ({m['source_role']} → {m['target_role']})")
        else:
            conn.execute(
                """INSERT INTO mechanisms (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid),
            )
            print(f"  toegevoegd: {m['name']} ({m['filter']}) {m['source_role']} → {m['target_role']}")

    conn.commit()

    print("\n== verificatie: volledige tegenmacht rond de borgingsstichting ==")
    for r in conn.execute(
        """SELECT m.name, sr.name, tr.name FROM mechanisms m
           LEFT JOIN roles sr ON sr.id=m.source_role_id LEFT JOIN roles tr ON tr.id=m.target_role_id
           WHERE 'borgingsstichting' IN (sr.name, tr.name) OR m.name IN ('toezichthouder_interventie','toezicht_tandeloosheid')
           ORDER BY m.name"""
    ).fetchall():
        print(f"  {r[1]} → {r[2]:<18} {r[0]}")

    nmech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen totaal: {nmech}.")


if __name__ == "__main__":
    main()
