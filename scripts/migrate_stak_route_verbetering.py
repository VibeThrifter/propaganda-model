"""
Modelreview — STAK-route afmaken + de STAK-constructie aanscherpen.

(1) STRIKT ÉÉN PAD. De eigenaar-niveau-mechanismen liepen `mediaeigenaar -> overnamevehikel`
    en sprongen zo over de STAK heen. Ze worden achter de STAK geleid, zodat `mediaeigenaar`
    nog precies één uitgaande pijl heeft (naar het administratiekantoor) en de hele
    eigenaarsinvloed via de controlestructuur loopt:
        mediaeigenaar -> administratiekantoor -> overnamevehikel -> mediaorganisatie
    Herbedraad (target overnamevehikel -> administratiekantoor):
        acquisitiestrategie, cross_media_eigendom, eigendomsconcentratie

(2) STAK BETER. `familiezeggenschap` (mediaeigenaar -> administratiekantoor) en
    `certificaatconstructie` (administratiekantoor -> overnamevehikel) + de rol
    `administratiekantoor` worden aangescherpt zodat de VIER echte effecten van een
    Stichting Administratiekantoor expliciet zijn:
        1. stemmacht geconcentreerd bij het stichtingsbestuur
        2. cash- en controlerechten ontkoppeld (certificaat = dividend, geen stem)
        3. keten overnamebestendig (controle niet te koop)
        4. uiteindelijke eigenaar afgeschermd (geen UBO-transparantie)

Geen schemawijziging. Idempotent. Backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# (1) achter de STAK leiden + (2) aanscherpen — per mechanisme alleen de te wijzigen velden
MECHANISMS = [
    {
        "name": "acquisitiestrategie",
        "target_role": "administratiekantoor",
        "description": (
            "De groei-/overnamestrategie van de eigenaar, uitgeoefend via de controlestructuur "
            "(STAK): met zijn verankerde zeggenschap laat de eigenaar de gecertificeerde holding "
            "nieuwe titels en holdings opkopen. De acquisitie wordt benedenstrooms uitgevoerd, "
            "maar de sturing zit bij de eigenaar — vandaar op de eerste schakel."
        ),
        "effect": "Toenemende concentratie; nieuwe titels komen onder hetzelfde gecertificeerde controle- en rendementsregime.",
    },
    {
        "name": "cross_media_eigendom",
        "target_role": "administratiekantoor",
        "description": (
            "Het via de controlestructuur gehouden imperium spant meerdere mediatypen tegelijk "
            "(krant, online, radio/tv). Een eigenaar-niveau-kenmerk, geen losse greep op één titel."
        ),
        "effect": "Eén eigenaarsperspectief kleurt meerdere kanalen; verschraling van pluriformiteit over mediatypen.",
    },
    {
        "name": "eigendomsconcentratie",
        "target_role": "administratiekantoor",
        "description": (
            "Structureel macro-kenmerk: twee families/conglomeraten controleren — via hun "
            "gecertificeerde holdings — >90% van de commerciële nieuwsmarkt. Een emergente "
            "eigenschap van de eigendomsstructuur (cross-filter/structureel), geen gerichte "
            "schakel; geplaatst aan de top van de controle-as."
        ),
        "effect": "Drastische beperking van pluriformiteit op eigenaarsniveau; structurele pro-elite-grondtoon van het hele veld.",
    },
    {
        "name": "familiezeggenschap",
        "description": (
            "De familie/UBO richt het administratiekantoor (STAK) op en benoemt het "
            "stichtingsbestuur. Daarmee verankert een kleine groep de permanente zeggenschap over "
            "de hele keten, ontkoppeld van het economische belang dat via certificaten wordt "
            "uitgekeerd."
        ),
        "effect": (
            "Controle blijft bij enkele personen, ongeacht verwatering van het kapitaal of "
            "bestuurswisselingen; externe kapitaalverschaffers krijgen wel dividend maar geen stem."
        ),
    },
    {
        "name": "certificaatconstructie",
        "description": (
            "Het administratiekantoor houdt de stemrechtdragende aandelen van de holding "
            "(overnamevehikel) en geeft daartegenover certificaten uit aan de economische "
            "eigenaren. Zo splitst de STAK economisch belang (certificaat = dividend) af van "
            "zeggenschap (stem = bij het stichtingsbestuur)."
        ),
        "effect": (
            "Vier effecten tegelijk: (1) stemmacht geconcentreerd bij het stichtingsbestuur, "
            "(2) cash- en controlerechten ontkoppeld, (3) de keten overnamebestendig (controle is "
            "niet te koop), en (4) de uiteindelijke eigenaar afgeschermd (geen UBO-transparantie). "
            "Eigenaarsinvloed is dus niet 'distaal = zwak' — de STAK is een controle-versterker "
            "hoog in de keten."
        ),
    },
]

UPDATE_ROLES = [
    {
        "name": "administratiekantoor",
        "description": (
            "Stichting Administratiekantoor (STAK): juridisch controlevehikel dat de "
            "stemrechtdragende aandelen van een holding houdt en daartegenover dividendgerechtigde "
            "certificaten uitgeeft. Splitst zeggenschap af van economisch belang, concentreert de "
            "controle bij de familie/UBO, maakt de keten overnamebestendig en houdt de "
            "uiteindelijke eigenaren buiten beeld."
        ),
        "examples": "Stichting Administratiekantoor Epifin (controle Van Thillo over DPG Media)",
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

    print("\n-- mechanismen herbedraden/aanscherpen --")
    for m in MECHANISMS:
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
        print(f"  {'bijgewerkt' if cur.rowcount else 'NIET gevonden'}: {m['name']}")

    print("\n-- rol aanscherpen --")
    for r in UPDATE_ROLES:
        cur = conn.execute(
            "UPDATE roles SET description = ?, examples = ? WHERE name = ?",
            (r["description"], r["examples"], r["name"]),
        )
        print(f"  {'bijgewerkt' if cur.rowcount else 'NIET gevonden'}: rol {r['name']}")

    conn.commit()

    print("\n== verificatie: uitgaande pijlen van mediaeigenaar (verwacht: alleen administratiekantoor) ==")
    for r in conn.execute(
        """SELECT DISTINCT tr.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id
           JOIN roles tr ON tr.id=m.target_role_id
           WHERE sr.name='mediaeigenaar' ORDER BY tr.name"""
    ).fetchall():
        print(f"  mediaeigenaar → {r[0]}")

    print("\n== STAK-keten (rol → rol) ==")
    for r in conn.execute(
        """SELECT m.name, sr.name, tr.name, m.filter FROM mechanisms m
           LEFT JOIN roles sr ON sr.id=m.source_role_id
           LEFT JOIN roles tr ON tr.id=m.target_role_id
           WHERE m.name IN ('familiezeggenschap','acquisitiestrategie','cross_media_eigendom',
                            'eigendomsconcentratie','certificaatconstructie','holdingconstructie','winstmaximalisatie')
           ORDER BY sr.name, m.name"""
    ).fetchall():
        print(f"  {r[1]} → {r[2]:<20} [{r[3]}]  {r[0]}")

    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
