"""
Modelreview — ontbrekende relatie toevoegen: belanghebbende -> partij (directe financiering).

Het model dekte de belanghebbende-principaal die de politiek beïnvloedt via INSTRUMENTEN
(lobbyist: `belangenbehartiging`/`lobbyist_naar_politicus`; denktank: `denktank_*`;
adverteerder: `adverteren_als_belang`). Maar een belanghebbende kan een politieke partij
ook RECHTSTREEKS financieren — via giften, donaties of sponsoring, zónder lobbyist als
tussenschakel. Dat directe geldkanaal naar de politieke principaal ontbrak.

Laag 1 blijft generiek; concrete giften horen in de instantielaag met bronvermelding
(relation_type `donor`/`financiering`). Geen schemawijziging; idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECH = {
    "name": "partijfinanciering",
    "filter": "cross_filter",
    "mechanism_type": "economisch",
    "source_role": "belanghebbende",
    "target_role": "partij",
    "description": (
        "Een belanghebbende (bedrijf, sector, branche, vermogend individu, ideologische beweging) "
        "financiert een politieke partij rechtstreeks via giften, donaties of sponsoring — zónder "
        "lobbyist als tussenschakel. Naast de instrument-routes (lobbyist, denktank, adverteerder) "
        "is dit het directe geldkanaal naar de politieke principaal. In NL deels zichtbaar via de "
        "giftenregeling, maar grote giften en indirecte constructies blijven beperkt transparant."
    ),
    "effect": (
        "Financiële afhankelijkheid en goodwill: de partij krijgt middelen, de donor bevoorrechte "
        "toegang en een welwillend oor. De partijagenda en -lijn (`partijlijn`, "
        "`gecoordineerde_voorlichting`) raken vooraf afgestemd op donorbelangen, die zo "
        "stroomafwaarts doorwerken in de politieke bronstroom en het publieke debat — zonder dat de "
        "herkomst zichtbaar is."
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
