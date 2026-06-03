"""
Modelreview — tegenmacht herbedraden: toezichthouder naar de concentratie-schakel +
borgingsstichting volledig maken.

Onderzoek (zie sessie): twee bevindingen.

1. TOEZICHTHOUDER wees naar `mediaeigenaar`, maar beide mechanismen gaan blijkens hun
   eigen definitie over MEDIACONCENTRATIE (ACM blokkeert/conditioneert overnames, bv.
   DPG-RTL). Dat bijt op de overname-/holdingschakel, niet op de eigenaar-als-persoon.
   Sinds de eigendomsketen-herbedrading zit concentratie hoog op de controle-as en doet
   de holding de overname. Daarom:
      toezichthouder_interventie : mediaeigenaar -> overnamevehikel
      toezicht_tandeloosheid     : mediaeigenaar -> overnamevehikel

2. BORGINGSSTICHTING raakte alleen de `hoofdredacteur`, terwijl haar roldefinitie
   "redactionele onafhankelijkheid EN continuiteit van titels" belooft en de eigenaar via
   TWEE hefbomen aanvalt (benoemingspolitiek -> hoofdredacteur EN
   redactioneel_budgetcontrole -> redactie). De tegenpool dekt nu ook de redactie:
      NEW redactiestatuut_borging : borgingsstichting -> redactie

(Optioneel, NIET in dit script: continuiteitsborging -> mediaorganisatie; en de causale
 lijn toezichthouder -> borgingsstichting. Wachten op akkoord.)

Geen schemawijziging. Idempotent. Backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# 1. toezichthouder-mechanismen herbedraden naar de concentratie-/overnameschakel
RETARGET = [
    {
        "name": "toezichthouder_interventie",
        "target_role": "overnamevehikel",
        "description": (
            "De toezichthouder (m.n. ACM) grijpt in op mediaconcentratie door overnames te "
            "blokkeren of te conditioneren op het holding-/overnamevehikelniveau (bv. de "
            "DPG-RTL-voorwaarden: verplichte onafhankelijke stichtingen met vetorecht over de "
            "hoofdredacteur)."
        ),
        "effect": "Concentratie wordt afgeremd of van waarborgen voorzien; de interventie kan zelfs een borgingsstichting afdwingen.",
    },
    {
        "name": "toezicht_tandeloosheid",
        "target_role": "overnamevehikel",
        "description": (
            "Toezichthouders (ACM, CvdM, RvJ) signaleren concentratie- en "
            "onafhankelijkheidsproblemen maar kunnen vaak niet effectief ingrijpen op het "
            "overname-/holdingniveau; de RvJ kan geen sancties opleggen en redactiestatuten "
            "bieden geen ijzerharde garanties."
        ),
        "effect": "Formele beschermingsmechanismen zijn onvoldoende robuust; de ACM DPG/RTL-voorwaarden zijn de uitzondering die de regel bevestigt.",
    },
]

# 2. nieuw tegenmacht-mechanisme: de borgingsstichting beschermt ook de hele redactie
NEW_MECHANISMS = [
    {
        "name": "redactiestatuut_borging",
        "filter": "tegenmacht",
        "mechanism_type": "juridisch",
        "description": (
            "De borgingsstichting verankert via het redactiestatuut (en haar prioriteitsaandeel/"
            "vetorecht) de onafhankelijkheid en bestaanszekerheid van de héle redactie — niet "
            "alleen de hoofdredacteur. Daarmee zet ze een rem op de eigenaarshefboom "
            "`redactioneel_budgetcontrole`: bezuinigingen en commerciële sturing van de redactie "
            "worden begrensd."
        ),
        "effect": (
            "Structurele bescherming van de redactionele autonomie en een minimum aan middelen; "
            "geen ijzeren garantie (een statuut is geen harde juridische muur en de stichting is "
            "een minderheid)."
        ),
        "source_role": "borgingsstichting",
        "target_role": "redactie",
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

    print("\n-- 1. toezichthouder herbedraden naar overnamevehikel --")
    for m in RETARGET:
        cur = conn.execute(
            "UPDATE mechanisms SET target_role_id=?, description=?, effect=? WHERE name=?",
            (role_id(conn, m["target_role"]), m["description"], m["effect"], m["name"]),
        )
        print(f"  {'herbedraad' if cur.rowcount else 'NIET gevonden'}: {m['name']} → {m['target_role']}")

    print("\n-- 2. nieuw mechanisme: borgingsstichting → redactie --")
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

    print("\n== verificatie: tegenmacht rond eigenaar/redactie ==")
    for r in conn.execute(
        """SELECT m.name, sr.name, tr.name FROM mechanisms m
           LEFT JOIN roles sr ON sr.id=m.source_role_id LEFT JOIN roles tr ON tr.id=m.target_role_id
           WHERE m.name IN ('toezichthouder_interventie','toezicht_tandeloosheid',
                            'onafhankelijkheidsborging','redactiestatuut_borging')
           ORDER BY m.name"""
    ).fetchall():
        print(f"  {r[1]} → {r[2]:<16} {r[0]}")

    print("\n== check: wijst nog iets vanuit toezichthouder naar mediaeigenaar? (verwacht: leeg) ==")
    rows = conn.execute(
        """SELECT m.name FROM mechanisms m JOIN roles sr ON sr.id=m.source_role_id
           JOIN roles tr ON tr.id=m.target_role_id
           WHERE sr.name='toezichthouder' AND tr.name='mediaeigenaar'"""
    ).fetchall()
    print("  " + ("LEEG ✓" if not rows else ", ".join(r[0] for r in rows)))

    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
