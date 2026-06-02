"""
Verrijking: de partij/het instituut als principaal achter de voorlichter (Luyendijk).

Probleem: de "voorlichter is van een partij OF een instituut"-dynamiek stond alleen in
de TEKST van `gecoordineerde_voorlichting`; structureel was de bronrol gewoon `politicus`.
Er was geen rol `partij` (de 6 partij-entiteiten hingen rolloos) en geen link van een
instituut naar de voorlichter. Deze migratie maakt de principaal-structuur echt:

  THEORIE
    1. Nieuwe rol `partij` (systeemactor) — de partij als coordinerende principaal.
    2. `gecoordineerde_voorlichting` wordt het PARTIJ-kanaal: bronrol politicus -> partij
       (0 instance-relaties, dus veilig te repointen).
    3. Nieuw `institutionele_voorlichting` (gezagsinstituut -> voorlichter) — het
       INSTITUUT-kanaal (RVD, departementale woordvoerders).
    4. Nieuw `partijlijn` (partij -> politicus) — de partij bepaalt de lijn die de
       politicus als 'bron' naar buiten brengt; geeft de partij-rol diepte.
  INSTANCES
    5. De partij-entiteiten (VVD, CDA, PVV, PvdA, SP, NSC) krijgen de rol `partij`.

Resultaat: de voorlichter heeft nu twee zichtbare principalen — `partij` en
`gezagsinstituut` — precies Luyendijks punt.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NEW_ROLE = {
    "name": "partij",
    "category": "systeemactor",
    "description": (
        "De politieke partij als coordinerende principaal achter haar politici en voorlichters. "
        "Bepaalt en bewaakt de lijn (fractiediscipline, woordvoerderschappen), levert kandidaten "
        "en stemt de naar buiten gebrachte boodschap af. Analytisch losgekoppeld van de "
        "individuele politicus (de publieke gedaante) en de voorlichter (de toegangs-poortwachter)."
    ),
}

MECHANISMS = [
    {
        "name": "gecoordineerde_voorlichting",
        "filter": "sourcing",
        "mechanism_type": "structureel",
        "description": (
            "De partij levert via haar voorlichter een afgestemde, voorverpakte boodschap langs "
            "de partijlijn. De voorlichter is de poortwachter: hij beheert de toegang tot de "
            "politici en deelt die uit als beloning of straf (vgl. 'toegangsdisciplinering'). "
            "Smeermiddel is de off-the-record-cultuur — de Nieuwspoort-code 'je hebt het niet "
            "van mij, maar...' (Luyendijk)."
        ),
        "effect": (
            "Partij, politicus en voorlichter zijn analytisch aparte rollen maar opereren als "
            "een bronmachine langs de partijlijn. In hun jacht op primeurs en toegang worden "
            "journalisten minder kritisch; de vage code wekt zelfcensuur (zie 'haagse_stam')."
        ),
        "source_role": "partij",
        "target_role": "voorlichter",
    },
    {
        "name": "institutionele_voorlichting",
        "filter": "sourcing",
        "mechanism_type": "structureel",
        "description": (
            "Een ministerie of instituut (Rijksvoorlichtingsdienst, departementale woordvoerders, "
            "persafdelingen van CBS/RIVM/politie) spreekt naar buiten via zijn voorlichter, die de "
            "institutionele lijn voorverpakt aanlevert en de toegang tot de organisatie beheert."
        ),
        "effect": (
            "De institutionele framing bereikt de journalist als kant-en-klare, 'gezaghebbende' "
            "bron; afwijkende vragen kosten toegang. De voorlichter is zo ook de poortwachter van "
            "het instituut, niet alleen van de partij (Luyendijk: van een partij of een instituut)."
        ),
        "source_role": "gezagsinstituut",
        "target_role": "voorlichter",
    },
    {
        "name": "partijlijn",
        "filter": "sourcing",
        "mechanism_type": "structureel",
        "description": (
            "De partij bepaalt en bewaakt de lijn die haar politici naar buiten brengen "
            "(fractiediscipline, woordvoerderschappen, verkiezingsprogramma). De politicus draagt "
            "die lijn uit als 'bron'."
        ),
        "effect": (
            "De individuele politicus spreekt zelden vrijuit maar langs de partijlijn; de partij "
            "is de eigenlijke coordinerende principaal achter de politieke bronstroom."
        ),
        "source_role": "partij",
        "target_role": "politicus",
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

    # 1. rol partij
    if conn.execute("SELECT 1 FROM roles WHERE name=?", (NEW_ROLE["name"],)).fetchone():
        conn.execute("UPDATE roles SET category=?, description=? WHERE name=?",
                     (NEW_ROLE["category"], NEW_ROLE["description"], NEW_ROLE["name"]))
        print("Rol bijgewerkt: partij")
    else:
        conn.execute("INSERT INTO roles (name, category, description) VALUES (?,?,?)",
                     (NEW_ROLE["name"], NEW_ROLE["category"], NEW_ROLE["description"]))
        print("Rol toegevoegd: partij (systeemactor)")

    # 2-4. mechanismen (repoint + nieuw)
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

    # 5. partij-entiteiten de rol partij geven
    pid = role_id(conn, "partij")
    parties = conn.execute("SELECT id, name FROM entities WHERE type='partij'").fetchall()
    for eid, name in parties:
        conn.execute("UPDATE entities SET primary_role_id=? WHERE id=?", (pid, eid))
        conn.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) VALUES (?,?,?)",
                     (eid, pid, "primaire functie: politieke partij"))
        print(f"  rol toegekend: {name} -> partij")

    conn.commit()
    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    rollen = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    mech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    rolloos = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE type='partij' AND primary_role_id IS NULL").fetchone()[0]
    conn.close()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")
    print(f"\nKlaar. Rollen: {rollen} | mechanismen: {mech} | rolloze partij-entiteiten: {rolloos}")


if __name__ == "__main__":
    main()
