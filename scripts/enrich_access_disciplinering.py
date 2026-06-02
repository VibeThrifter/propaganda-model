"""
Verrijking: access/cancelling-dynamiek in het propagandamodel.

Achtergrond: 'cancelling' (een gast die iets onwelgevalligs zegt wordt niet meer
uitgenodigd) en 'access' (wie er überhaupt aan tafel mag) zitten in het model van
Herman & Chomsky verspreid over twee filters:

  - Filter 4 (Flak): de straf/uitsluiting zelf -> bestaand mechanisme `deplatforming`
  - Filter 3 (Sourcing): access als schaarse hulpbron die media als beloning/straf
    inzetten -> nieuw mechanisme `toegangsdisciplinering`

Deze migratie:
  1. Scherpt `deplatforming` aan met de term 'cancelling', de access-symbiose en
     het kerninzicht dat redacties de uitsluiting niet als censuur ervaren maar
     rationaliseren als professioneel oordeel.
  2. Voegt het Sourcing-mechanisme `toegangsdisciplinering` toe: de symbiotische
     access-relatie waarin podium een beloning/straf-currency is (aanbodzijde).

Volgt de backup-then-migrate-conventie: kopieert de DB eerst naar
data/propaganda_model_backup_<timestamp>.db. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


# Aangescherpte tekst voor het bestaande Flak-mechanisme `deplatforming`
DEPLATFORMING_DESCRIPTION = (
    "Uitsluiten van stemmen uit de mainstream media — de hedendaagse 'cancelling'. "
    "Afwijkende experts worden simpelweg niet meer uitgenodigd (bv. Maarten van Rossem na "
    "Irak-kritiek): geen formeel verbod, de telefoon gaat enkel niet meer over. Het is het "
    "intrekken van een symbiotische toegangsrelatie (zie het sourcing-mechanisme "
    "'toegangsdisciplinering'): wie te veel institutionele flak oplevert, verliest zijn access."
)
DEPLATFORMING_EFFECT = (
    "Kritische stemmen bereiken minder publiek en verschuiven van geduide expert naar "
    "'querulant'. Redacties ervaren dit zelden als censuur maar rationaliseren het als "
    "professioneel oordeel ('niet objectief', 'te langdradig', 'het publiek haakt af') — "
    "het systeem houdt zichzelf zo geruisloos schoon van te radicale geluiden."
)

# Nieuw Sourcing-mechanisme: access als beloning/straf-currency (aanbodzijde)
NEW_MECHANISM = {
    "name": "toegangsdisciplinering",
    "filter": "sourcing",
    "mechanism_type": "structureel",
    "description": (
        "Access — een plek aan de talkshowtafel, de status van vaste deskundige — is "
        "een schaarse hulpbron die media als beloning én straf inzetten. Een dagelijkse "
        "talkshow moet elke avond de tafel vullen en leunt daarom op een poel 'veilige', "
        "terugkerende gasten. Wie de symbiose respecteert wordt herhaaldelijk uitgenodigd; wie "
        "fundamentele aannames uitdaagt verliest geruisloos zijn toegang."
    ),
    "effect": (
        "Potentiële gasten matigen zich preventief om hun podium te behouden "
        "(anticiperende zelfcensuur aan de aanbodzijde). De redactie bepaalt zo de facto welk "
        "spectrum aan stemmen structureel zichtbaar is, zonder ooit expliciet iemand uit te "
        "sluiten."
    ),
    "source_role": "redactie",
    "target_role": "academisch_criticus",
}


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{timestamp}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")
    return backup_path


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden in roles-tabel.")
    return row[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. deplatforming aanscherpen
    cur = conn.execute(
        "UPDATE mechanisms SET description = ?, effect = ? WHERE name = 'deplatforming'",
        (DEPLATFORMING_DESCRIPTION, DEPLATFORMING_EFFECT),
    )
    if cur.rowcount:
        print("Aangescherpt: deplatforming (cancelling + access-symbiose + zelf-rationalisatie)")
    else:
        print("Let op: mechanisme 'deplatforming' niet gevonden — niets aangepast.")

    # 2. toegangsdisciplinering toevoegen (idempotent)
    exists = conn.execute(
        "SELECT 1 FROM mechanisms WHERE name = ?", (NEW_MECHANISM["name"],)
    ).fetchone()
    if exists:
        print(f"Bestaat al: {NEW_MECHANISM['name']} — overgeslagen.")
    else:
        conn.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                NEW_MECHANISM["name"],
                NEW_MECHANISM["filter"],
                NEW_MECHANISM["mechanism_type"],
                NEW_MECHANISM["description"],
                NEW_MECHANISM["effect"],
                role_id(conn, NEW_MECHANISM["source_role"]),
                role_id(conn, NEW_MECHANISM["target_role"]),
            ),
        )
        print(
            f"Toegevoegd: {NEW_MECHANISM['name']} (sourcing) "
            f"{NEW_MECHANISM['source_role']} → {NEW_MECHANISM['target_role']}"
        )

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"Klaar. Totaal mechanismen: {total}")


if __name__ == "__main__":
    main()
