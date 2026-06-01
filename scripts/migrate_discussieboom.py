"""Migratie: discussieboom + failsafe-mechanismen.

Wijzigingen:
- arguments: + parent_argument_id, entity_id, status, contributed_by; relation_id wordt optioneel
- sources: + reliability
- Nieuwe tabel: edit_log
- Nieuwe indexen
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def migrate():
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")

    # --- 1. Herbouw arguments tabel met nieuwe kolommen ---
    print("Migratie arguments tabel...")
    conn.executescript("""
        CREATE TABLE arguments_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relation_id INTEGER REFERENCES relations(id),
            entity_id INTEGER REFERENCES entities(id),
            parent_argument_id INTEGER REFERENCES arguments_new(id),
            stance TEXT NOT NULL CHECK(stance IN ('supporting','contradicting','contextual')),
            claim TEXT NOT NULL,
            reasoning TEXT,
            weight REAL CHECK(weight BETWEEN 0.0 AND 1.0),
            status TEXT NOT NULL DEFAULT 'ongecontroleerd' CHECK(status IN (
                'ongecontroleerd','bronvermelding_nodig','betwist','geverifieerd','verouderd'
            )),
            contributed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (relation_id IS NOT NULL OR entity_id IS NOT NULL)
        );

        INSERT INTO arguments_new (id, relation_id, stance, claim, reasoning, weight, created_at)
        SELECT id, relation_id, stance, claim, reasoning, weight, created_at
        FROM arguments;

        DROP TABLE arguments;
        ALTER TABLE arguments_new RENAME TO arguments;
    """)

    count = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    print(f"  {count} argumenten gemigreerd")

    # --- 2. Voeg reliability toe aan sources ---
    print("Migratie sources tabel...")
    cols = [row[1] for row in conn.execute("PRAGMA table_info(sources)")]
    if 'reliability' not in cols:
        conn.execute("""
            ALTER TABLE sources ADD COLUMN reliability TEXT NOT NULL DEFAULT 'onbeoordeeld'
            CHECK(reliability IN (
                'primair','academisch','institutioneel',
                'kwaliteitsjournalistiek','regulier','opinie','grijs','onbeoordeeld'
            ))
        """)
        print("  reliability kolom toegevoegd")
    else:
        print("  reliability kolom bestond al")

    # --- 3. Maak edit_log tabel ---
    print("Maak edit_log tabel...")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS edit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            action TEXT NOT NULL CHECK(action IN (
                'created','updated','deleted','verified','disputed'
            )),
            changed_by TEXT,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  edit_log tabel aangemaakt")

    # --- 4. Indexen ---
    print("Indexen aanmaken...")
    indexes = [
        ("idx_arguments_relation", "arguments(relation_id)"),
        ("idx_arguments_entity", "arguments(entity_id)"),
        ("idx_arguments_parent", "arguments(parent_argument_id)"),
        ("idx_arguments_stance", "arguments(stance)"),
        ("idx_arguments_status", "arguments(status)"),
        ("idx_sources_reliability", "sources(reliability)"),
        ("idx_edit_log_table", "edit_log(table_name, record_id)"),
        ("idx_edit_log_changed_by", "edit_log(changed_by)"),
    ]
    for name, cols in indexes:
        conn.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {cols}")
    print(f"  {len(indexes)} indexen aangemaakt")

    # --- 5. Registreer migratie in edit_log ---
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, reason)
        VALUES ('_schema', 0, 'updated', 'migratie', 'Discussieboom + failsafe-mechanismen toegevoegd')
    """)

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()

    # Verificatie
    print("\nVerificatie:")
    for row in conn.execute("PRAGMA table_info(arguments)"):
        print(f"  arguments.{row[1]} ({row[2]})")
    print()
    print(f"  arguments: {conn.execute('SELECT COUNT(*) FROM arguments').fetchone()[0]} rows")
    print(f"  citations: {conn.execute('SELECT COUNT(*) FROM citations').fetchone()[0]} rows")
    print(f"  edit_log:  {conn.execute('SELECT COUNT(*) FROM edit_log').fetchone()[0]} rows")

    conn.close()
    print("\nMigratie voltooid!")


if __name__ == "__main__":
    migrate()
