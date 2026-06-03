"""
Modelreview — laatste eigenaar-shortcut weg: redactionele hefbomen naar het org-niveau.

De eigenaar raakte de redactionele laag nog direct via twee mechanismen die over de
zojuist rechtgetrokken eigendomsketen heen sprongen. In werkelijkheid benoemt niet de
UBO/familie persoonlijk de hoofdredacteur, en stelt niet de UBO persoonlijk het
redactiebudget vast — dat doet de directie/uitgever van het mediabedrijf zelf, binnen
het kader dat de eigenaar via de keten (STAK -> holding) heeft bepaald.

Daarom worden beide her-bronnd van `mediaeigenaar` naar `mediaorganisatie`:
   - benoemingspolitiek         : mediaeigenaar -> hoofdredacteur  =>  mediaorganisatie -> hoofdredacteur
   - redactioneel_budgetcontrole: mediaeigenaar -> redactie        =>  mediaorganisatie -> redactie

Daarna raakt `mediaeigenaar` de redactionele laag nooit meer direct: zijn invloed loopt
volledig via de keten mediaeigenaar -> administratiekantoor -> overnamevehikel ->
mediaorganisatie -> {hoofdredacteur, redactie} -> journalist. Alleen het persoonlijke
elite-netwerk (`mediaeigenaar_elite_netwerk`, F5) blijft rechtstreeks vanaf de eigenaar.

Geen schemawijziging. Idempotent. Backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECHANISMS = [
    {
        "name": "benoemingspolitiek",
        "source_role": "mediaorganisatie",
        "description": (
            "De directie/uitgever van de mediaorganisatie benoemt de hoofdredacteur — binnen het "
            "kader dat de eigenaar via de eigendomsketen (STAK → holding) heeft bepaald. De "
            "eigenaar raakt de redactie dus niet direct; de benoeming gebeurt op org-niveau, "
            "doorgaans met advies/instemming van de redactie (redactiestatuut)."
        ),
        "effect": (
            "De redactionele lijn weerspiegelt de via eigendom ingebedde voorkeuren, zónder "
            "expliciete instructie van de uiteindelijke eigenaar."
        ),
    },
    {
        "name": "redactioneel_budgetcontrole",
        "source_role": "mediaorganisatie",
        "description": (
            "De mediaorganisatie (directie) stelt het redactiebudget vast en beslist over "
            "bezuinigingen — binnen het rendementsregime dat de holding oplegt (`winstmaximalisatie`). "
            "Ook deze hefboom zit op org-niveau, niet bij de uiteindelijke eigenaar."
        ),
        "effect": "Minder middelen voor diepgravende, kritische journalistiek; krimp van de redactie.",
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

    print("\n-- redactionele hefbomen her-bronnen naar mediaorganisatie --")
    for m in MECHANISMS:
        sets, vals = [], []
        if "source_role" in m:
            sets.append("source_role_id = ?"); vals.append(role_id(conn, m["source_role"]))
        for f in ("description", "effect"):
            if f in m:
                sets.append(f"{f} = ?"); vals.append(m[f])
        vals.append(m["name"])
        cur = conn.execute(f"UPDATE mechanisms SET {', '.join(sets)} WHERE name = ?", vals)
        print(f"  {'her-bronnd' if cur.rowcount else 'NIET gevonden'}: {m['name']} → mediaorganisatie")

    conn.commit()

    print("\n== verificatie: uitgaande pijlen van mediaeigenaar (verwacht: administratiekantoor + elite_forum) ==")
    for r in conn.execute(
        """SELECT m.name, tr.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id
           JOIN roles tr ON tr.id=m.target_role_id
           WHERE sr.name='mediaeigenaar' ORDER BY tr.name, m.name"""
    ).fetchall():
        print(f"  mediaeigenaar → {r[1]:<20} ({r[0]})")

    print("\n== org-niveau redactionele hefbomen ==")
    for r in conn.execute(
        """SELECT m.name, sr.name, tr.name FROM mechanisms m
           LEFT JOIN roles sr ON sr.id=m.source_role_id LEFT JOIN roles tr ON tr.id=m.target_role_id
           WHERE m.name IN ('benoemingspolitiek','redactioneel_budgetcontrole','hoofdredacteur_als_filter','onafhankelijkheidsborging')
           ORDER BY m.name"""
    ).fetchall():
        print(f"  {r[1]} → {r[2]:<16} {r[0]}")

    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
