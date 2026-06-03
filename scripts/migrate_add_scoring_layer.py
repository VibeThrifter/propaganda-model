"""Migratie: scoringslaag — expliciete instantie-koppeltabel + theorie-doelen voor argumenten.

Twee wijzigingen, conform repo-conventie (eerst backup):

1. Nieuwe tabel `instantiations`: maakt de klasse<->instantie-koppeling expliciet
   (rol<->entiteit of mechanisme<->relatie) met een exemplariteit-gewicht per voorbeeld.
   Geseed uit de bestaande impliciete koppelingen (primary_role_id, entity_roles, mechanism_id).

2. `arguments` krijgt `role_id` en `mechanism_id` (zodat literatuur-argumenten/citaties
   ook direct aan een rol of mechanisme kunnen hangen) en de target-CHECK wordt verruimd
   naar "minstens een van de vier doelen". SQLite kan een CHECK niet in-place wijzigen, dus
   de tabel wordt herbouwd (data behoud, indexen opnieuw aangemaakt).

Idempotent: detecteert of de migratie al (deels) is uitgevoerd en slaat dat deel over.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def _has_table(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def _has_column(conn, table, column):
    return column in [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def _run(conn, statements):
    """Voer losse statements uit (geen executescript: die forceert een eigen commit)."""
    for sql in statements:
        conn.execute(sql)


INSTANTIATIONS_DDL = [
    """CREATE TABLE instantiations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id      INTEGER REFERENCES roles(id),
        mechanism_id INTEGER REFERENCES mechanisms(id),
        entity_id    INTEGER REFERENCES entities(id),
        relation_id  INTEGER REFERENCES relations(id),
        exemplarity  REAL DEFAULT 1.0 CHECK(exemplarity BETWEEN 0.0 AND 1.0),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CHECK ((role_id IS NOT NULL) + (mechanism_id IS NOT NULL) = 1),
        CHECK ((entity_id IS NOT NULL) + (relation_id IS NOT NULL) = 1),
        CHECK ((role_id IS NOT NULL AND entity_id IS NOT NULL)
            OR (mechanism_id IS NOT NULL AND relation_id IS NOT NULL))
    )""",
    # Partiele unieke indexen: NULLs gelden in SQLite als distinct, dus dedupliceer
    # op de daadwerkelijk gevulde paren.
    "CREATE UNIQUE INDEX idx_inst_role_entity ON instantiations(role_id, entity_id) WHERE role_id IS NOT NULL",
    "CREATE UNIQUE INDEX idx_inst_mech_relation ON instantiations(mechanism_id, relation_id) WHERE mechanism_id IS NOT NULL",
    "CREATE INDEX idx_inst_role ON instantiations(role_id)",
    "CREATE INDEX idx_inst_mechanism ON instantiations(mechanism_id)",
    "CREATE INDEX idx_inst_entity ON instantiations(entity_id)",
    "CREATE INDEX idx_inst_relation ON instantiations(relation_id)",
]

ARGUMENTS_REBUILD_DDL = [
    """CREATE TABLE arguments_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        relation_id INTEGER REFERENCES relations(id),
        entity_id INTEGER REFERENCES entities(id),
        role_id INTEGER REFERENCES roles(id),
        mechanism_id INTEGER REFERENCES mechanisms(id),
        parent_argument_id INTEGER,
        property TEXT,
        property_value TEXT,
        stance TEXT NOT NULL,
        claim TEXT NOT NULL,
        reasoning TEXT,
        weight REAL,
        status TEXT NOT NULL DEFAULT 'ongecontroleerd',
        contributed_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CHECK (relation_id IS NOT NULL OR entity_id IS NOT NULL
            OR role_id IS NOT NULL OR mechanism_id IS NOT NULL)
    )""",
    """INSERT INTO arguments_new
        (id, relation_id, entity_id, parent_argument_id, property, property_value,
         stance, claim, reasoning, weight, status, contributed_by, created_at)
     SELECT id, relation_id, entity_id, parent_argument_id, property, property_value,
            stance, claim, reasoning, weight, status, contributed_by, created_at
     FROM arguments""",
    "DROP TABLE arguments",
    "ALTER TABLE arguments_new RENAME TO arguments",
    "CREATE INDEX idx_arguments_relation ON arguments(relation_id)",
    "CREATE INDEX idx_arguments_entity ON arguments(entity_id)",
    "CREATE INDEX idx_arguments_role ON arguments(role_id)",
    "CREATE INDEX idx_arguments_mechanism ON arguments(mechanism_id)",
    "CREATE INDEX idx_arguments_parent ON arguments(parent_argument_id)",
    "CREATE INDEX idx_arguments_stance ON arguments(stance)",
    "CREATE INDEX idx_arguments_status ON arguments(status)",
]


def create_instantiations(conn):
    if _has_table(conn, "instantiations"):
        print("  instantiations bestaat al — overslaan.")
        return
    _run(conn, INSTANTIATIONS_DDL)
    print("  instantiations aangemaakt.")


def rebuild_arguments(conn):
    if _has_column(conn, "arguments", "role_id"):
        print("  arguments heeft role_id al — overslaan.")
        return
    _run(conn, ARGUMENTS_REBUILD_DDL)
    print("  arguments herbouwd met role_id/mechanism_id.")


def migrate():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    # Autocommit-modus zodat we PRAGMA's buiten een transactie kunnen zetten en
    # de tabel-rebuild expliciet kunnen omkaderen.
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    try:
        create_instantiations(conn)
        rebuild_arguments(conn)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        conn.close()
        raise

    # Integriteitscontrole na de rebuild
    problems = conn.execute("PRAGMA foreign_key_check").fetchall()
    if problems:
        conn.close()
        raise RuntimeError(f"foreign_key_check meldt problemen: {problems}")
    conn.execute("PRAGMA foreign_keys = ON")

    # Seed de instantiations uit de impliciete koppelingen
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from seed_instantiations import populate
    conn.execute("BEGIN")
    n1, n2, n3 = populate(conn)
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, reason)
        VALUES ('instantiations', 0, 'created', 'migratie', ?)
    """, (f"Scoringslaag toegevoegd; instantiations geseed "
          f"(hoofdrol={n1}, extra rollen={n2}, mechanisme={n3}).",))
    conn.execute("COMMIT")

    total = conn.execute("SELECT COUNT(*) FROM instantiations").fetchone()[0]
    conn.close()
    print(f"Instantiations geseed: hoofdrol={n1}, extra rollen={n2}, mechanisme={n3} "
          f"(totaal {total}).")
    print("Klaar. foreign_key_check: 0 problemen.")


if __name__ == "__main__":
    migrate()
