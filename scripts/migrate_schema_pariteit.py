#!/usr/bin/env python3
"""
Migratie: schema-pariteit herstellen (verbeterplan M0.2, juni 2026).

De live `arguments`-tabel is ooit herbouwd zónder CHECKs (stance/status/property
accepteren elke string) en zonder FK op parent_argument_id (Z9). Deze migratie:

1. herbouwt `arguments` met exact de DDL uit schema.sql — dus mét CHECKs
   (incl. property 'indirecte_invloed_op' en status 'verworpen'), mét FK op
   parent_argument_id en met de nieuwe kolom self_merged (ontwerp M0.6);
2. maakt de ontbrekende index idx_entities_type aan;
3. controleert vooraf dat alle bestaande waarden de nieuwe CHECKs overleven
   en achteraf dat geen rij verloren ging en alle FKs kloppen.

De DDL wordt uit schema.sql gelezen (single source of truth): de validator-
schemacheck (scripts/validate_model.py) hoort daarna 0 verschillen te melden.
Conventie: backup-then-migrate.
"""
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
SCHEMA_PATH = ROOT / "schema.sql"

KOPIEER_KOLOMMEN = [
    "id", "relation_id", "entity_id", "role_id", "mechanism_id",
    "parent_argument_id", "property", "property_value", "stance", "claim",
    "title", "reasoning", "weight", "status", "contributed_by", "created_at",
]

ARGUMENT_INDEXEN = [
    "CREATE INDEX idx_arguments_relation ON arguments(relation_id)",
    "CREATE INDEX idx_arguments_entity ON arguments(entity_id)",
    "CREATE INDEX idx_arguments_role ON arguments(role_id)",
    "CREATE INDEX idx_arguments_mechanism ON arguments(mechanism_id)",
    "CREATE INDEX idx_arguments_parent ON arguments(parent_argument_id)",
    "CREATE INDEX idx_arguments_stance ON arguments(stance)",
    "CREATE INDEX idx_arguments_status ON arguments(status)",
]

TOEGESTANE_PROPERTY = {
    "existence", "active_from", "active_until", "certainty", "influence",
    "relation_type", "description", "type", "role", "indirecte_invloed_op",
}
TOEGESTANE_STANCE = {"supporting", "contradicting", "contextual"}
TOEGESTANE_STATUS = {"ongecontroleerd", "bronvermelding_nodig", "betwist",
                     "geverifieerd", "verouderd", "verworpen"}


def arguments_ddl_uit_schema():
    """Pak het CREATE TABLE arguments-statement letterlijk uit schema.sql."""
    tekst = SCHEMA_PATH.read_text()
    match = re.search(r"CREATE TABLE arguments \(.*?\n\);", tekst, re.S)
    if not match:
        sys.exit("CREATE TABLE arguments niet gevonden in schema.sql")
    return match.group(0)


def precheck(conn):
    fouten = []
    for kolom, toegestaan in (("property", TOEGESTANE_PROPERTY),
                              ("stance", TOEGESTANE_STANCE),
                              ("status", TOEGESTANE_STATUS)):
        rijen = conn.execute(
            f"SELECT DISTINCT {kolom} FROM arguments WHERE {kolom} IS NOT NULL").fetchall()
        vreemd = {r[0] for r in rijen} - toegestaan
        if vreemd:
            fouten.append(f"{kolom}: waarden buiten de CHECK: {sorted(vreemd)}")

    n = conn.execute("""
        SELECT COUNT(*) FROM arguments
        WHERE relation_id IS NULL AND entity_id IS NULL
          AND role_id IS NULL AND mechanism_id IS NULL""").fetchone()[0]
    if n:
        fouten.append(f"{n} argumenten zonder enig target")

    n = conn.execute(
        "SELECT COUNT(*) FROM arguments WHERE weight IS NOT NULL AND (weight < 0 OR weight > 1)"
    ).fetchone()[0]
    if n:
        fouten.append(f"{n} argumenten met weight buiten [0,1]")

    if fouten:
        for f in fouten:
            print(f"  PRECHECK FOUT: {f}")
        sys.exit("Migratie afgebroken: bestaande data overleeft de nieuwe CHECKs niet.")


def main():
    if not DB_PATH.exists():
        sys.exit(f"Database niet gevonden: {DB_PATH}")

    backup = DB_PATH.with_name(
        f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = OFF")

    precheck(conn)
    voor = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]

    ddl = arguments_ddl_uit_schema().replace(
        "CREATE TABLE arguments (", "CREATE TABLE arguments_nieuw (", 1)
    kolommen = ", ".join(KOPIEER_KOLOMMEN)

    conn.execute("BEGIN")
    conn.execute(ddl)
    conn.execute(f"INSERT INTO arguments_nieuw ({kolommen}) "
                 f"SELECT {kolommen} FROM arguments")
    conn.execute("DROP TABLE arguments")
    conn.execute("ALTER TABLE arguments_nieuw RENAME TO arguments")
    for index_sql in ARGUMENT_INDEXEN:
        conn.execute(index_sql)

    bestaande_indexen = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index'")}
    if "idx_entities_type" not in bestaande_indexen:
        conn.execute("CREATE INDEX idx_entities_type ON entities(type)")
        print("Index idx_entities_type aangemaakt")

    na = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    if na != voor:
        conn.execute("ROLLBACK")
        sys.exit(f"Rijverlies ({voor} → {na}): teruggedraaid.")

    fk_problemen = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_problemen:
        conn.execute("ROLLBACK")
        sys.exit(f"foreign_key_check faalde: {fk_problemen[:5]} — teruggedraaid.")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"arguments herbouwd met CHECKs + FK ({na} rijen, self_merged toegevoegd).")
    conn.close()


if __name__ == "__main__":
    main()
