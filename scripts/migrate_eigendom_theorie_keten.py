"""
Modelreview — theorie-laag: eigendomsketen enkelvoudig maken (geen directe shortcut).

Reality-grounded besluit (Optie 2): de tussenconstructies (administratiekantoor/STAK,
overnamevehikel) BLIJVEN, want elk draagt een eigen, echt effect (STAK = controle
concentreren/verankeren/verbergen; holding = rendementsregime opleggen). Dat maakt het
model realistischer, niet nodeloos complex. Maar dan moet — zoals al bij de instanties —
de DIRECTE pijl `mediaeigenaar -> mediaorganisatie` weg, want de invloed loopt via de keten.

De keten blijft:
   mediaeigenaar --familiezeggenschap--> administratiekantoor
   administratiekantoor --certificaatconstructie--> overnamevehikel
   overnamevehikel --holdingconstructie--> mediaorganisatie

Vier mechanismen schoten een directe `mediaeigenaar -> mediaorganisatie`-pijl. Die worden
herbedraad naar hun echte schakel (geen verwijdering, alleen verplaatsing):
   - winstmaximalisatie   : -> overnamevehikel -> mediaorganisatie  (proximate rendementsdruk)
   - acquisitiestrategie  : -> mediaeigenaar  -> overnamevehikel     (ketenvorming via M&A)
   - cross_media_eigendom : -> mediaeigenaar  -> overnamevehikel     (breedte over media/holdings)
   - eigendomsconcentratie: -> cross_filter / structureel, mediaeigenaar -> overnamevehikel
        (emergent macro-kenmerk — duopolie — geen gerichte schakel; bij emergente_bias-soort)

NB tegenmacht: `onafhankelijkheidsborging` (borgingsstichting -> mediaorganisatie) blijft
ongemoeid — dat is een tegenkracht-filter, geen eigendomsschakel.

Geen schemawijziging. Idempotent. Backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# Per mechanisme alleen de te wijzigen velden.
REWIRE = [
    {
        "name": "winstmaximalisatie",
        "source_role": "overnamevehikel",
        "target_role": "mediaorganisatie",
        "description": (
            "Het overnamevehikel/de holding legt een rendementsregime op aan de mediaorganisatie: "
            "marges, kostenbesparing en synergie staan voorop. De eigenaarsdruk bereikt de titel "
            "dus via de proximate holding, niet als directe greep van de uiteindelijke eigenaar."
        ),
        "effect": "Bezuiniging op redacties; minder ruimte voor dure, diepgravende journalistiek.",
    },
    {
        "name": "acquisitiestrategie",
        "source_role": "mediaeigenaar",
        "target_role": "overnamevehikel",
        "description": (
            "De eigenaar laat de conglomeraatketen groeien door via overnamevehikels titels en "
            "holdings op te kopen. Beschrijft hoe de keten ontstaat — een relatie tussen eigenaar "
            "en vehikel, niet een directe greep op een afzonderlijke titel."
        ),
        "effect": "Toenemende concentratie; nieuwe titels komen onder hetzelfde rendements- en koersregime.",
    },
    {
        "name": "cross_media_eigendom",
        "source_role": "mediaeigenaar",
        "target_role": "overnamevehikel",
        "description": (
            "De eigenaar houdt via zijn vehikels belangen in meerdere mediatypen tegelijk (krant, "
            "online, radio/tv). Een eigenaar-niveau-kenmerk over de holdings heen, geen losse pijl "
            "naar één mediaorganisatie."
        ),
        "effect": "Eén eigenaarsperspectief kleurt meerdere kanalen; verschraling van pluriformiteit over mediatypen.",
    },
    {
        "name": "eigendomsconcentratie",
        "filter": "cross_filter",
        "mechanism_type": "structureel",
        "source_role": "mediaeigenaar",
        "target_role": "overnamevehikel",
        "description": (
            "Structureel macro-kenmerk: twee conglomeraten controleren via hun holdings >90% van "
            "de commerciële nieuwsmarkt. Een emergente eigenschap van de eigendomsstructuur, geen "
            "gerichte controleschakel — vandaar structureel/cross-filter, naast emergente_bias en "
            "systemische_homeostase."
        ),
        "effect": "Drastische beperking van pluriformiteit op eigenaarsniveau; structurele pro-elite-grondtoon van het hele veld.",
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

    print("\n-- eigendom-mechanismen herbedraden --")
    for m in REWIRE:
        sets, vals = [], []
        if "source_role" in m:
            sets.append("source_role_id = ?"); vals.append(role_id(conn, m["source_role"]))
        if "target_role" in m:
            sets.append("target_role_id = ?"); vals.append(role_id(conn, m["target_role"]))
        for f in ("filter", "mechanism_type", "description", "effect"):
            if f in m:
                sets.append(f"{f} = ?"); vals.append(m[f])
        vals.append(m["name"])
        cur = conn.execute(f"UPDATE mechanisms SET {', '.join(sets)} WHERE name = ?", vals)
        arrow = f"{m.get('source_role','?')} → {m.get('target_role','?')}"
        print(f"  {'herbedraad' if cur.rowcount else 'NIET gevonden'}: {m['name']}  ({arrow}{', '+m['filter'] if 'filter' in m else ''})")

    conn.commit()

    print("\n== verificatie: resterende mediaeigenaar → mediaorganisatie (verwacht: leeg) ==")
    rows = conn.execute(
        """SELECT m.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id
           JOIN roles tr ON tr.id=m.target_role_id
           WHERE sr.name='mediaeigenaar' AND tr.name='mediaorganisatie'"""
    ).fetchall()
    print("  " + ("LEEG ✓" if not rows else ", ".join(r[0] for r in rows)))

    print("\n== nieuwe eigendomsketen (rol → rol) ==")
    for r in conn.execute(
        """SELECT m.name, sr.name, tr.name FROM mechanisms m
           LEFT JOIN roles sr ON sr.id=m.source_role_id
           LEFT JOIN roles tr ON tr.id=m.target_role_id
           WHERE m.name IN ('familiezeggenschap','certificaatconstructie','holdingconstructie',
                            'winstmaximalisatie','acquisitiestrategie','cross_media_eigendom','eigendomsconcentratie')
           ORDER BY m.name"""
    ).fetchall():
        print(f"  {r[0]:<24} {r[1]} → {r[2]}")

    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
