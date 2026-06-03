"""
Migratie: de entity-`type`-enum opschonen tot zuiver STRUCTURELE categorieën.

Achtergrond
-----------
`entities.type` (wat is het?) en `roles` (welke functie in het model?) liepen door
elkaar: een dozijn type-waarden was eigenlijk een rolnaam (adverteerder, mediaeigenaar,
politicus, ...). Daardoor zei het Type vaak niets wat de Rol niet al zei.

Principe na deze migratie:
  - Type = structurele vorm. Voor organisaties varieert die echt (bedrijf, partij,
    stichting, omroep, ...); voor mensen bestaat er maar één soort: `persoon`.
  - Functie/positie hoort ALTIJD in de rol (primary_role_id / entity_roles).

Wat dit script doet (in deze volgorde, binnen één transactie):
  1. Backup van de DB (backup-then-migrate-conventie).
  2. ROLLEN BIJVULLEN: personen zonder primaire rol wiens functie alleen in het oude
     type zat (bv. draaideur-politici) krijgen de bijbehorende rol toegewezen, zodat
     er bij het samenvouwen geen functie-informatie verloren gaat.
  3. TYPES HERMAPPEN: rol-achtige types worden herleid tot hun structurele vorm
     (adverteerder->bedrijf, mediaeigenaar/politicus/journalist/...->persoon).
  4. TABEL HERBOUWEN met de nieuwe, strakkere CHECK-enum (SQLite-tabelherbouw).

Idempotent: als de nieuwe enum al actief is, wordt stap 3-4 overgeslagen.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# De nieuwe, zuiver structurele type-enum.
NEW_TYPES = [
    # Personen — één structurele soort; functie zit in de rol
    "persoon",
    # Organisaties — structurele/juridische vormen
    "partij",
    "mediaorganisatie",
    "omroep",
    "persbureau",
    "bedrijf",
    "lobbygroep",
    "denktank",
    "overheidsinstelling",
    "toezichthouder",
    "ngo",
    "vakbond",
    "elite_netwerk",
    "vermogensbeheerder",
    "pr_bureau",
    "platform",
    "rechterlijke_macht",
    "onderwijsinstelling",
    "burgerinitiatief",
    "stichting",
]

# Oud (rol-achtig) type -> nieuwe structurele vorm.
TYPE_REMAP = {
    "adverteerder": "bedrijf",            # 9 bedrijven in de rol van adverteerder
    "mediaeigenaar": "persoon",           # 6 personen/families; eigendom = rol
    "toezichthouder_persoon": "persoon",  # spiegel van de rol `toezichthouder`
    "politicus": "persoon",
    "journalist": "persoon",
    "lobbyist": "persoon",
    "columnist": "persoon",
    "voorlichter": "persoon",
    "academicus": "persoon",
    "advocaat": "persoon",
    "klokkenluider": "persoon",
}

# Oud type -> rolnaam waarmee een ONTBREKENDE primaire rol wordt bijgevuld,
# zodat het samenvouwen tot `persoon` geen functie-info verliest.
ROLE_BACKFILL = {
    "politicus": "politicus",
    "lobbyist": "lobbyist",
    "voorlichter": "voorlichter",
    "journalist": "journalist",
    "columnist": "columnist_opiniemaker",
    "mediaeigenaar": "mediaeigenaar",
    "toezichthouder_persoon": "toezichthouder",
    "adverteerder": "adverteerder",
    "klokkenluider": "klokkenluider",
}

NEW_ENTITIES_DDL = """
CREATE TABLE entities_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ({types})),
    primary_role_id INTEGER REFERENCES roles(id),
    description TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active_from TEXT,
    active_until TEXT,
    active BOOLEAN DEFAULT TRUE
)
""".format(types=", ".join(f"'{t}'" for t in NEW_TYPES))

COPY_COLUMNS = (
    "id, name, type, primary_role_id, description, metadata, "
    "created_at, updated_at, active_from, active_until, active"
)


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, dest)
    print(f"Backup gemaakt: {dest.name}")


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: verwachte rol '{name}' bestaat niet.")
    return row[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='entities'").fetchone()[0]
    if "'adverteerder'" not in ddl and "'politicus'" not in ddl:
        print("Type-enum is al opgeschoond — niets te doen.")
        conn.close()
        return

    backup_db()
    conn.execute("PRAGMA foreign_keys = OFF")

    try:
        conn.execute("BEGIN")

        # 1) Rollen bijvullen waar de functie alleen in het oude type zat.
        backfilled = 0
        for old_type, rname in ROLE_BACKFILL.items():
            rid = role_id(conn, rname)
            cur = conn.execute(
                "UPDATE entities SET primary_role_id=? "
                "WHERE type=? AND primary_role_id IS NULL",
                (rid, old_type),
            )
            if cur.rowcount:
                print(f"  rol bijgevuld: {cur.rowcount}× '{old_type}' -> rol '{rname}'")
                backfilled += cur.rowcount

        # 2) Types hermappen naar structurele vorm.
        remapped = 0
        for old_type, new_type in TYPE_REMAP.items():
            cur = conn.execute(
                "UPDATE entities SET type=? WHERE type=?", (new_type, old_type)
            )
            if cur.rowcount:
                print(f"  type hermapt: {cur.rowcount}× '{old_type}' -> '{new_type}'")
                remapped += cur.rowcount

        # Veiligheidscheck: geen enkel resterend type buiten de nieuwe enum.
        leftover = conn.execute(
            "SELECT DISTINCT type FROM entities WHERE type NOT IN ({})".format(
                ", ".join("?" * len(NEW_TYPES))
            ),
            NEW_TYPES,
        ).fetchall()
        if leftover:
            raise SystemExit(f"FOUT: types buiten nieuwe enum: {[r[0] for r in leftover]}")

        # 3) Tabel herbouwen met strakkere CHECK.
        conn.execute(NEW_ENTITIES_DDL)
        conn.execute(f"INSERT INTO entities_new ({COPY_COLUMNS}) SELECT {COPY_COLUMNS} FROM entities")
        conn.execute("DROP TABLE entities")
        conn.execute("ALTER TABLE entities_new RENAME TO entities")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_role ON entities(primary_role_id)")

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        conn.close()
        raise

    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")

    print(f"\nKlaar. {backfilled} rollen bijgevuld, {remapped} types hermapt.")
    print(f"Entities-tabel herbouwd met {len(NEW_TYPES)} structurele types. Totaal {total} entiteiten, FK's intact.")


if __name__ == "__main__":
    main()
