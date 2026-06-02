"""
Verrijking: de bovenstroomse vangst van het persbureau (Herman & Chomsky, filter 3).

Probleem: in de theorie wees alles WEG van het persbureau (pakketjournalistiek), maar niets
ernaartoe. Terwijl de kern van het derde filter juist is dat het persbureau zelf gevangen is
door zijn bronnen: het relayeert onder outputdruk grotendeels ongecontroleerd de persberichten
en officiele verklaringen van voorlichters/instituties. Daardoor is het een force-multiplier
voor officiele bronnen: een persbericht wordt via het persbureau in alle titels tegelijk nieuws.

Deze migratie:
  1. Nieuw `persbureau_brongebondenheid` (voorlichter -> persbureau) — de bovenstroomse vangst.
  2. Verwijdert het dode duplicaat `persbureau_naar_redactie` (0 instance-relaties; bijna
     letterlijk gelijk aan `pakketjournalistiek`).
  3. Scherpt `pakketjournalistiek` aan: maakt het chokepoint expliciet.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NEW_MECHANISM = {
    "name": "persbureau_brongebondenheid",
    "filter": "sourcing",
    "mechanism_type": "structureel",
    "description": (
        "Het persbureau moet continu, goedkoop en 'gezaghebbend' produceren en leunt daarom op "
        "kant-en-klare persberichten en officiele verklaringen van voorlichters en instituties, "
        "die het grotendeels ongecontroleerd doorgeeft."
    ),
    "effect": (
        "Het persbureau concentreert de afhankelijkheid van officiele bronnen en amplificeert die "
        "vervolgens landelijk via 'pakketjournalistiek': een persbericht wordt zo in alle titels "
        "tegelijk 'nieuws'. Het bureau is daarmee niet alleen een uniformerings- maar ook een "
        "bias-versterker aan de bovenkant van de keten."
    ),
    "source_role": "voorlichter",
    "target_role": "persbureau",
}

PAKKET_EFFECT = (
    "Homogenisering en concentratie: veel titels, een bron. Een keuze, omissie of framing bij "
    "het persbureau plant zich vrijwel gelijktijdig door het hele land voort (chokepoint). De "
    "diversiteit aan koppen verhult zo een gedeelde, smalle bronbasis."
)


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, dest)
    print(f"Backup gemaakt: {dest.name}")


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return row[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. nieuw mechanisme
    m = NEW_MECHANISM
    sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
    if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone():
        conn.execute(
            """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
               source_role_id=?, target_role_id=? WHERE name=?""",
            (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]))
        print(f"Mechanisme bijgewerkt: {m['name']} ({m['source_role']} -> {m['target_role']})")
    else:
        conn.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
               VALUES (?,?,?,?,?,?,?)""",
            (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid))
        print(f"Mechanisme toegevoegd: {m['name']} ({m['source_role']} -> {m['target_role']})")

    # 2. duplicaat persbureau_naar_redactie verwijderen (alleen als 0 relaties)
    row = conn.execute("SELECT id FROM mechanisms WHERE name='persbureau_naar_redactie'").fetchone()
    if row:
        n = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (row[0],)).fetchone()[0]
        if n == 0:
            conn.execute("DELETE FROM mechanisms WHERE id=?", (row[0],))
            print("Verwijderd: persbureau_naar_redactie (duplicaat, 0 relaties)")
        else:
            print(f"NIET verwijderd: persbureau_naar_redactie nog in gebruik ({n} relaties)")
    else:
        print("persbureau_naar_redactie bestaat niet (al opgeruimd).")

    # 3. pakketjournalistiek-effect aanscherpen
    cur = conn.execute("UPDATE mechanisms SET effect=? WHERE name='pakketjournalistiek'", (PAKKET_EFFECT,))
    if cur.rowcount:
        print("Aangescherpt: pakketjournalistiek (chokepoint expliciet)")

    conn.commit()
    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    mech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")
    print(f"\nKlaar. Totaal mechanismen: {mech}")


if __name__ == "__main__":
    main()
