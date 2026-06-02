"""
Verrijking: de draaideur als hub-familie (cross_filter), politicus als spil.

Probleem: de theorie dekte de draaideur met maar twee kruisingen (politicus->columnist,
journalist->politicus), terwijl de instances al laten zien dat het zwaartepunt elders ligt:
politiek <-> bedrijfsleven (KLM, KPMG, EY, Uber, Microsoft) en politiek <-> lobby
(Hill+Knowlton), plus media en instituties. Die domeinen ontbraken als mechanisme.

Deze migratie voegt vier domein-specifieke draaideur-mechanismen toe (elk een andere
bestemming, dus geen overlap met elkaar). De bestaande `draaideurconstructie` (werkpaard,
18 instances) en `draaideur_journalistiek_politiek` blijven staan.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECHANISMS = [
    {
        "name": "draaideur_politiek_bedrijfsleven",
        "filter": "cross_filter",
        "mechanism_type": "structureel",
        "description": (
            "Een bewindspersoon of Kamerlid wordt na zijn ambt CEO, commissaris of adviseur bij "
            "een bedrijf, sector of branche die hij eerder reguleerde (bv. Eurlings->KLM, "
            "Bos->KPMG, Kroes->Uber, Balkenende->EY, Schaart->Microsoft)."
        ),
        "effect": (
            "Kennis, netwerk en toegang uit het publieke ambt worden te gelde gemaakt voor een "
            "private belanghebbende; regelgeving en publiek debat worden vooraf al meegedacht in "
            "het belang van de toekomstige werkgever."
        ),
        "source_role": "politicus",
        "target_role": "belanghebbende",
    },
    {
        "name": "draaideur_politiek_lobby",
        "filter": "cross_filter",
        "mechanism_type": "structureel",
        "description": (
            "Een bewindspersoon of Kamerlid stapt over naar de lobby/public affairs en zet zijn "
            "toegang tot oud-collega's om in invloed (bv. Jack de Vries->Hill+Knowlton)."
        ),
        "effect": (
            "De grens tussen wetgever en belangenbehartiger vervaagt; lobbyisten met een "
            "politiek verleden krijgen bevoorrechte toegang tot de besluitvorming."
        ),
        "source_role": "politicus",
        "target_role": "lobbyist",
    },
    {
        "name": "draaideur_politiek_institutie",
        "filter": "cross_filter",
        "mechanism_type": "structureel",
        "description": (
            "Een bewindspersoon wordt bestuurder/toezichthouder van een (semi-)publiek instituut "
            "of ZBO — of omgekeerd komt een institutiebestuurder uit de gereguleerde sector. "
            "Benoemingen lopen langs partijlijnen."
        ),
        "effect": (
            "De personele kring die reguleert en die gereguleerd/uitvoert overlapt; institutioneel "
            "gezag en politieke loyaliteit raken verweven, wat onafhankelijk toezicht verzwakt."
        ),
        "source_role": "politicus",
        "target_role": "gezagsinstituut",
    },
    {
        "name": "draaideur_politiek_media",
        "filter": "cross_filter",
        "mechanism_type": "structureel",
        "description": (
            "Een (oud-)politicus of partijgebonden figuur wordt hoofdredacteur, commentator of "
            "presentator — of omgekeerd. De door de eigenaar benoemde, soms openlijk partijgebonden "
            "hoofdredacteur verenigt het eigendoms- en het ideologiefilter in een persoon."
        ),
        "effect": (
            "De redactionele eindverantwoordelijkheid ligt bij iemand met expliciete politieke "
            "binding; de scheiding tussen politiek bedrijf en redactie wordt personeel doorbroken."
        ),
        "source_role": "politicus",
        "target_role": "hoofdredacteur",
    },
]


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

    for m in MECHANISMS:
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

    conn.commit()
    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    draai = conn.execute("SELECT COUNT(*) FROM mechanisms WHERE name LIKE 'draaideur%'").fetchone()[0]
    mech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")
    print(f"\nKlaar. Draaideur-mechanismen: {draai} | totaal mechanismen: {mech}")


if __name__ == "__main__":
    main()
