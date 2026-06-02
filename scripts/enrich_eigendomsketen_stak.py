"""
Verrijking: de eigendomsketen rechtgetrokken en de stichtingen zichtbaar gemaakt.

Aanleiding: de eigendomslaag stond 'raar'. mediaeigenaar wees rechtstreeks naar de
mediaorganisatie, `overnamevehikel` had 0 entiteiten (Epifin c.s. stonden als
`aandeelhouder`), en er was geen stichting-knoop te zien — terwijl de Nederlandse
mediastructuur juist via stichtingen loopt:

  - STAK (Stichting Administratiekantoor): CONTROLE-/ondoorzichtigheidsvehikel. Boven
    Epifin/DPG zit een STAK die de aandelen certificeert; zeggenschap wordt losgekoppeld
    van economisch belang en de UBO blijft buiten beeld.  -> rol `administratiekantoor`
  - Onafhankelijkheidsstichting met prioriteitsaandeel: TEGENKRACHT. Stichting Democratie
    en Media (opvolger Stichting Het Parool, 1944) houdt 14,27% + een prioriteitsaandeel
    in DPG.  -> bestaande rol `borgingsstichting`

Deze migratie:
  SCHEMA
    1. Voegt entity-type 'stichting' toe aan de CHECK-constraint van entities
       (table-recreate; entities kent NOS/STAK/SDM-achtigen nu niet als type).
  THEORIE
    2. Nieuwe rol `administratiekantoor` (eigendom) — de STAK-knoop.
    3. Ladder-mechanismen: `familiezeggenschap` (mediaeigenaar -> administratiekantoor)
       en `certificaatconstructie` (administratiekantoor -> overnamevehikel).
    4. Scherpt `holdingconstructie` aan (STAK eruit, want nu eigen knoop) en de
       roldefinities van mediaeigenaar/overnamevehikel.
  INSTANCES
    5. Herrolt Epifin, VP Exploitatie, Concentra, Mediahuis Partners -> overnamevehikel.
    6. Maakt de STAK boven Epifin aan en bedraadt de keten als trap:
       Van Thillo -> STAK -> Epifin -> DPG (de directe Van Thillo->Epifin-sluiproute
       wordt omgebogen naar de STAK).
    7. Maakt Stichting Democratie en Media aan (borgingsstichting) met de
       14,27%+prioriteitsaandeel-relatie naar DPG.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# --- referentiegegevens ---------------------------------------------------

NEW_ROLE = {
    "name": "administratiekantoor",
    "category": "eigendom",
    "description": (
        "Stichting Administratiekantoor (STAK): juridisch vehikel dat de aandelen van een "
        "holding certificeert. Koppelt zeggenschap los van economisch belang, concentreert "
        "de controle bij de familie/UBO en houdt de uiteindelijke eigenaren buiten beeld."
    ),
}

# Aangescherpte roldefinities (UBO vs. holding scherper neerzetten)
ROLE_UPDATES = {
    "mediaeigenaar": (
        "De uiteindelijke eigenaar/UBO (vaak een familie) die via een keten van vehikels "
        "eigendom over mediaorganisaties uitoefent en daarmee de redactionele lijn kan beinvloeden."
    ),
    "overnamevehikel": (
        "Holding of investeringsvehikel (bv. Epifin, Mediahuis Partners, VP Exploitatie) "
        "tussen de uiteindelijke eigenaar en de mediaorganisatie, waarmee families eigendom "
        "uitoefenen op afstand van de redactie."
    ),
}

# Nieuwe ladder-mechanismen (filter eigendom)
NEW_MECHANISMS = [
    {
        "name": "familiezeggenschap",
        "filter": "eigendom",
        "mechanism_type": "structureel",
        "description": (
            "De familie/UBO bestuurt het administratiekantoor (STAK) en behoudt zo de "
            "zeggenschap over de hele eigendomsketen, los van het uitgekeerde economische belang."
        ),
        "effect": (
            "Controle blijft geconcentreerd bij enkele personen, ongeacht latere verwatering "
            "van het kapitaal; externe kapitaalverschaffers en bestuurswisselingen raken de "
            "redactionele zeggenschap niet."
        ),
        "source_role": "mediaeigenaar",
        "target_role": "administratiekantoor",
    },
    {
        "name": "certificaatconstructie",
        "filter": "eigendom",
        "mechanism_type": "juridisch",
        "description": (
            "De STAK certificeert de aandelen van het overnamevehikel/holding: de economische "
            "rechten (certificaten) worden gescheiden van het stemrecht, dat bij het "
            "stichtingsbestuur blijft."
        ),
        "effect": (
            "De uiteindelijke eigenaren blijven buiten beeld (geen UBO-transparantie) en "
            "zeggenschap is niet overdraagbaar met het economische belang; de keten wordt "
            "ondoorzichtig en overnamebestendig."
        ),
        "source_role": "administratiekantoor",
        "target_role": "overnamevehikel",
    },
]

# Aangescherpt bestaand mechanisme
HOLDING_DESC = (
    "Eigendom wordt uitgeoefend via gestapelde investeringsvehikels/holdings (bv. Epifin, "
    "Mediahuis Partners) tussen de uiteindelijke eigenaar en de mediaorganisatie — op afstand "
    "van de redactie. De certificering daarboven gebeurt door de STAK (zie 'certificaatconstructie')."
)
HOLDING_EFFECT = (
    "Eigendom op afstand: de eigenaar is juridisch ver verwijderd van de redactie, wat "
    "verantwoording vertroebelt en invloed informeel maakt."
)

# Entiteiten die feitelijk overnamevehikel zijn maar als aandeelhouder stonden
VEHIKEL_NAMES = ["Epifin", "VP Exploitatie", "Concentra", "Mediahuis Partners"]

STAK_ENTITY = {
    "name": "Stichting Administratiekantoor Epifin",
    "type": "stichting",
    "role": "administratiekantoor",
    "description": (
        "STAK boven Epifin/DPG: certificeert de aandelen, koppelt zeggenschap los van "
        "economisch belang en houdt de uiteindelijke eigenaren (familie Van Thillo) buiten beeld."
    ),
}

SDM_ENTITY = {
    "name": "Stichting Democratie en Media",
    "type": "stichting",
    "role": "borgingsstichting",
    "description": (
        "Onafhankelijkheidsstichting (opvolger van Stichting Het Parool, 1944). Houdt 14,27% "
        "plus een prioriteitsaandeel in DPG en bewaakt de onafhankelijkheid/continuiteit van "
        "o.a. Trouw en de Volkskrant. Structurele rem op eigenaarsinvloed, geen ijzeren garantie."
    ),
}

UNSOURCED_CERTAINTY = 0.05  # conventie: onbronde relaties krijgen certainty 0.05


# --- helpers --------------------------------------------------------------

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


def mechanism_id(conn, name):
    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
    return row[0] if row else None


def entity_id(conn, name):
    row = conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()
    return row[0] if row else None


# --- 1. schema: type 'stichting' toevoegen --------------------------------

def add_stichting_type(conn):
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='entities'"
    ).fetchone()[0]
    if "'stichting'" in sql:
        print("Schema: type 'stichting' bestaat al — overgeslagen.")
        return

    new_sql = sql.replace("CHECK(type IN (", "CHECK(type IN (\n        'stichting',", 1)
    new_sql = new_sql.replace("CREATE TABLE entities", "CREATE TABLE entities_new", 1)

    # indexen (excl. autoindex met sql IS NULL) bewaren om opnieuw aan te maken
    index_sqls = [
        r[0] for r in conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='entities' AND sql IS NOT NULL"
        ).fetchall()
    ]

    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("BEGIN")
    conn.execute(new_sql)
    conn.execute("INSERT INTO entities_new SELECT * FROM entities")
    conn.execute("DROP TABLE entities")
    conn.execute("ALTER TABLE entities_new RENAME TO entities")
    for isql in index_sqls:
        conn.execute(isql)
    conn.execute("COMMIT")
    conn.execute("PRAGMA foreign_keys=ON")

    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt na schema-migratie: {bad}")
    print("Schema: type 'stichting' toegevoegd (table-recreate, FK-check OK).")


# --- 2/3/4. theorie -------------------------------------------------------

def upsert_role(conn, r):
    if conn.execute("SELECT 1 FROM roles WHERE name=?", (r["name"],)).fetchone():
        conn.execute("UPDATE roles SET category=?, description=? WHERE name=?",
                     (r["category"], r["description"], r["name"]))
        print(f"Rol bijgewerkt: {r['name']}")
    else:
        conn.execute("INSERT INTO roles (name, category, description) VALUES (?,?,?)",
                     (r["name"], r["category"], r["description"]))
        print(f"Rol toegevoegd: {r['name']} ({r['category']})")


def upsert_mechanism(conn, m):
    sid = role_id(conn, m["source_role"])
    tid = role_id(conn, m["target_role"])
    if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone():
        conn.execute(
            """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
               source_role_id=?, target_role_id=? WHERE name=?""",
            (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]))
        print(f"Mechanisme bijgewerkt: {m['name']}")
    else:
        conn.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
               VALUES (?,?,?,?,?,?,?)""",
            (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid))
        print(f"Mechanisme toegevoegd: {m['name']} ({m['source_role']} -> {m['target_role']})")


# --- 5/6/7. instances -----------------------------------------------------

def get_or_create_entity(conn, e):
    eid = entity_id(conn, e["name"])
    rid = role_id(conn, e["role"])
    if eid:
        conn.execute("UPDATE entities SET type=?, primary_role_id=?, description=? WHERE id=?",
                     (e["type"], rid, e["description"], eid))
        print(f"Entiteit bijgewerkt: {e['name']}")
    else:
        conn.execute(
            "INSERT INTO entities (name, type, primary_role_id, description, active) VALUES (?,?,?,?,1)",
            (e["name"], e["type"], rid, e["description"]))
        eid = entity_id(conn, e["name"])
        print(f"Entiteit aangemaakt: {e['name']} ({e['type']}, rol {e['role']})")
    conn.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) VALUES (?,?,?)",
                 (eid, rid, "primaire functie"))
    return eid


def ensure_relation(conn, src, tgt, rtype, mech_name, desc, influence):
    if conn.execute("SELECT 1 FROM relations WHERE source_id=? AND target_id=?",
                    (src, tgt)).fetchone():
        return False
    conn.execute(
        """INSERT INTO relations
           (source_id, target_id, relation_type, mechanism_id, description, certainty, influence, bidirectional, active)
           VALUES (?,?,?,?,?,?,?,0,1)""",
        (src, tgt, rtype, mechanism_id(conn, mech_name), desc, UNSOURCED_CERTAINTY, influence))
    return True


def reroll_vehikels(conn):
    ov = role_id(conn, "overnamevehikel")
    ah = role_id(conn, "aandeelhouder")
    for name in VEHIKEL_NAMES:
        eid = entity_id(conn, name)
        if not eid:
            print(f"  let op: '{name}' niet gevonden — overgeslagen.")
            continue
        conn.execute("UPDATE entities SET primary_role_id=? WHERE id=?", (ov, eid))
        conn.execute("DELETE FROM entity_roles WHERE entity_id=? AND role_id=?", (eid, ah))
        conn.execute(
            "INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) VALUES (?,?,?)",
            (eid, ov, "herrold: holding/overnamevehikel, niet louter aandeelhouder"))
        print(f"  herrold: {name} -> overnamevehikel")


def wire_chain(conn, stak_id):
    vt = entity_id(conn, "Christian Van Thillo")
    epifin = entity_id(conn, "Epifin")
    dpg = entity_id(conn, "DPG Media")
    sdm = entity_id(conn, "Stichting Democratie en Media")

    # Van Thillo -> Epifin (sluiproute) ombuigen naar Van Thillo -> STAK
    row = conn.execute("SELECT id FROM relations WHERE source_id=? AND target_id=?",
                       (vt, epifin)).fetchone()
    if row:
        conn.execute(
            "UPDATE relations SET target_id=?, relation_type='eigendom', mechanism_id=?, description=? WHERE id=?",
            (stak_id, mechanism_id(conn, "familiezeggenschap"),
             "Familie Van Thillo oefent zeggenschap uit via het administratiekantoor.", row[0]))
        print("  keten: Van Thillo -> Epifin omgebogen naar Van Thillo -> STAK")
    else:
        if ensure_relation(conn, vt, stak_id, "eigendom", "familiezeggenschap",
                           "Familie Van Thillo oefent zeggenschap uit via het administratiekantoor.", 0.6):
            print("  keten: Van Thillo -> STAK toegevoegd")

    if ensure_relation(conn, stak_id, epifin, "eigendom", "certificaatconstructie",
                       "STAK certificeert de aandelen van Epifin; zeggenschap los van economisch belang.", 0.7):
        print("  keten: STAK -> Epifin toegevoegd")

    if sdm and dpg and ensure_relation(
            conn, sdm, dpg, "eigendom", "onafhankelijkheidsborging",
            "14,27% + prioriteitsaandeel in DPG; bewaakt onafhankelijkheid van o.a. Trouw en de Volkskrant.", 0.5):
        print("  keten: Stichting Democratie en Media -> DPG (prioriteitsaandeel) toegevoegd")


# --- main -----------------------------------------------------------------

def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None  # expliciete transacties (nodig voor PRAGMA foreign_keys)
    conn.execute("PRAGMA foreign_keys=ON")

    print("\n[1] schema")
    add_stichting_type(conn)

    print("\n[2-4] theorie")
    upsert_role(conn, NEW_ROLE)
    for name, desc in ROLE_UPDATES.items():
        conn.execute("UPDATE roles SET description=? WHERE name=?", (desc, name))
        print(f"Roldefinitie aangescherpt: {name}")
    for m in NEW_MECHANISMS:
        upsert_mechanism(conn, m)
    conn.execute("UPDATE mechanisms SET description=?, effect=? WHERE name='holdingconstructie'",
                 (HOLDING_DESC, HOLDING_EFFECT))
    print("Mechanisme aangescherpt: holdingconstructie (STAK verplaatst naar eigen knoop)")

    print("\n[5] instances: vehikels herrollen")
    reroll_vehikels(conn)

    print("\n[6-7] instances: stichtingen + keten")
    stak_id = get_or_create_entity(conn, STAK_ENTITY)
    get_or_create_entity(conn, SDM_ENTITY)
    wire_chain(conn, stak_id)

    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")

    rollen = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    mech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    ov = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE primary_role_id=(SELECT id FROM roles WHERE name='overnamevehikel')"
    ).fetchone()[0]
    stk = conn.execute("SELECT COUNT(*) FROM entities WHERE type='stichting'").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Rollen: {rollen} | mechanismen: {mech} | overnamevehikel-entiteiten: {ov} | stichting-entiteiten: {stk}")


if __name__ == "__main__":
    main()
